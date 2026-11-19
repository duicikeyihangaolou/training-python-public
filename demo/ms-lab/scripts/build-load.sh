#!/usr/bin/env bash
# 构建 ms-lab 镜像并导入当前节点的容器运行时。
# - 默认（单节点 kubeadm / containerd）：docker save | ctr -n k8s.io images import
# - kind 客户机：KIND_CLUSTER=ms-lab bash scripts/build-load.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DOCKER_MIRROR="${DOCKER_MIRROR:-docker.m.daocloud.io}"
MAVEN_IMAGE="${MAVEN_IMAGE:-${DOCKER_MIRROR}/library/maven:3.9-eclipse-temurin-17}"
JRE_IMAGE="${JRE_IMAGE:-eclipse-temurin:17-jre}"
KIND_CLUSTER="${KIND_CLUSTER:-}"

load_image() {
  local img="$1"
  if [[ -n "$KIND_CLUSTER" ]]; then
    echo "=== kind load $img → cluster $KIND_CLUSTER ==="
    # 经镜像站 pull/tag 后，kind load docker-image 偶发
    # "content digest ... not found"；改走 image-archive 更稳。
    local tmp
    tmp="$(mktemp /tmp/ms-lab-img-XXXXXX.tar)"
    docker save -o "$tmp" "$img"
    kind load image-archive "$tmp" --name "$KIND_CLUSTER"
    rm -f "$tmp"
  else
    docker save "$img" | ctr -n k8s.io images import -
  fi
}

pull_tag() {
  # usage: pull_tag <local-tag> <mirror-ref> [fallback-ref]
  local local_tag="$1" mirror_ref="$2" fallback_ref="${3:-}"
  if docker image inspect "$local_tag" >/dev/null 2>&1; then return 0; fi
  if docker pull --platform linux/amd64 "$mirror_ref"; then
    docker tag "$mirror_ref" "$local_tag" 2>/dev/null || true
  elif [[ -n "$fallback_ref" ]]; then
    docker pull --platform linux/amd64 "$fallback_ref"
    docker tag "$fallback_ref" "$local_tag" 2>/dev/null || true
  else
    docker pull --platform linux/amd64 "$local_tag"
  fi
}

ensure_jre() {
  pull_tag eclipse-temurin:17-jre "${DOCKER_MIRROR}/library/eclipse-temurin:17-jre"
}

ensure_nacos() {
  pull_tag nacos/nacos-server:v2.3.2 \
    "${DOCKER_MIRROR}/nacos/nacos-server:v2.3.2" \
    nacos/nacos-server:v2.3.2
  load_image nacos/nacos-server:v2.3.2 || true
}

ensure_python() {
  pull_tag ms-lab/python:3.11-slim "${DOCKER_MIRROR}/library/python:3.11-slim"
}

# 基础设施公共镜像（客户自备机必拉；国内默认走 DOCKER_MIRROR）
ensure_infra() {
  local pairs=(
    "redis:6.2.16-alpine|${DOCKER_MIRROR}/library/redis:6.2.16-alpine"
    "docker.io/jaegertracing/all-in-one:1.57|${DOCKER_MIRROR}/jaegertracing/all-in-one:1.57"
    "quay.io/prometheus/prometheus:v2.54.1|${DOCKER_MIRROR}/quay.io/prometheus/prometheus:v2.54.1"
    "grafana/grafana:11.2.0|${DOCKER_MIRROR}/grafana/grafana:11.2.0"
  )
  local item local_tag mirror_tag
  for item in "${pairs[@]}"; do
    local_tag="${item%%|*}"
    mirror_tag="${item##*|}"
    pull_tag "$local_tag" "$mirror_tag" "$local_tag" || true
    load_image "$local_tag" || true
  done
}

ensure_jre
ensure_nacos || true
ensure_python
ensure_infra || true

# 只构建部分 Java 模块：JAVA_MODULES="order-service" bash scripts/build-load.sh；JAVA_MODULES=none 跳过
MODULES=(${JAVA_MODULES:-user-service inventory-service order-service gateway recommend-bff})
[[ "${MODULES[0]}" == "none" ]] && MODULES=()
for mod in "${MODULES[@]}"; do
  echo "=== building ms-lab/${mod}:dev ==="
  docker build \
    --build-arg "MAVEN_IMAGE=${MAVEN_IMAGE}" \
    --build-arg "JRE_IMAGE=${JRE_IMAGE}" \
    -t "ms-lab/${mod}:dev" \
    -f "${mod}/Dockerfile" .
  load_image "ms-lab/${mod}:dev"
done

# Python 服务：aiops-detector（§12）、ai-governor（§10）、model-service（§9，BentoML + PyTorch CPU）
# 只构建部分：PY_MODULES="model-service" bash scripts/build-load.sh
PY_MODULES=(${PY_MODULES:-aiops-detector ai-governor model-service})

# torch CPU wheel：宿主机直连国内镜像下载（docker build 内部网络常只有百 KB/s），再由 Dockerfile COPY 进去
TORCH_WHEEL="torch-2.5.1+cpu-cp311-cp311-linux_x86_64.whl"
TORCH_WHEEL_URL="${TORCH_WHEEL_URL:-https://mirrors.aliyun.com/pytorch-wheels/cpu/torch-2.5.1%2Bcpu-cp311-cp311-linux_x86_64.whl}"
mkdir -p model-service/wheels
if [[ " ${PY_MODULES[*]} " == *" model-service "* && ! -s "model-service/wheels/${TORCH_WHEEL}" ]]; then
  echo "=== prefetch ${TORCH_WHEEL} ==="
  curl -fL --retry 3 -o "model-service/wheels/${TORCH_WHEEL}.part" "$TORCH_WHEEL_URL" \
    && mv "model-service/wheels/${TORCH_WHEEL}.part" "model-service/wheels/${TORCH_WHEEL}" \
    || echo "WARN: prefetch failed, Dockerfile will fall back to network"
fi
for mod in "${PY_MODULES[@]}"; do
  echo "=== building ms-lab/${mod}:dev ==="
  docker build \
    --build-arg "PYTHON_IMAGE=ms-lab/python:3.11-slim" \
    -t "ms-lab/${mod}:dev" \
    -f "${mod}/Dockerfile" .
  load_image "ms-lab/${mod}:dev"
done

echo DONE
if [[ -n "$KIND_CLUSTER" ]]; then
  echo "KIND_CLUSTER=$KIND_CLUSTER images loaded via kind"
else
  ctr -n k8s.io images ls -q | grep -E 'ms-lab/|nacos|redis|jaeger|prometheus|grafana' || true
fi
