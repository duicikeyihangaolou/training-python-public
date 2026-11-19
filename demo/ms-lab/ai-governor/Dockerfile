ARG PYTHON_IMAGE=ms-lab/python:3.11-slim
FROM ${PYTHON_IMAGE}
WORKDIR /app
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
COPY ai-governor/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY ai-governor/app.py /app/app.py
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
