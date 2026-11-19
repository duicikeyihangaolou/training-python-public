#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DOCKER_MIRROR="${DOCKER_MIRROR:-docker.m.daocloud.io}"
MAVEN_IMAGE="${MAVEN_IMAGE:-crpi-wbg5vm8h2xypwe6e.cn-chengdu.personal.cr.aliyuncs.com/gpufusion/maven:3.9-eclipse-temurin-17}"
JRE_IMAGE="${JRE_IMAGE:-eclipse-temurin:17-jre}"

ensure_jre() {
  if docker image inspect "$JRE_IMAGE" >/dev/null 2>&1; then return 0; fi
  docker pull "${DOCKER_MIRROR}/library/eclipse-temurin:17-jre"
  docker tag "${DOCKER_MIRROR}/library/eclipse-temurin:17-jre" eclipse-temurin:17-jre
}

ensure_nacos() {
  if ! docker image inspect nacos/nacos-server:v2.3.2 >/dev/null 2>&1; then
    docker pull "${DOCKER_MIRROR}/nacos/nacos-server:v2.3.2" || docker pull nacos/nacos-server:v2.3.2
    docker tag "${DOCKER_MIRROR}/nacos/nacos-server:v2.3.2" nacos/nacos-server:v2.3.2 2>/dev/null || true
  fi
  docker save nacos/nacos-server:v2.3.2 | ctr -n k8s.io images import - || true
}

ensure_python() {
  local py_img="ms-lab/python:3.11-slim"
  if docker image inspect "$py_img" >/dev/null 2>&1; then return 0; fi
  docker pull "${DOCKER_MIRROR}/library/python:3.11-slim"
  docker tag "${DOCKER_MIRROR}/library/python:3.11-slim" "$py_img"
}

ensure_jre
ensure_nacos || true
ensure_python

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
  docker save "ms-lab/${mod}:dev" | ctr -n k8s.io images import -
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
  docker save "ms-lab/${mod}:dev" | ctr -n k8s.io images import -
done

echo DONE
ctr -n k8s.io images ls -q | grep ms-lab || true
