#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# bare-metal / 单节点：order-service hostPath 需要宿主机目录；kind 在节点容器内 DirectoryOrCreate 即可
if [[ -z "${KIND_CLUSTER:-}" ]]; then
  mkdir -p /data/ms-lab 2>/dev/null || sudo mkdir -p /data/ms-lab
fi
kubectl apply -f "$ROOT/k8s/00-namespace.yaml"
kubectl apply -f "$ROOT/k8s/10-infra.yaml"
kubectl apply -f "$ROOT/k8s/40-rbac.yaml"
kubectl apply -f "$ROOT/k8s/30-apps.yaml"
kubectl apply -f "$ROOT/k8s/50-observability.yaml"
for d in redis nacos jaeger prometheus grafana user-service inventory-service order-service recommend recommend-canary recommend-bff gateway aiops-detector ai-governor; do
  kubectl -n ms-lab rollout status deploy/$d --timeout=300s || true
done
kubectl -n ms-lab get pods -o wide
kubectl -n ms-lab get svc
