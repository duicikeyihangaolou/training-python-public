#!/usr/bin/env python3
"""AIOps 动作：chaos 回滚、K8s 扩缩容。"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from typing import Any
from urllib.parse import urlencode


def http_json(url: str, method: str = "GET", data: bytes | None = None) -> Any:
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else None


def rollback_chaos(api_base: str = "http://127.0.0.1:8088") -> dict:
    out = {}
    for path, qs in (
        ("/chaos/error-rate", "rate=0.02"),
        ("/chaos/latency-ms", "ms=0"),
    ):
        url = f"{api_base.rstrip('/')}{path}?{qs}"
        req = urllib.request.Request(url, method="POST", data=b"")
        with urllib.request.urlopen(req, timeout=10) as resp:
            out[path] = json.loads(resp.read().decode("utf-8"))
    return out


def inject_chaos(api_base: str = "http://127.0.0.1:8088", error_rate: float = 0.25) -> dict:
    url = f"{api_base.rstrip('/')}/chaos/error-rate?rate={error_rate}"
    req = urllib.request.Request(url, method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_prometheus_alerts(prom: str = "http://127.0.0.1:9090") -> list[dict]:
    data = http_json(f"{prom.rstrip('/')}/api/v1/alerts")
    return data.get("data", {}).get("alerts", [])


def query_prom(prom: str, expr: str) -> Any:
    url = f"{prom.rstrip('/')}/api/v1/query?{urlencode({'query': expr})}"
    return http_json(url)


def kubectl(*args: str) -> str:
    proc = subprocess.run(
        ["kubectl", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "kubectl failed")
    return proc.stdout.strip()


def scale_deployment(name: str, replicas: int, namespace: str = "default") -> str:
    return kubectl(
        "scale",
        "deployment",
        name,
        f"--replicas={replicas}",
        "-n",
        namespace,
    )


def get_deploy_status(name: str, namespace: str = "default") -> str:
    return kubectl(
        "get",
        "deploy,pods",
        "-n",
        namespace,
        "-l",
        f"app={name}",
        "-o",
        "wide",
    )
