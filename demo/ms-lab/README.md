# ms-lab — Spring Cloud 教学栈（K8s / Java）

配套讲义：[`../../doc/learning-microservices-in-2-days.md`](../../doc/learning-microservices-in-2-days.md)\
Lab 实录（统一，Java 主干 + Python AI）：
[`../../doc/learning-microservices-in-2-days-lab.md`](../../doc/learning-microservices-in-2-days-lab.md)

Namespace：`ms-lab`（现状与 Python 栈 `ms-lab` **互不依赖**，可单独部署验收；目标是把 Python 模型服务 / AIOps 并入本 ns）。

| 组件     | 技术                                                                |
| -------- | ------------------------------------------------------------------- |
| 注册发现 | Nacos（discovery + 配置 DataId `order-service.yaml`）              |
| 网关     | Spring Cloud Gateway + JWT + 灰度头                                 |
| 同步调用 | OpenFeign + LoadBalancer + Sentinel Fallback                        |
| 韧性     | Sentinel 慢调用降级                                                 |
| 一致性   | JDBC Outbox + Redis Streams（课堂优先可跑通；Seata AT 可作为延展）  |
| 热更新   | `order.pool.*` 经 Nacos `@RefreshScope` 热刷新；`/admin/reload` 兜底 |
| AI       | 本 ns `recommend` / `recommend-canary` + `recommend-bff`；`X-Experiment` 决定排序配方 |
| AIOps    | 本 ns `aiops-detector`（订单成功率；北京时间夜间窗口；见统一实录 §5.4） |
| 观测     | Prometheus 抓取 `/actuator/prometheus`；Grafana 预置数据源；order-service OTLP → Jaeger |

NodePort：gateway `30888` · nacos `30848` · jaeger `30891` · prometheus `30892` · grafana `30890`

脚本：`scripts/build-load.sh` · `deploy.sh` · `smoke-e2e.sh` · `chaos.sh` · `publish-nacos-config.sh`（发布池参数到 Nacos）

```bash
export DOCKER_MIRROR=docker.m.daocloud.io
rsync -az ./ acubic-cicd:/root/ms-lab/
ssh acubic-cicd 'cd /root/ms-lab && bash scripts/build-load.sh && bash scripts/deploy.sh'
MS_LAB_HOST=103.198.127.21 bash scripts/smoke-e2e.sh
MS_LAB_HOST=103.198.127.21 bash scripts/chaos.sh
```

详见
[`../../doc/learning-microservices-in-2-days-lab.md`](../../doc/learning-microservices-in-2-days-lab.md)。
