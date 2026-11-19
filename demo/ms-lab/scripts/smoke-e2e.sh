#!/usr/bin/env bash
# ms-lab 端到端验收（Java 主干 + Python AI）。任一断言失败即非零退出。仅操作 ms-lab 命名空间。
set -euo pipefail
HOST="${MS_LAB_HOST:-103.198.127.21}"
GW="http://${HOST}:30888"
NS="ms-lab"

# wait_for <tries> <sleep_sec> <cmd...>：重试直到命令成功
wait_for() {
  local tries=$1 gap=$2
  shift 2
  for _ in $(seq 1 "$tries"); do
    if "$@"; then return 0; fi
    sleep "$gap"
  done
  echo "timeout waiting for: $*" >&2
  return 1
}

# 端口转发到集群内 Service（仅本 ns）；PF_PID 在 pf_stop 中回收
PF_PID=""
pf_start() { # pf_start <svc> <localport>
  kubectl -n "$NS" port-forward --address 127.0.0.1 "svc/$1" "$2:8080" >/tmp/msl-pf-$1.log 2>&1 &
  PF_PID=$!
  wait_for 30 0.5 curl -sf -o /dev/null "http://127.0.0.1:$2/health"
}
pf_stop() {
  if [[ -n "$PF_PID" ]]; then kill "$PF_PID" 2>/dev/null || true; wait "$PF_PID" 2>/dev/null || true; PF_PID=""; fi
}
trap pf_stop EXIT

restart_count() { # restart_count <app-label>
  kubectl -n "$NS" get pod -l "app=$1" -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'
}

# 在集群内（借 ai-governor 的 Python）驱动 recommend / recommend-canary 的流量，避免额外 port-forward
drive_recommend() { # drive_recommend <seconds>
  kubectl -n "$NS" exec -i deploy/ai-governor -- python - "$1" <<'PYEOF'
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
        time.sleep(0.15)
print("driven", n, "rounds")
PYEOF
}

order_pool_max() { # order_pool_max <localport> -> prints maxSize
  curl -sf "http://127.0.0.1:$1/health" | python3 -c 'import sys,json;print(json.load(sys.stdin)["pool"]["maxSize"])'
}
pool_is() { # pool_is <localport> <expected>
  [[ "$(order_pool_max "$1")" == "$2" ]]
}
stream_ready() {
  [[ "$(kubectl -n "$NS" exec deploy/redis -- redis-cli XLEN order.created)" -ge 1 ]]
}

echo "== token =="
TOKEN=$(curl -sf -X POST "$GW/public/token" -H 'Content-Type: application/json' -d '{"userId":"u1"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
echo "token_len=${#TOKEN}"

echo "== warm up (JVM 冷启动：首个 reserve 请求要 5s 左右，超过 Feign 读超时，先预热) =="
for _ in 1 2 3; do
  kubectl -n "$NS" exec deploy/order-service -- sh -c \
    'curl -s -m 20 -o /dev/null http://inventory-service:8080/api/inventory/sku-1; curl -s -m 20 -o /dev/null -X POST -H "Content-Type: application/json" -d "{\"qty\":1}" http://inventory-service:8080/api/inventory/sku-1/reserve; curl -s -m 10 -o /dev/null http://user-service:8080/actuator/health' || true
done

echo "== create order =="
ORDER=$(curl -sf -X POST "$GW/api/orders" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"userId":"u1","sku":"sku-1","qty":1}')
echo "$ORDER" | python3 -m json.tool
echo "$ORDER" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ok"] is True and d["code"]=="CREATED", d'

echo "== outbox -> redis stream order.created (poll <=30s) =="
wait_for 15 2 stream_ready
echo "XLEN order.created=$(kubectl -n "$NS" exec deploy/redis -- redis-cli XLEN order.created)"

# nacos_set <localport> <value>：发布 max-size 并等待 /health 生效（需先 pf_start）
# Nacos 仅在内容变化时推送，因此每次都用不同的值（31 / 30 交替），保证是真实变更
nacos_set() {
  MS_LAB_HOST="$HOST" bash "$(dirname "$0")/publish-nacos-config.sh" "$2"
  wait_for 30 1 pool_is "$1" "$2"
}

echo "== nacos hot reload: 31 -> 30 via Nacos, no restart =="
RESTARTS_BEFORE=$(kubectl -n "$NS" get pod -l app=order-service -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}')
pf_start order-service 38081
nacos_set 38081 31
nacos_set 38081 30
echo "order pool maxSize=$(order_pool_max 38081)"
pf_stop
RESTARTS_AFTER=$(kubectl -n "$NS" get pod -l app=order-service -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}')
test "$RESTARTS_BEFORE" = "$RESTARTS_AFTER"
echo "restartCount unchanged: $RESTARTS_AFTER"

echo "== admin/reload fallback: maxSize=25 (in-memory only), then restore via Nacos =="
pf_start order-service 38082
curl -sf -X POST "http://127.0.0.1:38082/admin/reload" -H 'Content-Type: application/json' -d '{"maxSize":25}' >/dev/null
test "$(order_pool_max 38082)" = "25"
pf_stop
pf_start order-service 38083
nacos_set 38083 31
nacos_set 38083 30
pf_stop

echo "== recommend: same canary flag, X-Experiment changes ranking score =="
REC1=$(curl -sf "$GW/api/recommend" -H "Authorization: Bearer $TOKEN" -H 'X-Canary: false' -H 'X-Experiment: ranker_v1' -D /tmp/msl-rec1.hdr)
REC2=$(curl -sf "$GW/api/recommend" -H "Authorization: Bearer $TOKEN" -H 'X-Canary: false' -H 'X-Experiment: ranker_v2' -D /tmp/msl-rec2.hdr)
echo "$REC1" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("v1 experiment=",d["experiment"],"top=",d["items"][0])'
echo "$REC2" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("v2 experiment=",d["experiment"],"top=",d["items"][0])'
python3 - "$REC1" "$REC2" <<'PY'
import json, sys
a, b = json.loads(sys.argv[1]), json.loads(sys.argv[2])
assert a["experiment"] == "ranker_v1" and b["experiment"] == "ranker_v2", (a["experiment"], b["experiment"])
assert a["items"][0]["score"] != b["items"][0]["score"], "experiment did not change ranking scores"
print("A/B scores differ: v1=%s v2=%s" % (a["items"][0]["score"], b["items"][0]["score"]))
PY

echo "== canary + A/B split over u1..u100 (via gateway) =="
MS_LAB_HOST="$HOST" python3 - <<'PY'
import json, os, urllib.request
host = os.environ.get("MS_LAB_HOST", "127.0.0.1")
gw = f"http://{host}:30888"
canary = 0
counts = {}
for i in range(1, 101):
    tok = json.load(urllib.request.urlopen(urllib.request.Request(
        gw + "/public/token",
        data=json.dumps({"userId": f"u{i}"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )))["access_token"]
    req = urllib.request.Request(gw + "/api/recommend", headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req) as resp:
        if resp.headers.get("X-Canary") == "true":
            canary += 1
        exp = resp.headers.get("X-Experiment", "unknown")
        counts[exp] = counts.get(exp, 0) + 1
print(f"canary={canary}/100 experiments={counts}")
assert 3 <= canary <= 20, f"canary ratio out of range: {canary}/100"
assert counts.get("ranker_v1", 0) >= 35 and counts.get("ranker_v2", 0) >= 35, f"A/B split out of range: {counts}"
PY

echo "== python model-service: gateway response carries model_sha =="
REC3=$(curl -sf "$GW/api/recommend" -H "Authorization: Bearer $TOKEN" -H 'X-Experiment: ranker_v2')
echo "$REC3" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d.get("model_sha"), d; print("model_sha=", d["model_sha"], "model_version=", d["model_version"])'

echo "== model hot reload (9.2.2): retrain ranker_v2 in the pod, reload with no restart =="
REC_RESTARTS_BEFORE=$(restart_count recommend)
pf_start recommend 38091
rec_score() {
  curl -sf "http://127.0.0.1:38091/api/recommend" -H 'X-User-Id: u1' -H 'X-Experiment: ranker_v2' \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["model_sha"], d["items"][0]["score"])'
}
reload_model() {
  curl -sf -X POST "http://127.0.0.1:38091/admin/reload-model" -H 'Content-Type: application/json' -d '{"name":"ranker_v2"}'
}
read -r SHA0 SCORE0 <<<"$(rec_score)"
kubectl -n "$NS" exec deploy/recommend -c recommend -- python /app/train.py --out /models --names ranker_v2 --seed 7 >/dev/null
reload_model >/dev/null
read -r SHA1 SCORE1 <<<"$(rec_score)"
echo "before: sha=$SHA0 score=$SCORE0 | after reload: sha=$SHA1 score=$SCORE1"
test "$SHA0" != "$SHA1"
test "$SCORE0" != "$SCORE1"
# 还原初始权重，保证后续断言不受影响
kubectl -n "$NS" exec deploy/recommend -c recommend -- python /app/train.py --out /models --names ranker_v2 --seed 42 >/dev/null
reload_model >/dev/null
read -r SHA2 SCORE2 <<<"$(rec_score)"
echo "restored: sha=$SHA2 score=$SCORE2"
pf_stop
test "$REC_RESTARTS_BEFORE" = "$(restart_count recommend)"
echo "recommend restartCount unchanged: $REC_RESTARTS_BEFORE"

echo "== idempotency: same X-Idempotency-Key twice on inventory =="
pf_start inventory-service 38084
IDEM="smoke-$(date +%s)"
R1=$(curl -sf -X POST "http://127.0.0.1:38084/api/inventory/sku-3/reserve" \
  -H 'Content-Type: application/json' -H "X-Idempotency-Key: $IDEM" -d '{"orderId":"O-smoke","qty":1}')
R2=$(curl -sf -X POST "http://127.0.0.1:38084/api/inventory/sku-3/reserve" \
  -H 'Content-Type: application/json' -H "X-Idempotency-Key: $IDEM" -d '{"orderId":"O-smoke","qty":1}')
pf_stop
echo "first=$R1"
echo "second=$R2"
echo "$R1" | python3 -c 'import sys,json; assert json.load(sys.stdin)["code"]=="RESERVED"'
echo "$R2" | python3 -c 'import sys,json; assert json.load(sys.stdin)["code"]=="DUPLICATE"'

echo "== aiops-detector health =="
pf_start aiops-detector 38085
curl -sf "http://127.0.0.1:38085/health" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ok"] is True; print("aiops samples:", d["samples"])'

echo "== aiops offline: STL residual / IsolationForest logs / trace RCA =="
python3 - <<'PYEOF'
import json, math, urllib.request

def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:38085" + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=30))

# 12.2.1 STL：周期 12 的正弦序列，在 index=40 注入尖峰
series = [100 + 10 * math.sin(2 * math.pi * i / 12) + (i % 3) * 0.1 for i in range(72)]
series[40] = 160
r = post("/anomaly/stl", {"series": series, "period": 12})
assert r["enough_data"] and 40 in r["anomaly_indices"], r
print("stl anomalies:", r["anomaly_indices"])

# 12.1 日志：20 个常态窗口 + 1 个错误突发窗口
lines = []
for w in range(20):
    for j in range(10):
        lines.append({"ts": 1_700_000_000 + w * 30 + j, "text": f"INFO order created id={w * 100 + j}"})
for j in range(40):
    lines.append({"ts": 1_700_000_000 + 20 * 30 + j % 25, "text": f"ERROR feign.RetryableException: Read timed out id={j}"})
r = post("/anomaly/logs", {"lines": lines, "window_s": 30})
assert r["enough_data"] and len(r["anomalous"]) >= 1, r
print("log anomalous windows:", r["anomalous"])

# 12.3 RCA：15 条 Trace，后 5 条 inventory-service 自身耗时暴涨
def trace(i, inv_us):
    order_us = inv_us + 60_000
    root_us = order_us + 20_000
    return {
        "traceID": f"t{i}",
        "processes": {"p1": {"serviceName": "gateway"}, "p2": {"serviceName": "order-service"}, "p3": {"serviceName": "inventory-service"}},
        "spans": [
            {"spanID": f"g{i}", "processID": "p1", "duration": root_us, "references": [], "tags": []},
            {"spanID": f"o{i}", "processID": "p2", "duration": order_us, "references": [{"refType": "CHILD_OF", "spanID": f"g{i}"}], "tags": []},
            {"spanID": f"i{i}", "processID": "p3", "duration": inv_us, "references": [{"refType": "CHILD_OF", "spanID": f"o{i}"}], "tags": []},
        ],
    }
traces = [trace(i, 20_000) for i in range(10)] + [trace(10 + i, 2_000_000) for i in range(5)]
r = post("/rca", {"traces": traces})
assert r["top1"] == "inventory-service", r
print("rca top1:", r["top1"], r["suspects"][0])
PYEOF

echo "== aiops online endpoints respond (data may be sparse right after deploy) =="
curl -sf "http://127.0.0.1:38085/anomaly/stl?metric=success&minutes=30" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ok"] is True; print("stl online enough_data=", d.get("enough_data"))'
curl -sf "http://127.0.0.1:38085/anomaly/logs?service=order-service&minutes=30" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ok"] is True; print("logs online lines=", d["lines"], "enough_data=", d.get("enough_data"))'
curl -sf "http://127.0.0.1:38085/rca?entry=gateway&minutes=30" | python3 -c 'import sys,json; d=json.load(sys.stdin); assert d["ok"] is True; print("rca online traces=", d["traces"], "top1=", d["top1"])'
pf_stop

echo "== ai-governor: route advice (linear regression on per-instance latency) =="
drive_recommend 45
pf_start ai-governor 38086
curl -sf "http://127.0.0.1:38086/route" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(json.dumps(d, ensure_ascii=False))
assert d["best"] in ("recommend", "recommend-canary"), d
assert all(c.get("predicted_ms") is not None for c in d["candidates"]), d
'

echo "== ai-governor: scale advice (Prophet forecast of gateway QPS) =="
scale_ready() {
  [[ "$(curl -sf "http://127.0.0.1:38086/scale?minutes=15&step_s=15" | python3 -c 'import sys,json; print(json.load(sys.stdin)["engine"])')" != "no-data" ]]
}
for _ in $(seq 1 6); do curl -s -o /dev/null "$GW/api/recommend" -H "Authorization: Bearer $TOKEN"; done
wait_for 12 5 scale_ready
curl -sf "http://127.0.0.1:38086/scale?minutes=15&step_s=15" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(json.dumps(d, ensure_ascii=False))
assert d["engine"] == "prophet", d
assert isinstance(d["recommended_replicas"], int) and 1 <= d["recommended_replicas"] <= 3, d
'
pf_stop

echo "== grafana datasource (NodePort 30890) =="
curl -sf "http://${HOST}:30890/api/health" | python3 -c 'import sys,json; assert json.load(sys.stdin)["database"]=="ok"'
curl -sf -u admin:admin "http://${HOST}:30890/api/datasources" | python3 -c \
  'import sys,json; names=[d["name"] for d in json.load(sys.stdin)]; print("datasources:", names); assert "Prometheus" in names'

echo "== jaeger services (expect order-service; poll <=30s) =="
jaeger_has_order() {
  local out
  out=$(curl -sf "http://${HOST}:30891/api/services")
  echo "$out"
  [[ "$out" == *'"order-service"'* ]]
}
wait_for 15 2 jaeger_has_order

echo "== prometheus orders_total (name may carry _total suffix) =="
curl -sfG "http://${HOST}:30892/api/v1/query" --data-urlencode 'query=sum({__name__=~"orders_total(_total)?"})' | python3 -c '
import sys, json
d = json.load(sys.stdin)
res = d["data"]["result"]
assert res and float(res[0]["value"][1]) > 0, d
print("sum(orders_total)=", res[0]["value"][1])
'

echo "SMOKE OK order=$(echo "$ORDER" | python3 -c 'import sys,json;print(json.load(sys.stdin)["orderId"])')"
