FROM crpi-wbg5vm8h2xypwe6e.cn-chengdu.personal.cr.aliyuncs.com/gpufusion/python:3.11-slim-bookworm
WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN useradd -m -u 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt
COPY app/ ./app/
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
