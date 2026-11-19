#!/usr/bin/env bash
# ms-lab 故障注入（Java + Python 两侧），任一断言失败即非零退出。仅操作 ms-lab 命名空间。
#  1. Java：inventory 加延迟 → 下单应出现降级体（degraded:true），且 /rca 的嫌疑第一名是 inventory-service（§12.3）
#  2. Python：recommend-canary 加延迟 → ai-governor /route 切到 recommend（§10.1）；
#     延迟超过 bff 读超时 → bff 返回非 null 降级体（§13.2）
# 无论成功失败都会清零所有注入。
set -euo pipefail
HOST="${MS_LAB_HOST:-103.198.127.21}"
GW="http://${HOST}:30888"
MS="${CHAOS_MS:-2000}"
NS="ms-lab"

free_port() {
  python3 - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

inject() {
  local ms="$1"
  local pf_port pf_pid=0
  pf_port="$(free_port)"
  kubectl -n "$NS" port-forward --address 127.0.0.1 svc/inventory-service "${pf_port}:8080" \
    >/tmp/ms-lab-chaos-pf.log 2>&1 &
  pf_pid=$!
  for _ in $(seq 1 40); do
    if curl -sf -o /dev/null --connect-timeout 1 \
      -X POST "http://127.0.0.1:${pf_port}/chaos/latency" \
      -H 'Content-Type: application/json' \
      -d "{\"ms\": ${ms}}"; then
      kill "${pf_pid}" 2>/dev/null || true
      wait "${pf_pid}" 2>/dev/null || true
      return 0
    fi
    if ! kill -0 "${pf_pid}" 2>/dev/null; then
      break
    fi
    sleep 0.25
  done
  kill "${pf_pid}" 2>/dev/null || true
  wait "${pf_pid}" 2>/dev/null || true
  echo "chaos inject failed (ms=${ms}); see /tmp/ms-lab-chaos-pf.log" >&2
  cat /tmp/ms-lab-chaos-pf.log >&2 || true
  return 1
}

# 无论成功失败都清零注入延迟
# 在集群内用 ai-governor 的 Python 访问其它服务，避免额外 port-forward
in_cluster_py() { # in_cluster_py <python-code>
  kubectl -n "$NS" exec -i deploy/ai-governor -- python -c "$1"
}
canary_latency() { # canary_latency <ms>
  in_cluster_py "import httpx; print(httpx.post('http://recommend-canary:8080/chaos/latency', json={'ms': $1}, timeout=5).text)" || true
}

trap 'echo "clear chaos"; inject 0 || true; canary_latency 0' EXIT

echo "inject latency ${MS}ms"
inject "$MS"

TOKEN=$(curl -sf -X POST "$GW/public/token" -H 'Content-Type: application/json' -d '{"userId":"u2"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

echo "fire orders"
DEGRADED=0
for i in $(seq 1 12); do
  BODY=$(curl -s -X POST "$GW/api/orders" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"userId":"u2","sku":"sku-2","qty":1}' || true)
  echo "$BODY"
  if echo "$BODY" | grep -qE '"degraded" ?: ?true'; then DEGRADED=1; fi
done

if [[ "$DEGRADED" -ne 1 ]]; then
  echo "FAIL: no degraded response observed under ${MS}ms latency" >&2
  exit 1
fi
echo "inventory chaos OK: degraded responses observed"

echo "== RCA (12.3): trace analysis should point to inventory-service =="
sleep 10  # 等待 OTLP 批量导出
rca_top1() { # rca_top1 <entry>
  kubectl -n "$NS" exec deploy/aiops-detector -- python3 -c \
    "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8080/rca?entry=$1&minutes=5', timeout=30).read().decode())"
}
RCA=$(rca_top1 gateway)
if [[ "$(echo "$RCA" | python3 -c 'import sys,json;print(json.load(sys.stdin)["traces"])')" == "0" ]]; then
  echo "no gateway traces, fall back to entry=order-service"
  RCA=$(rca_top1 order-service)
fi
echo "$RCA" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print("traces=", d["traces"], "top1=", d["top1"])
for s in d["suspects"][:3]:
    print("  ", s)
assert d["top1"] == "inventory-service", d
'
echo "RCA OK"

echo "== clear inventory chaos before the Python phase =="
inject 0

echo "== python chaos: recommend-canary latency 300ms -> /route prefers recommend =="
canary_latency 300
# 对两个实例持续发流量，让 Prometheus 采到延迟序列
kubectl -n "$NS" exec -i deploy/ai-governor -- python - 45 <<'PYEOF'
import sys, time, httpx
end = time.time() + float(sys.argv[1])
n = 0
with httpx.Client(timeout=5.0) as c:
    while time.time() < end:
        for base in ("http://recommend:8080", "http://recommend-canary:8080"):
            try:
                c.get(base + "/api/recommend", headers={"X-User-Id": f"u{n % 50}", "X-Experiment": "ranker_v1"})
            except Exception:
                pass
        n += 1
        time.sleep(0.1)
PYEOF
ROUTE=$(in_cluster_py "import httpx; print(httpx.get('http://127.0.0.1:8080/route', timeout=10).text)")
echo "$ROUTE" | python3 -c '
import sys, json
d = json.load(sys.stdin)
for c in d["candidates"]:
    print("  ", c)
assert d["best"] == "recommend", d
by = {c["name"]: c["predicted_ms"] for c in d["candidates"]}
assert by["recommend-canary"] > by["recommend"], by
'
echo "route switch OK"

echo "== python chaos: latency 2500ms > bff read timeout -> non-null degraded body =="
canary_latency 2500
GW_HOST="$HOST" python3 - <<'PYEOF'
import json, os, urllib.request

gw = f"http://{os.environ['GW_HOST']}:30888"

def token(uid):
    req = urllib.request.Request(gw + "/public/token", data=json.dumps({"userId": uid}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=10))["access_token"]

canary_user = None
for i in range(1, 101):
    t = token(f"u{i}")
    req = urllib.request.Request(gw + "/api/recommend", headers={"Authorization": f"Bearer {t}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.headers.get("X-Canary") == "true":
            canary_user, canary_token, first = f"u{i}", t, resp
            break
assert canary_user, "no canary user found in u1..u100"
req = urllib.request.Request(gw + "/api/recommend", headers={"Authorization": f"Bearer {canary_token}"})
with urllib.request.urlopen(req, timeout=15) as resp:
    body = json.load(resp)
    degraded_hdr = resp.headers.get("X-Degraded")
print("canary user", canary_user, "degraded header:", degraded_hdr, "items:", len(body.get("items", [])))
assert body.get("degraded") is True and degraded_hdr == "true", body
assert len(body["items"]) > 0, body
PYEOF
echo "bff fallback OK"

echo "CHAOS OK"
