"""AIOps（课堂 §12）：
  /health            订单成功率「夜间阈值 + 自适应」告警（§12.2.2）
  /anomaly/stl       指标 STL 残差异常检测（§12.2.1），GET 读 Prometheus，POST 离线序列
  /anomaly/logs      日志窗口 IsolationForest 异常检测（§12.1），GET 读 K8s Pod 日志，POST 离线日志行
  /rca               基于 Jaeger 调用链的根因分析（§12.3），GET 读 Jaeger，POST 离线 Trace
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

import anomaly
import rca

SERVICE = "aiops-detector"
app = FastAPI(title=SERVICE)

PROM_URL = os.getenv("PROM_URL", "http://prometheus:9090")
JAEGER_URL = os.getenv("JAEGER_URL", "http://jaeger:16686")
WINDOW = int(os.getenv("WINDOW", "30"))
# 课堂按本地时区判定「夜间」（默认北京时间 00:00–06:59）；不要用 UTC
TZ = ZoneInfo(os.getenv("TZ_NAME", "Asia/Shanghai"))
NIGHT_START = int(os.getenv("NIGHT_START", "0"))
NIGHT_END = int(os.getenv("NIGHT_END", "7"))
_history: deque[float] = deque(maxlen=WINDOW)
_last_alert: str | None = None
_stop = False


def query_success_rate() -> float | None:
    # Spring Boot 3 Micrometer 课堂导出为 orders_total{status=...}（偶见 orders_total_total）
    # 无流量时分母为 0：(sum(...) > 0) 过滤后结果为空 -> 不产生样本（不能当作成功率 0 误报）
    queries = (
        'sum(rate(orders_total{status="ok"}[1m])) / (sum(rate(orders_total[1m])) > 0)',
        'sum(rate(orders_total_total{status="ok"}[1m])) / (sum(rate(orders_total_total[1m])) > 0)',
    )
    try:
        for q in queries:
            resp = httpx.get(f"{PROM_URL}/api/v1/query", params={"query": q}, timeout=3.0)
            result = resp.json().get("data", {}).get("result", [])
            if result:
                return float(result[0]["value"][1])
        return None
    except Exception as exc:
        print(f"prom query failed: {exc}", flush=True)
        return None


def threshold(now: datetime) -> float:
    # night window (local TZ): looser absolute floor to cut false alarms on quiet traffic
    if NIGHT_START <= now.hour < NIGHT_END:
        return float(os.getenv("NIGHT_THR", "0.85"))
    return float(os.getenv("DAY_THR", "0.95"))


def loop():
    global _last_alert
    while not _stop:
        rate = query_success_rate()
        now = datetime.now(TZ)
        if rate is not None:
            _history.append(rate)
            thr = threshold(now)
            if len(_history) >= 5:
                mu = sum(_history) / len(_history)
                var = sum((x - mu) ** 2 for x in _history) / len(_history)
                sigma = var ** 0.5
                drop = rate < (mu - max(sigma, 0.02))
                if rate < thr or drop:
                    msg = f"ALERT order_success_rate={rate:.3f} thr={thr:.2f} mu={mu:.3f} hour={now.hour}"
                    print(msg, flush=True)
                    _last_alert = msg
                else:
                    print(f"ok rate={rate:.3f} thr={thr:.2f} mu={mu:.3f}", flush=True)
        time.sleep(10)


@app.on_event("startup")
def startup():
    threading.Thread(target=loop, daemon=True).start()


@app.get("/health")
def health():
    return {"ok": True, "service": SERVICE, "last_alert": _last_alert, "samples": list(_history)[-5:]}


# ---------------------------------------------------------------- §12.2.1 指标异常（STL）
SUCCESS_QUERIES = (
    'sum(rate(orders_total{status="ok"}[1m])) / (sum(rate(orders_total[1m])) > 0)',
    'sum(rate(orders_total_total{status="ok"}[1m])) / (sum(rate(orders_total_total[1m])) > 0)',
)
QPS_QUERY = 'sum(rate(http_server_requests_seconds_count{job="gateway"}[1m]))'


class StlBody(BaseModel):
    series: list[float | None]
    period: int = 12
    z: float = 3.0


@app.post("/anomaly/stl")
def anomaly_stl_offline(body: StlBody):
    """离线：直接传入时间序列，便于复现与验收。"""
    return {"ok": True, "mode": "offline", **anomaly.stl_anomalies(body.series, body.period, body.z)}


@app.get("/anomaly/stl")
def anomaly_stl(metric: str = Query("success"), minutes: int = Query(60, ge=10, le=720),
                step_s: int = Query(30, ge=10, le=300), period: int = Query(12, ge=4, le=288)):
    """在线：对订单成功率（success）或网关 QPS（qps）做 STL 残差检测。"""
    queries = SUCCESS_QUERIES if metric == "success" else (QPS_QUERY,)
    values: list[float | None] = []
    for q in queries:
        try:
            values = anomaly.prom_series(q, minutes, step_s, PROM_URL)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"prometheus: {exc}") from exc
        if values:
            break
    return {"ok": True, "mode": "online", "metric": metric, **anomaly.stl_anomalies(values, period)}


# ---------------------------------------------------------------- §12.1 日志异常（IsolationForest）
class LogLine(BaseModel):
    ts: float
    text: str


class LogsBody(BaseModel):
    lines: list[LogLine]
    window_s: int = 30


@app.post("/anomaly/logs")
def anomaly_logs_offline(body: LogsBody):
    """离线：传入带时间戳的日志行（秒级 epoch）。"""
    lines = [(l.ts, l.text) for l in body.lines]
    return {"ok": True, "mode": "offline", **anomaly.log_anomalies(lines, body.window_s)}


@app.get("/anomaly/logs")
def anomaly_logs(service: str = Query("order-service"), minutes: int = Query(30, ge=2, le=240),
                 window_s: int = Query(30, ge=5, le=300)):
    """在线：通过 K8s API 拉取 app=<service> 的 Pod 日志，按窗口提特征并检测。"""
    try:
        lines = anomaly.fetch_pod_logs(service, minutes)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"k8s logs: {exc}") from exc
    return {"ok": True, "mode": "online", "service": service, "lines": len(lines), **anomaly.log_anomalies(lines, window_s)}


# ---------------------------------------------------------------- §12.3 根因分析
class RcaBody(BaseModel):
    traces: list[dict]


@app.post("/rca")
def rca_offline(body: RcaBody):
    """离线：传入 Jaeger 格式的 Trace 列表。"""
    return {"mode": "offline", **rca.rank_suspects(body.traces)}


@app.get("/rca")
def rca_online(entry: str = Query("gateway"), minutes: int = Query(10, ge=1, le=120), limit: int = Query(200, ge=10, le=1000)):
    """在线：从 Jaeger 拉取入口服务最近的 Trace，定位最可疑的服务。"""
    try:
        traces = rca.fetch_traces(JAEGER_URL, entry, minutes, limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"jaeger: {exc}") from exc
    return {"mode": "online", "entry": entry, "minutes": minutes, **rca.rank_suspects(traces)}
