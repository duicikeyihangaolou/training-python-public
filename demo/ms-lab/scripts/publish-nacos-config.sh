#!/usr/bin/env bash
# 向 Nacos 发布 order-service 池参数（DataId=order-service.yaml，Group=DEFAULT_GROUP）。
# 用法：MS_LAB_HOST=<节点IP> bash scripts/publish-nacos-config.sh <maxSize> [minIdle]
set -euo pipefail
HOST="${MS_LAB_HOST:-103.198.127.21}"
MAX_SIZE="${1:?usage: publish-nacos-config.sh <maxSize> [minIdle]}"
MIN_IDLE="${2:-5}"

CONTENT=$(printf 'order:\n  pool:\n    max-size: %s\n    min-idle: %s\n' "$MAX_SIZE" "$MIN_IDLE")

RESP=$(curl -sf -X POST "http://${HOST}:30848/nacos/v1/cs/configs" \
  --data-urlencode "dataId=order-service.yaml" \
  --data-urlencode "group=DEFAULT_GROUP" \
  --data-urlencode "type=yaml" \
  --data-urlencode "content=${CONTENT}")

if [[ "$RESP" != "true" ]]; then
  echo "publish failed: ${RESP}" >&2
  exit 1
fi
echo "published order-service.yaml max-size=${MAX_SIZE} min-idle=${MIN_IDLE}"
