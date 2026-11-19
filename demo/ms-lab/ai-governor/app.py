"""AI 辅助微服务治理（讲义 §10）：智能路由建议 + 预测扩缩容建议。

  GET /route   线性回归预测各推荐实例的下一窗口延迟，返回最优实例（§10.1）
  GET /scale   Prophet 预测 gateway QPS，给出建议副本数（§10.2）；APPLY=true 才会真正 patch Deployment
  GET /health

数据全部来自 Prometheus；模型是轻量的，重点是「指标 -> 预测 -> 治理动作」这条链路。
"""
from __future__ import annotations

import logging
import math
import os
import ssl
import time
from typing import Any

import httpx
import numpy as np
from fastapi import FastAPI, Query

SERVICE = "ai-governor"
app = FastAPI(title=SERVICE)
log = logging.getLogger(SERVICE)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

PROM_URL = os.getenv("PROM_URL", "http://prometheus:9090")
NAMESPACE = os.getenv("NAMESPACE", "ms-lab")

# §10.1 智能路由
ROUTE_CANDIDATES = [c.strip() for c in os.getenv("ROUTE_CANDIDATES", "recommend:8080,recommend-canary:8080").split(",") if c.strip()]
ROUTE_HORIZON_S = int(os.getenv("ROUTE_HORIZON_S", "30"))
ROUTE_LOOKBACK_MIN = int(os.getenv("ROUTE_LOOKBACK_MIN", "10"))

# §10.2 预测扩缩容
SCALE_TARGET = os.getenv("SCALE_TARGET", "recommend")
QPS_QUERIES = (
    'sum(rate(http_server_requests_seconds_count{job="gateway"}[1m]))',
    'sum(rate(spring_cloud_gateway_requests_seconds_count{job="gateway"}[1m]))',
)
QPS_PER_REPLICA = float(os.getenv("QPS_PER_REPLICA", "5"))
MIN_REPLICAS = int(os.getenv("MIN_REPLICAS", "1"))
MAX_REPLICAS = int(os.getenv("MAX_REPLICAS", "4"))
HEADROOM = float(os.getenv("HEADROOM", "1.2"))
APPLY = os.getenv("APPLY", "false").lower() == "true"

SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"


def prom_range(query: str, minutes: int, step_s: int) -> list[tuple[float, float]]:
    end = time.time()
    start = end - minutes * 60
    resp = httpx.get(
        f"{PROM_URL}/api/v1/query_range",
        params={"query": query, "start": start, "end": end, "step": step_s},
        timeout=5.0,
    )
    result = resp.json().get("data", {}).get("result", [])
    if not result:
        return []
    out = []
    for ts, val in result[0]["values"]:
        v = float(val)
        if math.isfinite(v):  # Prometheus 在 0/0 时返回 "NaN"
            out.append((float(ts), v))
    return out


def linear_predict(points: list[tuple[float, float]], horizon_s: float) -> tuple[float | None, float]:
    """最小二乘直线外推；样本不足 3 个时退化为最近值。返回 (预测值, 斜率/秒)。"""
    if not points:
        return None, 0.0
    ys = np.array([p[1] for p in points][-30:])
    ts = np.array([p[0] for p in points][-30:])
    if len(ys) < 3:
        return float(ys[-1]), 0.0
    slope, intercept = np.polyfit(ts - ts[0], ys, 1)
    pred = slope * (ts[-1] + horizon_s - ts[0]) + intercept
    return float(max(pred, 0.0)), float(slope)


@app.get("/health")
def health():
    return {"ok": True, "service": SERVICE, "apply": APPLY, "candidates": ROUTE_CANDIDATES}


@app.get("/route")
def route(service: str = Query("recommend")):
    """预测每个候选实例下一窗口的平均延迟（ms），选最小者。无数据的实例不参与选择。"""
    cands: list[dict[str, Any]] = []
    for inst in ROUTE_CANDIDATES:
        q = (
            f'sum(rate(recommend_latency_seconds_sum{{instance="{inst}"}}[30s]))'
            f' / sum(rate(recommend_latency_seconds_count{{instance="{inst}"}}[30s]))'
        )
        try:
            pts = prom_range(q, ROUTE_LOOKBACK_MIN, 10)
        except Exception as exc:  # noqa: BLE001
            cands.append({"instance": inst, "predicted_ms": None, "samples": 0, "error": str(exc)})
            continue
        pred, slope = linear_predict(pts, ROUTE_HORIZON_S)
        cands.append({
            "instance": inst,
            "name": inst.split(":")[0],
            "samples": len(pts),
            "last_ms": round(pts[-1][1] * 1000, 2) if pts else None,
            "slope_ms_per_min": round(slope * 60 * 1000, 3),
            "predicted_ms": round(pred * 1000, 2) if pred is not None else None,
        })
    scored = [c for c in cands if c.get("predicted_ms") is not None]
    if scored:
        best = min(scored, key=lambda c: c["predicted_ms"])["name"]
        reason = "min predicted latency"
    else:
        best = ROUTE_CANDIDATES[0].split(":")[0] if ROUTE_CANDIDATES else ""
        reason = "no data, default to first candidate"
    log.info('{"type":"route","best":"%s","reason":"%s"}', best, reason)
    return {"service": service, "best": best, "reason": reason, "candidates": cands, "horizon_s": ROUTE_HORIZON_S}


def prophet_forecast(points: list[tuple[float, float]], step_s: int, horizon_points: int) -> tuple[float, str, str | None]:
    """返回 (预测窗口内的峰值 QPS, 引擎, 错误信息)。Prophet 失败时退化为线性外推并如实标注。"""
    try:
        import pandas as pd
        from prophet import Prophet

        df = pd.DataFrame({"ds": pd.to_datetime([p[0] for p in points], unit="s"), "y": [p[1] for p in points]})
        m = Prophet(
            daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False,
            changepoint_prior_scale=0.1, uncertainty_samples=0,
        )
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon_points, freq=f"{step_s}s", include_history=False)
        fc = m.predict(future)
        return float(max(fc["yhat"].max(), 0.0)), "prophet", None
    except Exception as exc:  # noqa: BLE001
        peak = 0.0
        pred, _ = linear_predict(points, step_s * horizon_points)
        if pred is not None:
            peak = max(pred, max(p[1] for p in points))
        return peak, "linear-fallback", f"{type(exc).__name__}: {exc}"


def k8s(method: str, path: str, json_body: Any = None, content_type: str | None = None) -> httpx.Response | None:
    token_path = f"{SA_DIR}/token"
    if not os.path.exists(token_path):
        return None
    token = open(token_path, encoding="utf-8").read().strip()
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type
    ctx = ssl.create_default_context(cafile=f"{SA_DIR}/ca.crt")
    return httpx.request(method, f"https://kubernetes.default.svc{path}", headers=headers, json=json_body, verify=ctx, timeout=5.0)


def current_replicas() -> int | None:
    resp = k8s("GET", f"/apis/apps/v1/namespaces/{NAMESPACE}/deployments/{SCALE_TARGET}")
    if resp is None or resp.status_code != 200:
        return None
    return int(resp.json()["spec"].get("replicas", 1))


def apply_replicas(n: int) -> bool:
    resp = k8s(
        "PATCH", f"/apis/apps/v1/namespaces/{NAMESPACE}/deployments/{SCALE_TARGET}/scale",
        json_body={"spec": {"replicas": n}}, content_type="application/merge-patch+json",
    )
    return resp is not None and resp.status_code == 200


@app.get("/scale")
def scale(minutes: int = Query(30, ge=5, le=240), horizon_min: int = Query(10, ge=1, le=60), step_s: int = Query(30, ge=10, le=300)):
    """用 Prophet 预测未来 horizon_min 分钟的 gateway QPS 峰值，换算建议副本数。"""
    points: list[tuple[float, float]] = []
    used_query = None
    for q in QPS_QUERIES:
        try:
            points = prom_range(q, minutes, step_s)
        except Exception as exc:  # noqa: BLE001
            log.info('{"type":"scale_query_failed","error":"%s"}', exc)
            continue
        if points:
            used_query = q
            break
    cur = current_replicas()
    if len(points) < 3:
        return {
            "target": SCALE_TARGET, "engine": "no-data", "history_points": len(points),
            "forecast_peak_qps": 0.0, "recommended_replicas": MIN_REPLICAS, "current_replicas": cur, "applied": False,
        }
    horizon_points = max(1, horizon_min * 60 // step_s)
    peak, engine, err = prophet_forecast(points, step_s, horizon_points)
    need = math.ceil(peak * HEADROOM / QPS_PER_REPLICA) if peak > 0 else MIN_REPLICAS
    rec = int(min(max(need, MIN_REPLICAS), MAX_REPLICAS))
    applied = False
    if APPLY and cur is not None and rec != cur:
        applied = apply_replicas(rec)
    out = {
        "target": SCALE_TARGET, "engine": engine, "history_points": len(points), "query": used_query,
        "last_qps": round(points[-1][1], 3), "forecast_peak_qps": round(peak, 3),
        "qps_per_replica": QPS_PER_REPLICA, "headroom": HEADROOM,
        "recommended_replicas": rec, "current_replicas": cur, "applied": applied,
    }
    if err:
        out["engine_error"] = err
    log.info('{"type":"scale","engine":"%s","peak_qps":%.3f,"recommended":%d,"current":%s}', engine, peak, rec, cur)
    return out
