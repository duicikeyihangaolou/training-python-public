ARG PYTHON_IMAGE=ms-lab/python:3.11-slim
FROM ${PYTHON_IMAGE}
WORKDIR /app
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
# CPU 版 torch（约 175MB）。docker build 内网络常很慢，所以 build-load.sh 会先在宿主机把 wheel 下到 model-service/wheels/，
# 这里优先用本地 wheel；没有则依次走国内镜像 find-links、官方 cpu 索引（都不可用时构建失败，避免误装数 GB 的 CUDA 轮子）
ARG TORCH_VERSION=2.5.1
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG TORCH_FIND_LINKS=https://mirrors.aliyun.com/pytorch-wheels/cpu
COPY model-service/wheels/ /wheels/
RUN pip install --no-cache-dir "torch==${TORCH_VERSION}+cpu" -f /wheels \
 || pip install --no-cache-dir "torch==${TORCH_VERSION}+cpu" -f "${TORCH_FIND_LINKS}" \
 || pip install --no-cache-dir "torch==${TORCH_VERSION}+cpu" --extra-index-url "${TORCH_INDEX_URL}"
COPY model-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /app/requirements.txt
COPY model-service/ranker.py model-service/train.py model-service/service.py /app/
# 镜像内置 v1/v2 初始权重；运行时由 initContainer 拷贝到可写的 /models（emptyDir），热加载从 /models 读取
RUN python /app/train.py --out /app/models
EXPOSE 8080
CMD ["bentoml", "serve", "service:ModelService", "--host", "0.0.0.0", "--port", "8080"]
