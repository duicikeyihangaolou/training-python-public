"""基于调用链（Jaeger）的根因分析（§12.3）。

思路（可解释、不依赖训练）：
1. 对每条 Trace，把每个 span 的「自身耗时」= span 耗时 - 直接子 span 耗时之和（不小于 0），按服务汇总；
2. 以各服务自身耗时的中位数作基线，超出部分记为「超额耗时」；
3. 只统计「错误源头」span：自身带错误标记、且没有带错误的子 span（避免把被连带报错的上游服务当成根因）；
4. 综合评分 = 0.7 * 超额耗时占比 + 0.3 * 错误源头占比，排序给出嫌疑服务。
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

import httpx
import numpy as np

EXCESS_MIN_MS = 20.0  # 总超额耗时低于该值视为噪声，不参与延迟维度评分
W_LATENCY = 0.7
W_ERROR = 0.3


def _tags(span: dict[str, Any]) -> dict[str, Any]:
    return {t["key"]: t.get("value") for t in span.get("tags", [])}


def _is_error(span: dict[str, Any]) -> bool:
    tags = _tags(span)
    if tags.get("error") in (True, "true", "True"):
        return True
    if str(tags.get("otel.status_code", "")).upper() == "ERROR":
        return True
    for key in ("http.status_code", "http.response.status_code"):
        try:
            if int(tags.get(key, 0)) >= 500:
                return True
        except (TypeError, ValueError):
            pass
    return False


def analyze_trace(trace: dict[str, Any]) -> tuple[dict[str, float], dict[str, int]]:
    """返回 (服务 -> 自身耗时 ms, 服务 -> 错误源头 span 数)。"""
    spans = trace.get("spans", [])
    procs = trace.get("processes", {})
    svc_of = {s["spanID"]: procs.get(s.get("processID"), {}).get("serviceName", "unknown") for s in spans}
    children: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in spans:
        for ref in s.get("references", []):
            if ref.get("refType") == "CHILD_OF":
                children[ref["spanID"]].append(s)
    err = {s["spanID"]: _is_error(s) for s in spans}
    self_ms: dict[str, float] = defaultdict(float)
    origin: dict[str, int] = defaultdict(int)
    for s in spans:
        kids = children.get(s["spanID"], [])
        own = max(0.0, s["duration"] - sum(k["duration"] for k in kids)) / 1000.0
        self_ms[svc_of[s["spanID"]]] += own
        if err[s["spanID"]] and not any(err[k["spanID"]] for k in kids):
            origin[svc_of[s["spanID"]]] += 1
    return dict(self_ms), dict(origin)


def rank_suspects(traces: list[dict[str, Any]]) -> dict[str, Any]:
    per_trace = [analyze_trace(t) for t in traces if t.get("spans")]
    if not per_trace:
        return {"ok": True, "traces": 0, "top1": None, "suspects": []}
    services = sorted({s for st, _ in per_trace for s in st} | {s for _, eo in per_trace for s in eo})
    baseline = {s: float(np.median([st.get(s, 0.0) for st, _ in per_trace])) for s in services}
    excess = {s: 0.0 for s in services}
    errors = {s: 0 for s in services}
    for st, eo in per_trace:
        for s in services:
            excess[s] += max(0.0, st.get(s, 0.0) - baseline[s])
            errors[s] += eo.get(s, 0)
    total_excess = sum(excess.values())
    total_err = sum(errors.values())
    suspects = []
    for s in services:
        lat_share = excess[s] / total_excess if total_excess >= EXCESS_MIN_MS else 0.0
        err_share = errors[s] / total_err if total_err else 0.0
        suspects.append({
            "service": s,
            "score": round(W_LATENCY * lat_share + W_ERROR * err_share, 4),
            "excess_self_ms": round(excess[s], 1),
            "baseline_self_ms": round(baseline[s], 2),
            "error_origin_spans": errors[s],
        })
    suspects.sort(key=lambda x: -x["score"])
    top1 = suspects[0]["service"] if suspects and suspects[0]["score"] > 0 else None
    return {"ok": True, "traces": len(per_trace), "top1": top1, "suspects": suspects}


def fetch_traces(jaeger_url: str, service: str, minutes: int, limit: int = 200) -> list[dict[str, Any]]:
    end_us = int(time.time() * 1_000_000)
    start_us = end_us - minutes * 60 * 1_000_000
    resp = httpx.get(
        f"{jaeger_url}/api/traces",
        params={"service": service, "start": start_us, "end": end_us, "limit": limit},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])
