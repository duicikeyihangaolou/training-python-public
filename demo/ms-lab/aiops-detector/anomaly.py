"""指标 STL 残差异常检测（§12.2.1）与日志窗口 IsolationForest 异常检测（§12.1）。

两者都支持「在线」（从 Prometheus / K8s 取数）和「离线」（POST 传入数据）两种用法：
离线模式输入固定，便于课堂复现与自动化验收。
"""
from __future__ import annotations

import os
import re
import ssl
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL

SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"
NAMESPACE = os.getenv("NAMESPACE", "ms-lab")


# ---------------------------------------------------------------- 指标：STL 残差
def stl_anomalies(values: list[float | None], period: int = 12, z_thr: float = 3.0) -> dict[str, Any]:
    """STL 分解（趋势 + 季节 + 残差），对残差做稳健 z-score（中位数 / MAD），超过阈值判为异常点。"""
    s = pd.Series([np.nan if v is None else v for v in values], dtype="float64")
    n_valid = int(s.notna().sum())
    if n_valid == 0:
        return {"enough_data": False, "points": len(values), "reason": "no valid points"}
    s = s.interpolate(limit_direction="both")
    if len(s) < 2 * period:
        return {"enough_data": False, "points": len(s), "reason": f"need >= {2 * period} points"}
    res = STL(s, period=period, robust=True).fit()
    resid = np.asarray(res.resid)
    med = float(np.median(resid))
    mad = float(np.median(np.abs(resid - med)))
    sigma = max(1.4826 * mad, 1e-6)
    zs = (resid - med) / sigma
    idx = [int(i) for i in np.where(np.abs(zs) > z_thr)[0]]
    return {
        "enough_data": True,
        "points": len(s),
        "period": period,
        "z_threshold": z_thr,
        "resid_sigma": round(sigma, 6),
        "anomaly_indices": idx,
        "anomalies": [{"index": i, "value": round(float(s.iloc[i]), 6), "z": round(float(zs[i]), 2)} for i in idx],
    }


# ---------------------------------------------------------------- 日志：IsolationForest
ERR_RE = re.compile(r"\b(ERROR|WARN|Exception|degraded|timed out|Timeout|FAIL)", re.I)
MASK_RE = re.compile(r"[0-9a-f]{8,}|\d+")


def template_of(line: str) -> str:
    return MASK_RE.sub("<N>", line)[:160]


def window_features(lines: list[tuple[float, str]], window_s: int) -> list[dict[str, Any]]:
    buckets: dict[int, list[str]] = defaultdict(list)
    for ts, text in lines:
        buckets[int(ts // window_s)].append(text)
    rows = []
    for b in sorted(buckets):
        texts = buckets[b]
        errs = sum(1 for t in texts if ERR_RE.search(t))
        rows.append({
            "window_start": b * window_s,
            "n": len(texts),
            "errors": errs,
            "error_ratio": errs / len(texts),
            "templates": len({template_of(t) for t in texts}),
            "mean_len": float(np.mean([len(t) for t in texts])),
        })
    return rows


def log_anomalies(lines: list[tuple[float, str]], window_s: int = 30, min_windows: int = 6) -> dict[str, Any]:
    rows = window_features(lines, window_s)
    if len(rows) < min_windows:
        return {"enough_data": False, "windows": len(rows), "reason": f"need >= {min_windows} windows"}
    x = np.array([[r["n"], r["errors"], r["error_ratio"], r["templates"], r["mean_len"]] for r in rows], dtype=float)
    forest = IsolationForest(n_estimators=100, contamination="auto", random_state=0).fit(x)
    pred = forest.predict(x)
    score = forest.score_samples(x)
    med_err = float(np.median([r["error_ratio"] for r in rows]))
    anomalous = []
    for r, p, sc in zip(rows, pred, score):
        r["score"] = round(float(sc), 4)
        # 孤立点 且 错误比例高于常态，避免把「安静窗口」当成告警（讲义 §12.1.2：控制误报）
        if p == -1 and r["error_ratio"] > med_err:
            anomalous.append({
                "window_start": datetime.fromtimestamp(r["window_start"], tz=timezone.utc).isoformat(),
                "n": r["n"], "errors": r["errors"], "error_ratio": round(r["error_ratio"], 3), "score": r["score"],
            })
    return {
        "enough_data": True,
        "windows": len(rows),
        "window_s": window_s,
        "max_error_ratio": round(max(r["error_ratio"] for r in rows), 3),
        "anomalous": anomalous,
    }


# ---------------------------------------------------------------- 取数
def k8s_get(path: str, params: dict[str, Any] | None = None) -> httpx.Response:
    token = open(f"{SA_DIR}/token", encoding="utf-8").read().strip()
    ctx = ssl.create_default_context(cafile=f"{SA_DIR}/ca.crt")
    return httpx.get(
        f"https://kubernetes.default.svc{path}", params=params,
        headers={"Authorization": f"Bearer {token}"}, verify=ctx, timeout=10.0,
    )


def fetch_pod_logs(app_label: str, minutes: int) -> list[tuple[float, str]]:
    pods = k8s_get(f"/api/v1/namespaces/{NAMESPACE}/pods", {"labelSelector": f"app={app_label}"}).json().get("items", [])
    out: list[tuple[float, str]] = []
    for pod in pods:
        name = pod["metadata"]["name"]
        resp = k8s_get(
            f"/api/v1/namespaces/{NAMESPACE}/pods/{name}/log",
            {"sinceSeconds": minutes * 60, "timestamps": "true"},
        )
        if resp.status_code != 200:
            continue
        for line in resp.text.splitlines():
            head, _, text = line.partition(" ")
            try:  # K8s 时间戳形如 2026-11-18T08:00:00.123456789Z，窗口统计只需秒级精度
                ts = datetime.strptime(head[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                continue
            out.append((ts, text))
    return out


def prom_series(query: str, minutes: int, step_s: int, prom_url: str) -> list[float | None]:
    import time

    end = time.time()
    resp = httpx.get(
        f"{prom_url}/api/v1/query_range",
        params={"query": query, "start": end - minutes * 60, "end": end, "step": step_s},
        timeout=5.0,
    )
    result = resp.json().get("data", {}).get("result", [])
    if not result:
        return []
    vals: list[float | None] = []
    for _, v in result[0]["values"]:
        f = float(v)
        vals.append(f if np.isfinite(f) else None)
    return vals
