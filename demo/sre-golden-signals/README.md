# SRE 黄金指标 Demo

配套讲义：[`../../doc/we-know-sre-golden-signals.md`](../../doc/we-know-sre-golden-signals.md)

阿里云 lab
实录：[`../../doc/we-know-sre-golden-signals-lab-ali.md`](../../doc/we-know-sre-golden-signals-lab-ali.md)

## 一键启动

```bash
cd demo/sre-golden-signals
docker compose up -d --build
```

| 组件          | URL                                                    |
| ------------- | ------------------------------------------------------ |
| Grafana       | http://localhost:3000 （admin / admin）                |
| Prometheus    | http://localhost:9090                                  |
| Alertmanager  | http://localhost:9093                                  |
| Demo API      | http://localhost:8088（避免与 KubeClipper :8080 冲突） |
| Node Exporter | http://localhost:9100/metrics                          |

## 常用课堂命令

```bash
# 打流量
python3 loadgen.py --base http://127.0.0.1:8088 --qps 10 --seconds 180

# 注入 20% 错误率（触发 HighErrorRate）
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.2'

# 注入额外 800ms 延迟（触发 HighLatencyP95）
curl -X POST 'http://127.0.0.1:8088/chaos/latency-ms?ms=800'

# 接收告警（另开终端；Linux/macOS 均可通过 host.docker.internal）
python3 webhook_receiver.py

# 恢复
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.02'
curl -X POST 'http://127.0.0.1:8088/chaos/latency-ms?ms=0'
```

## AIOps（第 12 课 · Demo E）

```bash
# 无需 API Key（全班必做）
python3 aiops_agent.py --mode advise --rules-only
python3 aiops_agent.py --mode execute --confirm --rules-only

# 可选：GLM / OpenAI 兼容
pip3 install -r requirements-aiops.txt
export GLM_API_KEY=... GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/ GLM_MODEL=glm-4-flash
python3 aiops_agent.py --mode advise
kubectl apply -f k8s/sre-load-deploy.yaml   # 扩容演示需 K8s
python3 aiops_agent.py --mode execute --confirm
```

详见讲义 [第 12 课](../../doc/we-know-sre-golden-signals.md#第-12-课-简易-aiops-与-ai-场景扩展) 与
lab 实录 §13。
