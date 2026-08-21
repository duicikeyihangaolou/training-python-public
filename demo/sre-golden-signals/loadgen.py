#!/usr/bin/env python3
"""简易流量发生器：持续打 /api/orders 与 /api/pay，用于课堂演示 QPS / 错误率。"""

from __future__ import annotations

import argparse
import concurrent.futures
import random
import time
import urllib.error
import urllib.request


def hit(base: str, path: str) -> int:
    url = f"{base.rstrip('/')}{path}"
    req = urllib.request.Request(url, method="GET" if path.startswith("/api/orders") else "POST")
    if path.startswith("/api/pay"):
        req = urllib.request.Request(url, data=b"{}", method="POST")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8088")
    parser.add_argument("--qps", type=float, default=8.0, help="目标近似 QPS")
    parser.add_argument("--seconds", type=int, default=120)
    args = parser.parse_args()

    paths = ["/api/orders", "/api/orders", "/api/pay"]
    interval = 1.0 / max(args.qps, 0.1)
    end = time.time() + args.seconds
    ok = err = 0
    print(f"loadgen -> {args.base} qps≈{args.qps} for {args.seconds}s")

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
        while time.time() < end:
            path = random.choice(paths)
            fut = pool.submit(hit, args.base, path)
            fut.add_done_callback(
                lambda f: None
            )
            try:
                code = fut.result(timeout=6)
                if 200 <= code < 400:
                    ok += 1
                else:
                    err += 1
            except Exception:
                err += 1
            time.sleep(interval)

    print(f"done ok={ok} err={err}")


if __name__ == "__main__":
    main()
