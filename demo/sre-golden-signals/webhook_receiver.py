#!/usr/bin/env python3
"""本地 webhook 接收器：打印 Alertmanager JSON，并追加 JSONL 供 AIOps 读取。"""

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ALERTS_JSONL = Path(os.environ.get("SRE_AIOPS_ALERTS_JSONL", "/tmp/sre-aiops-alerts.jsonl"))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        print("=" * 60, flush=True)
        print(f"POST {self.path}", flush=True)
        try:
            data = json.loads(body.decode("utf-8"))
            print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)
            record = {"ts": time.time(), "path": self.path, "payload": data}
            ALERTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
            with ALERTS_JSONL.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            print(body, flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    host, port = "0.0.0.0", 9999
    print(f"webhook listener on http://{host}:{port}", flush=True)
    print(f"jsonl -> {ALERTS_JSONL}", flush=True)
    HTTPServer((host, port), Handler).serve_forever()
