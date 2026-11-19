"""推荐模型服务（BentoML + PyTorch CPU）。

对外契约与原 Java recommend-service 保持一致，recommend-bff 无需改动协议：
  GET  /api/recommend   头：X-User-Id / X-Canary / X-Experiment
  GET  /health
  GET  /metrics         （BentoML 内置，含下方自定义指标）
  POST /admin/reload-model   热加载：从 MODEL_DIR 重新读取 ranker_*.pt 并原子替换（不重启、不丢请求）
  POST /chaos/latency        故障注入：{"ms": 2000}

金丝雀（X-Canary / MODEL_VERSION）决定请求进入哪套 Deployment；
实验（X-Experiment）决定使用哪个排序模型，两者正交（讲义 §11.3）。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
import uuid
import zlib
from pathlib import Path
from typing import Any

import bentoml
import torch
from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel

from ranker import load_ranker

log = logging.getLogger("recommend")
logging.basicConfig(level=logging.INFO, format="%(message)s")

SERVICE = "recommend"
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
MODEL_NAMES = ("ranker_v1", "ranker_v2")

ITEMS = [f"sku-{i}" for i in range(1, 21)]
POP = {sku: (21 - i) / 20.0 for i, sku in enumerate(ITEMS)}

REQUESTS = bentoml.metrics.Counter(
    name="recommend_requests_total",
    documentation="recommend requests",
    labelnames=["experiment", "status"],
)
LATENCY = bentoml.metrics.Histogram(
    name="recommend_latency_seconds",
    documentation="recommend end-to-end latency",
    labelnames=["experiment"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


def _tracer():
    """可选 OTel：导出到 Jaeger，服务名 recommend，便于 §7 链路与 §12.3 根因分析。"""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318/v1/traces")
        provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        return trace.get_tracer(SERVICE)
    except Exception as exc:  # noqa: BLE001
        log.info(json.dumps({"type": "otel_skipped", "reason": str(exc)}))
        return None


class ModelRegistry:
    """线程安全的模型注册表：加载新权重后原子替换引用，在途请求仍使用旧对象。"""

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        self._lock = threading.Lock()
        self._models: dict[str, dict[str, Any]] = {}

    def load(self, name: str) -> dict[str, Any]:
        path = self.model_dir / f"{name}.pt"
        if not path.is_file():
            raise FileNotFoundError(str(path))
        sha = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        model = load_ranker(str(path))
        with self._lock:
            prev = self._models.get(name)
            entry = {
                "model": model,
                "sha": sha,
                "generation": (prev["generation"] + 1) if prev else 1,
                "loaded_at": time.time(),
            }
            self._models[name] = entry
        return entry

    def get(self, name: str) -> dict[str, Any] | None:
        with self._lock:
            return self._models.get(name)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                n: {"sha": e["sha"], "generation": e["generation"], "loaded_at": int(e["loaded_at"])}
                for n, e in self._models.items()
            }


REGISTRY = ModelRegistry(MODEL_DIR)
TRACER = None
CHAOS = {"latency_ms": 0}


class ChaosBody(BaseModel):
    ms: int = 0


class ReloadBody(BaseModel):
    name: str = "ranker_v2"


def default_experiment() -> str:
    return "ranker_v2" if MODEL_VERSION.endswith("2") else "ranker_v1"


def stage_log(stage: str, request_id: str, **fields: Any) -> None:
    # 三阶段结构化日志：type 取值 recall / rank / rearrange，同一 request_id 串联（讲义 §11.1）
    log.info(json.dumps({"type": stage, "request_id": request_id, **fields}, ensure_ascii=False))


def recall(request_id: str, uid: str) -> list[str]:
    candidates = sorted(ITEMS, key=lambda s: POP[s], reverse=True)[:12]
    stage_log("recall", request_id, user_id=uid, count=len(candidates), candidates=candidates)
    return candidates


def features_for(uid: str, candidates: list[str]) -> torch.Tensor:
    rows = []
    for i, sku in enumerate(candidates):
        # crc32 保证同一用户跨重启特征一致（内置 hash() 每个进程随机）
        rows.append([POP[sku], (zlib.crc32((uid + sku).encode("utf-8")) % 1000) / 1000.0, i / max(len(candidates), 1)])
    return torch.tensor(rows, dtype=torch.float32)


def rearrange(request_id: str, ranked: list[tuple[str, float]]) -> list[dict[str, Any]]:
    out = [{"sku": sku, "score": round(float(score), 4)} for sku, score in ranked[:8]]
    stage_log("rearrange", request_id, count=len(out), skus=[it["sku"] for it in out])
    return out


api = FastAPI(title="model-service")


@api.get("/health")
def health():
    return {
        "ok": True,
        "service": SERVICE,
        "model_version": MODEL_VERSION,
        "default_experiment": default_experiment(),
        "models": REGISTRY.snapshot(),
        "chaos_latency_ms": CHAOS["latency_ms"],
    }


@api.post("/admin/reload-model")
def reload_model(body: ReloadBody):
    if body.name not in MODEL_NAMES:
        raise HTTPException(status_code=400, detail=f"name must be one of {MODEL_NAMES}")
    try:
        entry = REGISTRY.load(body.name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"model file missing: {exc}") from exc
    log.info(json.dumps({"type": "model_reload", "name": body.name, "sha": entry["sha"], "generation": entry["generation"]}))
    return {"ok": True, "name": body.name, "sha": entry["sha"], "generation": entry["generation"]}


@api.post("/chaos/latency")
def chaos_latency(body: ChaosBody):
    CHAOS["latency_ms"] = max(0, body.ms)
    return {"ok": True, "chaos_latency_ms": CHAOS["latency_ms"]}


@api.get("/api/recommend")
async def recommend(
    request: Request,
    user_id: str | None = None,
    x_user_id: str | None = Header(default=None),
    x_experiment: str | None = Header(default=None),
    x_canary: str | None = Header(default=None),
):
    start = time.time()
    uid = user_id or x_user_id or "anonymous"
    exp = x_experiment if x_experiment in MODEL_NAMES else default_experiment()
    request_id = uuid.uuid4().hex[:12]
    if CHAOS["latency_ms"] > 0:
        await asyncio.sleep(CHAOS["latency_ms"] / 1000.0)

    entry = REGISTRY.get(exp)
    if entry is None:
        REQUESTS.labels(experiment=exp, status="500").inc()
        raise HTTPException(status_code=503, detail=f"model {exp} not loaded")

    span_cm = None
    if TRACER is not None:
        from opentelemetry import propagate

        ctx = propagate.extract(dict(request.headers))
        span_cm = TRACER.start_as_current_span("recommend.pipeline", context=ctx)
        span = span_cm.__enter__()
        span.set_attribute("user.id", uid)
        span.set_attribute("experiment", exp)
        span.set_attribute("model.version", MODEL_VERSION)
        span.set_attribute("model.sha", entry["sha"])
        span.set_attribute("request.id", request_id)
    try:
        candidates = recall(request_id, uid)
        feats = features_for(uid, candidates)
        with torch.no_grad():
            scores = entry["model"](feats).tolist()
        ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
        stage_log(
            "rank", request_id, experiment=exp, model_version=MODEL_VERSION, model_sha=entry["sha"],
            top=[{"sku": s, "score": round(float(sc), 4)} for s, sc in ranked[:3]],
        )
        items = rearrange(request_id, ranked)
    finally:
        if span_cm is not None:
            span_cm.__exit__(None, None, None)

    payload = {
        "user_id": uid,
        "experiment": exp,
        "model_version": MODEL_VERSION,
        "model_sha": entry["sha"],
        "canary": x_canary == "true",
        "items": items,
    }
    log.info(json.dumps({"type": "ab_split", "request_id": request_id, **payload}, ensure_ascii=False))
    REQUESTS.labels(experiment=exp, status="200").inc()
    LATENCY.labels(experiment=exp).observe(time.time() - start)
    return Response(
        content=json.dumps(payload),
        media_type="application/json",
        headers={"X-Version": MODEL_VERSION, "X-Experiment": exp},
    )


def _startup() -> None:
    global TRACER
    for name in MODEL_NAMES:
        entry = REGISTRY.load(name)
        log.info(json.dumps({"type": "model_loaded", "name": name, "sha": entry["sha"]}))
    TRACER = _tracer()


_startup()


@bentoml.service(name="model_service", traffic={"timeout": 30})
@bentoml.asgi_app(api, path="/")
class ModelService:
    """BentoML 负责进程管理、/metrics、/healthz、/readyz；业务路由由挂载的 FastAPI 提供。"""
