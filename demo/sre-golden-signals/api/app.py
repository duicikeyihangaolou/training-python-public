"""SRE 黄金指标演示 API：暴露 Latency / Traffic / Errors，并支持人为注入故障。"""

from __future__ import annotations

import os
import random
import time

from fastapi import FastAPI, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = FastAPI(title="SRE Golden Signals Demo API")

REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
INFLIGHT = Gauge("http_inflight_requests", "In-flight HTTP requests")
ERROR_RATE = Gauge("demo_forced_error_rate", "Forced error rate for demo")

# 0.0 ~ 1.0；可通过 /chaos/error-rate 动态调整
_forced_error_rate = float(os.getenv("ERROR_RATE", "0.02"))
_extra_latency_ms = 0.0
ERROR_RATE.set(_forced_error_rate)


@app.middleware("http")
async def observe(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    INFLIGHT.inc()
    start = time.perf_counter()
    status = "500"
    try:
        if _extra_latency_ms > 0:
            time.sleep(_extra_latency_ms / 1000.0)
        if random.random() < _forced_error_rate and request.url.path.startswith("/api"):
            status = "500"
            return Response(content='{"error":"injected failure"}', status_code=500)
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        elapsed = time.perf_counter() - start
        LATENCY.labels(request.method, request.url.path).observe(elapsed)
        REQUESTS.labels(request.method, request.url.path, status).inc()
        INFLIGHT.dec()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/orders")
def list_orders():
    # 模拟业务接口：偶尔稍慢
    time.sleep(random.uniform(0.01, 0.08))
    return {"orders": [{"id": 1, "amount": 99.0}, {"id": 2, "amount": 42.5}]}


@app.post("/api/pay")
def pay():
    time.sleep(random.uniform(0.02, 0.12))
    return {"paid": True, "tx": f"tx-{random.randint(1000, 9999)}"}


@app.post("/chaos/error-rate")
def set_error_rate(rate: float):
    """课堂注入故障：rate=0.2 表示约 20% 请求返回 500。"""
    global _forced_error_rate
    _forced_error_rate = max(0.0, min(1.0, rate))
    ERROR_RATE.set(_forced_error_rate)
    return {"error_rate": _forced_error_rate}


@app.post("/chaos/latency-ms")
def set_latency(ms: float):
    """课堂注入延迟：额外增加固定毫秒延迟。"""
    global _extra_latency_ms
    _extra_latency_ms = max(0.0, ms)
    return {"extra_latency_ms": _extra_latency_ms}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
