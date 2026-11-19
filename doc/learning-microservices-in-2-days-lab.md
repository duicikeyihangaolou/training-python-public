# 微服务分布式架构 2 天 — 统一 lab 实录（一个栈：Java 主干 + Python AI）

配套讲义：[`learning-microservices-in-2-days.md`](./learning-microservices-in-2-days.md)（语言无关）\
配套代码：[`../demo/ms-lab/`](../demo/ms-lab/)（唯一的教学栈，命名空间 `ms-lab`）

> 按大纲 §1→§13 的顺序走通，**一个命名空间、一条路径**。\
> **语言分工原则：需要 Java 的地方用 Java，需要 Python 的地方用 Python。**
>
> - **Day 1 + Day 2 §8（§1–§8）：Java。** Spring Cloud 治理：Feign、Nacos、Gateway、Outbox、观测、幂等、金丝雀。
> - **Day 2 §9–§12：Python。** 模型服务化（BentoML + PyTorch）、智能路由与扩缩容（线性回归 + Prophet）、AIOps（STL / IsolationForest / Trace 根因）。
> - **§13：混合。** Java 网关与订单 + Python 模型服务 + AIOps 端到端串联与故障注入。

---

## 0. 阅读指南

### 0.1 状态标记

| 标记 | 含义 |
| ---- | ---- |
| **已实测** | 已在集群上跑通，下文附有实测输出 |
| **待实跑** | 代码与脚本已完成，尚未在集群上验证 |
| **仅讲义** | 讲义讲解或白板环节，无 lab 脚本、无自动化断言 |

> 本版（2026-11-18/19）全部上机项均为 **已实测**；「不上机」项见 [§9](#9-不上机的内容与已知限制)。

### 0.2 一个栈的组成（14 个 Pod）

| 组件 | 语言 | 作用 | 大纲 |
| ---- | ---- | ---- | ---- |
| `gateway` | Java | Spring Cloud Gateway、JWT、`X-Canary` / `X-Experiment` | §4 |
| `order-service` / `inventory-service` / `user-service` | Java | Feign、Nacos 热更新、Outbox、幂等 | §2 §3 §6 §8 |
| `recommend-bff` | Java | 调 Python 模型服务；超时 + 非 null 降级；可选智能路由 | §11 §13 |
| `recommend` / `recommend-canary` | **Python** | **BentoML + PyTorch(CPU)** 排序模型 v1 / v2，热加载 | §9 §11 |
| `ai-governor` | **Python** | `/route` 线性回归智能路由，`/scale` Prophet 扩缩容建议 | §10 |
| `aiops-detector` | **Python** | 阈值告警、STL 残差、IsolationForest 日志、Trace 根因 `/rca` | §12 |
| `nacos` `redis` `jaeger` `prometheus` `grafana` | — | 基础设施 | §3 §6 §7 |

Python 的 `recommend*` 不注册到 Nacos（BentoML 无 Nacos 客户端）；Java 侧用 K8s DNS 调用，Nacos 里只有 Java 服务。

### 0.3 章节 × 语言 × 落点总览

| 大纲章节 | 主题 | 语言 | 落点 | 状态 |
| -------- | ---- | ---- | ---- | ---- |
| §1 | 拆分与选型讨论 | — | 讲义 | 仅讲义 |
| §2.1 | Feign 调库存 | Java | `order-service` → `inventory-service` | 已实测 |
| §2.2 | gRPC | — | 讲义 | 仅讲义 |
| §2.3 | 异步消息 | Java | Outbox + Redis Streams | 已实测 |
| §3 | Nacos 注册 / 配置热更新 | Java | Nacos + `@RefreshScope` | 已实测 |
| §4 | Gateway / JWT / 灰度头 | Java | `gateway` | 已实测 |
| §5 | 熔断降级 | Java | Feign 超时降级 + chaos | 已实测 |
| §6 | 事务消息 | Java | JDBC Outbox + Redis Stream | 已实测 |
| §7 | 链路 / 指标 / 日志 | Java | Jaeger（4 个 Java 服务 + Python 均可见）/ Prometheus / Grafana | 已实测（日志聚合仅讲义） |
| §8 | 幂等 / 金丝雀 | Java | `inventory-service`、`recommend` / `recommend-canary` | 已实测 |
| §9 | 模型服务化 | Python | `model-service`（BentoML + PyTorch）、模型热加载 | 已实测 |
| §10 | 智能路由 / 弹性伸缩 | Python | `ai-governor`：线性回归 `/route`、Prophet `/scale` | 已实测 |
| §11 | 推荐链路 + A/B | Java 编排 + Python 排序 | `recommend-bff` → `recommend*` | 已实测 |
| §12 | AIOps | Python | `aiops-detector`：阈值 / STL / IsolationForest / `/rca` | 已实测 |
| §13 | 综合演示与故障注入 | 混合 | `smoke-e2e.sh`、`chaos.sh` | 已实测 |

---

## 1. 环境与访问

SSH 别名 `acubic-cicd`、节点 IP `103.198.127.21` 仅为**一次实测环境的 example**，请换成你自己的 K8s 节点。环境变量统一为 `MS_LAB_HOST`。

| Lab（example） | SSH 别名 | 公网 IP | 节点 | 实录日期 |
| -------------- | -------- | ------- | ---- | -------- |
| acubic-cicd | `acubic-cicd` | `103.198.127.21` | 单节点 control-plane | 2026-11-18 / 19 |

**访问约定**：NodePort 走**节点 IP**，本机 `127.0.0.1` 可能被拒绝。

| 服务 | NodePort | URL（example） |
| ---- | -------- | -------------- |
| gateway | 30888 | `http://103.198.127.21:30888` |
| nacos | 30848 | `http://103.198.127.21:30848/nacos/` |
| grafana | 30890 | `http://103.198.127.21:30890`（admin/admin） |
| jaeger | 30891 | `http://103.198.127.21:30891` |
| prometheus | 30892 | `http://103.198.127.21:30892` |

`ai-governor`、`aiops-detector`、`recommend*` 是 ClusterIP，课堂里用 `kubectl exec deploy/<name> -- python -c ...` 访问（脚本里已封装）。

---

## 2. 基线探测与部署

### 2.1 基线探测

```bash
ssh acubic-cicd
hostname; nproc; free -h | head -2; df -h / | tail -1
kubectl get nodes -o wide
kubectl get ns | head
kubectl get ns ms-lab 2>&1 || true
```

| 项 | 值 |
| -- | -- |
| OS | Ubuntu 24.04.x LTS，内核 `6.8.0-100-generic` |
| CPU / 内存 / 磁盘 | **64 vCPU / 62 GiB** / 1.8T |
| K8s | v1.35.0，单节点 `ubuntu2404`，containerd 1.7.29 |
| 镜像限制 | Docker Hub 直连可能超时；`export DOCKER_MIRROR=docker.m.daocloud.io`；本机无 JDK/Maven，用容器构建 |

### 2.2 同步 / 构建 / 部署

```bash
# 本机
rsync -az --delete --exclude target demo/ms-lab/ acubic-cicd:/root/ms-lab/

ssh acubic-cicd
cd /root/ms-lab
export DOCKER_MIRROR=docker.m.daocloud.io
bash scripts/build-load.sh   # Java：容器内 Maven；Python：aiops-detector / ai-governor / model-service；全部 ctr import
bash scripts/deploy.sh       # apply 00 → 10 → 40-rbac → 30 → 50，等待所有 Deployment rollout
kubectl -n ms-lab get pods
```

只构建部分模块：`JAVA_MODULES="order-service" PY_MODULES=none bash scripts/build-load.sh`（`JAVA_MODULES=none` 跳过 Java）。

**实测 Pod（2026-11-19，全部 Running；14 个）**

```text
ai-governor-...         1/1  Running  0
aiops-detector-...      1/1  Running  0
gateway-...             1/1  Running  2
grafana-...             1/1  Running  0
inventory-service-...   1/1  Running  1
jaeger-...              1/1  Running  0
nacos-...               1/1  Running  0
order-service-...       1/1  Running  4
prometheus-...          1/1  Running  0
recommend-...           1/1  Running  0
recommend-bff-...       1/1  Running  2
recommend-canary-...    1/1  Running  0
redis-...               1/1  Running  0
user-service-...        1/1  Running  2
```

Java 服务的 `RESTARTS` 1–4 次是**14 个 Pod 同时冷启动**时 liveness 在启动慢时杀过几次（节点上 Nacos 占 CPU），之后稳定；验收只要求 Ready。

**资源占用（`kubectl top` + ResourceQuota，实测）**

| 项 | 值 |
| -- | -- |
| ResourceQuota `ms-lab-quota` | pods 14/40；requests.memory 4288Mi/20Gi；limits.memory 10752Mi/28Gi |
| 内存实际占用 | Nacos ≈1.07Gi；Java 服务 200–380Mi；`recommend*` 各 ≈375Mi；`ai-governor` ≈116Mi；`aiops-detector` ≈139Mi |
| 镜像大小 | `model-service` **1.92GB**（torch CPU）；`aiops-detector` 843MB；`ai-governor` 705MB；Java 服务 500–590MB |

### 2.3 镜像构建注意（Python）

| 问题 | 处理 |
| ---- | ---- |
| `docker build` 内网络访问 pypi.org / download.pytorch.org 常超时或只有百 KB/s | `build-load.sh` 先在**宿主机**用 `curl` 从 `mirrors.aliyun.com/pytorch-wheels/cpu` 下 `torch-2.5.1+cpu` wheel 到 `model-service/wheels/`，Dockerfile `COPY` 后用 `pip -f /wheels` 安装；没有本地 wheel 才回退网络（实测宿主机 17MB/s，容器内 160KB/s） |
| 误装 CUDA 版 torch（数 GB） | 只装 `torch==2.5.1+cpu`，两条网络路径都失败时构建失败 |
| Python 基础镜像 | `docker pull docker.m.daocloud.io/library/python:3.11-slim` 后 tag 为 `ms-lab/python:3.11-slim` |

---

## 3. Day 1 · Java 主干（大纲 §1–§7）

### 3.1 §1 拆分与选型讨论（仅讲义）

订单 / 库存 / 用户拆分练习（§1.2.2）为讨论题，无 lab 脚本。落地到代码即服务边界：`gateway`、`order-service`、`inventory-service`、`user-service`。

### 3.2 §2 服务通信

#### 3.2.1 §2.1.2 Feign 调库存（Java，已实测）

`order-service` 通过 OpenFeign 调 `inventory-service`，Feign `readTimeout≈800ms`，超时返回 **非 null** 降级体。

JWT 下单（Gateway → order → user / inventory），2026-11-19 实测：

```json
{
  "ok": true,
  "code": "CREATED",
  "orderId": "Of08a8ee22322",
  "amountCents": 1000,
  "pool": {"minIdle": 5, "maxSize": 20},
  "inventory": {"ok": true, "code": "RESERVED", "remaining": 497}
}
```

慢调用 / Fallback 见 §3.6（chaos）。

#### 3.2.2 §2.2 gRPC（仅讲义）

gRPC vs REST 性能对比、ProtoBuf IDL 为讲义演示，不进默认 lab。

#### 3.2.3 §2.3 异步消息（Java，已实测）

事件走 **Redis Streams** 作课堂等价 Kafka，真实 Kafka / RocketMQ 不在默认部署。详见 §3.7。

### 3.3 §3 服务发现与配置管理

#### 3.3.1 §3.1 Nacos 注册发现（已实测）

Nacos standalone + `prefer-ip-address`。注册到 Nacos 的有 `order-service` / `inventory-service` / `user-service` / `recommend-bff` / `gateway`；Python 的 `recommend*` 不注册。

> Gateway `lb://` 依赖 Nacos 时课堂不稳，故**课堂路由用 K8s DNS**，Nacos 仍注册供控制台演示。

#### 3.3.2 §3.2.2 连接池热更新（Nacos DataId，已实测）

`order-service` 通过 `spring.config.import: optional:nacos:order-service.yaml` 读取配置，池参数由 `OrderPoolProperties`（`@RefreshScope` + `@ConfigurationProperties("order.pool")`）持有，`/health` 返回当前 `pool.maxSize`。

```bash
# Nacos 仅在内容变化时推送，所以用 31 → 30 交替发布
MS_LAB_HOST=103.198.127.21 bash scripts/publish-nacos-config.sh 31
MS_LAB_HOST=103.198.127.21 bash scripts/publish-nacos-config.sh 30
kubectl -n ms-lab port-forward svc/order-service 38081:8080 &
curl -s http://127.0.0.1:38081/health
```

**验收**：`/health` 的 `pool.maxSize` 在 30 秒内变为 `30`，`kubectl -n ms-lab get pod -l app=order-service` 的 `RESTARTS` 不变。**兜底**：`POST /admin/reload` 只改当前 Pod 内存。

实测输出（2026-11-19，`smoke-e2e.sh`）：

```text
published order-service.yaml max-size=31 min-idle=5
published order-service.yaml max-size=30 min-idle=5
order pool maxSize=30
restartCount unchanged: 4
```

> Nacos standalone 每次容器启动都清空 Derby（见 §8），所以 `smoke-e2e.sh` 每次先发布配置再验收。

### 3.4 §4 网关与安全（Java，已实测）

`gateway`（Spring Cloud Gateway）完成 JWT 验签，透传用户头并注入 `X-Canary` / `X-Experiment`，按 `userId` 稳定分桶。

```bash
HOST="${MS_LAB_HOST:-103.198.127.21}"
TOKEN=$(curl -sf -X POST "http://${HOST}:30888/public/token" \
  -H 'Content-Type: application/json' -d '{"userId":"u1"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

### 3.5 §4.2.2 灰度标识

灰度头 `X-Canary` 默认稳定（`false`），由网关按用户哈希决定，验收见 §4.2。

### 3.6 §5 熔断降级与 chaos（Java，已实测）

```bash
MS_LAB_HOST=103.198.127.21 bash scripts/chaos.sh
```

脚本对 `svc/inventory-service` 做 `kubectl port-forward` + `curl` 注入 `latency=2000ms`，连续下单：Feign readTimeout≈800ms，返回 **非 null** 降级体。规则：**12 笔里至少一笔含 `"degraded":true`，否则非零退出**；无论成败都会 `trap` 清零所有注入（含 Python 侧）。

实测摘录（2026-11-19）：

```json
{"code":"INVENTORY_UNAVAILABLE","ok":false,"degraded":true,
 "message":"feign.RetryableException: Read timed out executing POST http://inventory-service:8080/api/inventory/sku-2/reserve",
 "inventory":{"ok":false,"code":"INVENTORY_UNAVAILABLE","degraded":true}}
```

> Java 主路径为 Feign 超时降级；Sentinel RT 降级规则为辅。`chaos.sh` 后半段还会注入 Python 故障，见 §5.5。

### 3.7 §6 事务消息 / Outbox（Java，已实测）

采用 **JDBC Outbox + Redis Streams**（未上 Seata AT）。订单与 Outbox 事件同事务写入，事件投递到 Redis Stream `order.created`。**验收**：`XLEN order.created ≥ 1`（实测 `XLEN=1`）。「杀进程不丢事件」为仅演示。

### 3.8 §7 可观测性

#### 3.8.1 §7.1 / §7.3.2 链路追踪（Jaeger，已实测）

**全部 Java 服务**（`gateway` / `order-service` / `inventory-service` / `user-service` / `recommend-bff`）都接入 `micrometer-tracing-bridge-otel` + `opentelemetry-exporter-otlp`，经 OTLP HTTP 发到 `jaeger:4318`；`order-service` 另加 `feign-micrometer`，Feign 调用会带 `traceparent`，所以一次下单在 Jaeger 里是 `gateway → order-service → inventory-service/user-service` 的**一条完整链路**。这是 §12.3 根因分析的数据基础。

```bash
curl -s http://103.198.127.21:30891/api/services
```

实测输出（2026-11-19）：

```text
{"data":["order-service","recommend","jaeger-all-in-one","inventory-service","recommend-bff","user-service","gateway"],"total":7,...}
```

注意其中的 `recommend` 是 **Python 的 BentoML 服务**（OTel 服务名 `recommend`）。

#### 3.8.2 §7.2 指标与 Grafana（已实测）

Grafana 与 Prometheus 同 ns，NodePort **30890**，数据源 `Prometheus`（`http://prometheus:9090`）由 ConfigMap 预置，不预置仪表盘。Prometheus 抓取：Java 服务 `/actuator/prometheus`，Python `recommend*` 的 `/metrics`（含自定义 `recommend_requests_total` / `recommend_latency_seconds`）。

```bash
curl -s http://103.198.127.21:30890/api/health
curl -s -u admin:admin http://103.198.127.21:30890/api/datasources
```

实测：`datasources: ['Prometheus']`；`sum(orders_total)=3`。课堂用法：Explore 里输入 `sum by (status) ({__name__=~"orders_total(_total)?"})`。

> **踩坑**：Grafana 首次启动要做数据库迁移，在本节点约需 5–10 分钟，期间 readiness 为 0/1，不是故障。

#### 3.8.3 §7.3 日志聚合（仅讲义）

ELK 不在课堂默认部署；课堂用结构化 JSON 日志代替。§12.1 的日志异常检测直接读 Pod 日志。

---

## 4. Day 2 上午 · Java 主干（大纲 §8）

### 4.1 §8.1.1 幂等（Java，已实测）

`inventory-service` 用 Redis `SETNX` + `X-Idempotency-Key` 防重复消费。同一 key 两次预留：第一次 `RESERVED`、第二次 `DUPLICATE`，库存只扣一次。

```text
first={"ok":true,"code":"RESERVED","remaining":99,"message":""}
second={"ok":true,"code":"DUPLICATE","remaining":99}
```

### 4.2 §8.2.2 10% 金丝雀（已实测）

网关按 `userId` 的稳定哈希，约 10% 流量打到 `recommend-canary`（模型 v2）。

| 维度 | 头 | 决定什么 |
| ---- | -- | -------- |
| 金丝雀 | `X-Canary` / `MODEL_VERSION` | 请求进入哪套 Deployment（`recommend` v1 或 `recommend-canary` v2） |

**验收**：u1..u100 经网关，`X-Canary=true` 在 3–20 之间（实测 13/100）。回滚（`CANARY_PERCENT=0`）为仅演示。

---

## 5. Day 2 · Python AI 与 AIOps（大纲 §9–§12）

> 本节是语言切换点：**从 §9 起，服务实现语言由 Java 切换为 Python**。Python 服务与 Java 在**同一 namespace**，Java `recommend-bff` 通过 HTTP 调用 Python 模型服务。

### 5.1 §9 AI 模型服务化（Python，已实测）

| 大纲小节 | 内容 | 落点 | 状态 |
| -------- | ---- | ---- | ---- |
| §9.1 | 挑战、版本、GPU、训练推理不一致 | 讲义 | 仅讲义 |
| §9.2.1 | BentoML 封装 PyTorch 模型 | `model-service/`：`@bentoml.service` + 挂载 FastAPI；`Ranker` 是 3→8→Tanh→1 的小 MLP | 已实测 |
| §9.2.2 | 模型 v1→v2 无中断切换（热加载） | `/admin/reload-model`：重新读 `/models/*.pt`、原子替换 | 已实测 |
| §9.3 | Kafka + 推理 Worker | Redis Streams 等价，不单独演示 | 仅讲义 |
| Triton | 原厂组件 | 不部署 | 仅讲义 |

**服务结构**（`demo/ms-lab/model-service/`）：

| 文件 | 内容 |
| ---- | ---- |
| `ranker.py` | PyTorch 模型定义与 `load_ranker(path)`（`weights_only=True`） |
| `train.py` | 训练两个排序模型 `ranker_v1`（拟合权重 `0.5/0.3/0.2`）、`ranker_v2`（`0.8/0.15/0.05`）；`--seed` 可模拟「训练出新版本」；先写临时文件再原子替换 |
| `service.py` | `ModelRegistry`（按文件加载、记录 `sha` 与 generation）；FastAPI 路由 `/health`、`/api/recommend`、`/admin/reload-model`、`/chaos/latency`；三阶段 JSON 日志 `recall/rank/rearrange` 与 `ab_split`；`bentoml.metrics` 自定义指标 |
| `Dockerfile` | CPU torch + BentoML；构建时 `train.py` 生成初始权重 |

`recommend` / `recommend-canary` 用同一镜像，仅 `MODEL_VERSION` 不同（v1 / v2）；initContainer 把镜像里的 `/app/models/*.pt` 拷到 emptyDir `/models`，运行时从 `/models` 读取，这样热加载可以不重启容器。

**接口契约**（Java `recommend-bff` 与 Python 之间）：

```text
GET /api/recommend   头：X-User-Id / X-Canary / X-Experiment
  → {"user_id","experiment","model_version","model_sha","canary","items":[{"sku","score"}...]}
     响应头 X-Version / X-Experiment
```

**模型热加载实测**（2026-11-19，`smoke-e2e.sh`）：

```bash
# 在 Pod 内用另一个 seed 重训 ranker_v2，再让服务重新加载
kubectl -n ms-lab exec deploy/recommend -c recommend -- python /app/train.py --out /models --names ranker_v2 --seed 7
kubectl -n ms-lab exec deploy/ai-governor -- python -c "import httpx;print(httpx.post('http://recommend:8080/admin/reload-model',json={'name':'ranker_v2'}).text)"
```

```text
before: sha=03d984008ec5 score=0.887 | after reload: sha=54a39426e2cc score=0.8956
restored: sha=03d984008ec5 score=0.887
recommend restartCount unchanged: 0
```

**验收**：reload 后 `model_sha` 与分数变化，且 `recommend` 的 `restartCount` 不变。网关响应也带 `model_sha`（`model_sha=03d984008ec5 model_version=v1`）。

### 5.2 §10 智能路由与弹性伸缩（Python，已实测）

`ai-governor`（FastAPI，`demo/ms-lab/ai-governor/app.py`）有两个接口，都读本 ns 的 Prometheus。

#### 5.2.1 §10.1 `/route`：线性回归预测延迟，选最快实例

- 对每个候选实例（`ROUTE_CANDIDATES=recommend:8080,recommend-canary:8080`）取近几分钟的 `rate(recommend_latency_seconds_sum)/rate(..._count)` 序列；
- 用 `numpy.polyfit` 做一次线性回归，外推 30 秒后的延迟；
- 返回预测延迟最小的实例；无数据时返回第一个候选。

`recommend-bff` 可用 `SMART_ROUTING=true` 打开：每 5 秒向 `ROUTER_URL/route` 取一次建议，失败退回原来的按头路由。默认关闭，保证 smoke 的金丝雀断言稳定。

```bash
kubectl -n ms-lab exec deploy/ai-governor -- python -c "import httpx;print(httpx.get('http://127.0.0.1:8080/route').text)"
```

实测（chaos：给 canary 注入 300ms 延迟并向两个实例打流量）：

```text
recommend        samples=16 last_ms=1.26   slope_ms_per_min=-0.002 predicted_ms=1.19
recommend-canary samples=14 last_ms=302.33 slope_ms_per_min=50.917 predicted_ms=217.88
route switch OK        # best == recommend
```

#### 5.2.2 §10.2 `/scale`：Prophet 预测 QPS，给出建议副本数

- 读 `sum(rate(http_server_requests_seconds_count{job="gateway"}[1m]))` 的历史；
- 用 **Prophet** 预测未来的 QPS 峰值；
- `replicas = ceil(peak × HEADROOM / QPS_PER_REPLICA)`，夹在 `MIN_REPLICAS..MAX_REPLICAS`；
- 默认只**建议**（`APPLY=false`）；设为 `true` 时通过 K8s API 对 `deployments/recommend` 的 `scale` 子资源打补丁（RBAC 只给 `ai-governor` 这一个权限）；
- Prophet 失败时回退线性外推，并在响应里写 `engine: linear-fallback` 与 `engine_error`。

实测（2026-11-19）：

```json
{"target":"recommend","engine":"prophet","history_points":61,
 "query":"sum(rate(http_server_requests_seconds_count{job=\"gateway\"}[1m]))",
 "last_qps":0.4,"forecast_peak_qps":1.337,"qps_per_replica":5.0,"headroom":1.2,
 "recommended_replicas":1,"current_replicas":1,"applied":false}
```

**验收**：`engine == "prophet"` 且 1 ≤ `recommended_replicas` ≤ 3。

> 踩坑：`prophet==1.1.6` 搭配新版 `cmdstanpy 1.3.x` 会报 `'Prophet' object has no attribute 'stan_backend'`（内置 cmdstan 缺 makefile），需把 `cmdstanpy` 固定为 `1.2.5`，已写进 `ai-governor/requirements.txt`。

### 5.3 §11 推荐链路与 A/B（Java 编排 + Python 排序）

#### 5.3.1 两件事正交

| 维度 | 头 | 决定什么 |
| ---- | -- | -------- |
| 金丝雀 | `X-Canary` / `MODEL_VERSION` | 请求进入哪套 Deployment |
| A/B 实验 | `X-Experiment` | 排序配方（`ranker_v1` / `ranker_v2`，对应两个 `.pt` 权重） |

#### 5.3.2 Java 编排 + Python 排序（已实测）

网关 `AuthHeaderFilter` 用稳定哈希分桶：金丝雀约 10%，实验 50/50。`recommend-bff` 把请求转发给 Python 模型服务；**连接超时 300ms、读超时 1000ms**，超时或异常时返回**非 null 降级体**（`sku-1..8`、`score:0`、`degraded:true`、`model_version:"fallback"`，响应头 `X-Degraded: true`）。

```bash
curl -s "http://103.198.127.21:30888/api/recommend" -H "Authorization: Bearer $TOKEN" \
  -H 'X-Canary: false' -H 'X-Experiment: ranker_v1' | python3 -m json.tool | head -20
curl -s "http://103.198.127.21:30888/api/recommend" -H "Authorization: Bearer $TOKEN" \
  -H 'X-Canary: false' -H 'X-Experiment: ranker_v2' | python3 -m json.tool | head -20
```

**验收**：两次 `items[0].score` 不同；u1..u100 的金丝雀数在 3–20，两桶 `X-Experiment` 各不少于 35。

实测输出（2026-11-19）：

```text
v1 experiment= ranker_v1 top= {'sku': 'sku-6', 'score': 0.7515}
v2 experiment= ranker_v2 top= {'sku': 'sku-2', 'score': 0.887}
A/B scores differ: v1=0.7515 v2=0.887
canary=13/100 experiments={'ranker_v2': 51, 'ranker_v1': 49}
```

分数是 PyTorch 模型的输出，不再是手写权重和。`X-Experiment` 不影响金丝雀分桶，但改变排序与首位商品。

#### 5.3.3 §11.1 推荐三阶段日志

Python 服务每个请求输出三行结构化 JSON：`type` 分别为 `recall`、`rank`、`rearrange`，共享 `request_id`；`ab_split` 行记录分桶。特征与分桶用 `zlib.crc32`（不用内置 `hash()`，后者每个进程随机，重启后分桶会变）。

#### 5.3.4 §11.3.2 A/B 实验层日志（实操 20 min）

验收：分桶稳定（重启后同一用户落同一桶）+ `ab_split` 日志可见。实验 ≠ 发布，见讲义 §11.3.2。

#### 5.3.5 §11.1–§11.2 Milvus / ONNX / 缓存

Milvus、ONNX Runtime、Redis + Caffeine 特征缓存未在 lab 部署，为仅讲义。

### 5.4 §12 AIOps 智能告警（Python，已实测）

`aiops-detector`（`demo/ms-lab/aiops-detector/`）：一个 FastAPI 服务，三类检测 + 原有阈值告警。

| 能力 | 接口 | 算法 | 数据来源 |
| ---- | ---- | ---- | -------- |
| §12.2.2 阈值 + 自适应告警 | 后台循环 + `/health` | 夜间 / 日间阈值；`μ - max(σ, 0.02)` 自适应 | Prometheus 订单成功率 |
| §12.2.1 指标 STL 残差 | `/anomaly/stl` | `statsmodels` STL（robust），对残差做 MAD z-score | 请求体序列，或 Prometheus |
| §12.1 日志异常检测 | `/anomaly/logs` | `scikit-learn` IsolationForest：30 秒窗口的 `n/errors/error_ratio/templates/mean_len`；只有 `predict==-1` 且 `error_ratio` 高于中位数才标记 | 请求体日志行，或 K8s API 读 Pod 日志（Role 允许 `pods/log`） |
| §12.3 Trace 根因 | `/rca?entry=gateway&minutes=10` | 见下 | Jaeger HTTP API（`/api/traces`） |

**判定规则（阈值告警）**：夜间窗口按**北京时间**（`TZ_NAME=Asia/Shanghai`）的 `NIGHT_START=0..NIGHT_END=7`，阈值 `NIGHT_THR=0.85`；其余时段 `DAY_THR=0.99`；采样 ≥5 个点后，当前成功率低于 `μ - max(σ, 0.02)` 也告警。无流量时 PromQL 分母为 0 须过滤为空（`/ (sum(rate(orders_total[1m])) > 0)`），否则空闲时会持续误报。

```bash
HOST="${MS_LAB_HOST:-103.198.127.21}"
# 注入失败订单（不存在的 SKU → orders_total{status=error}）
for i in $(seq 1 20); do
  curl -s -X POST "http://${HOST}:30888/api/orders" \
    -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"userId":"u1","sku":"sku-missing","qty":1}' || true
done
kubectl -n ms-lab exec deploy/aiops-detector -- \
  python3 -c 'import urllib.request;print(urllib.request.urlopen("http://127.0.0.1:8080/health").read().decode())'
```

无流量、无故障时 `{"ok":true,"service":"aiops-detector","last_alert":null,"samples":[1.0,1.0,1.0,1.0,1.0]}`；注入失败订单后 `last_alert` 出现 `ALERT order_success_rate=...`（阈值告警沿用此前的实测输出，本轮 smoke 只断言 `/health` 与新增的三个检测）。

#### 5.4.1 §12.2.1 / §12.1 离线验收（合成数据）

`smoke-e2e.sh` 先用**合成数据**验证算法（不依赖线上有没有故障）：

```text
stl anomalies: [40]                       # 在第 40 个点注入尖峰，STL 残差检出
log anomalous windows: [{'window_start': '...22:23:00', 'n': 20, 'errors': 20, 'error_ratio': 1.0, 'score': -0.7671},
                        {'window_start': '...22:23:30', 'n': 20, 'errors': 20, 'error_ratio': 1.0, 'score': -0.7691}]
```

线上接口（`/anomaly/stl`、`/anomaly/logs`、`/rca`）在 smoke 里只断言能正常返回（刚部署时数据稀疏，`enough_data=False` 属正常）：`stl online enough_data= False`，`logs online lines= 125`，`rca online traces= 200`。

#### 5.4.2 §12.3 基于 Trace 的根因分析（实操）

算法（`aiops-detector/rca.py`）：

1. 从 Jaeger 拉近 N 分钟、入口服务（默认 `gateway`）的 Trace；
2. 对每条 Trace 算每个服务的 **self time**（span 耗时减去其子 span 耗时）；
3. 各服务的 self time 与所有 Trace 的**中位数基线**比较，得到**超额耗时**（至少 20ms 才计）；
4. 找**错误起点 span**（自己报错、且其子 span 没有报错）——上游被动级联的错误不计；
5. 打分 = 0.7 × 归一化超额耗时 + 0.3 × 归一化错误起点数，降序输出嫌疑服务。

用 chaos 验证（见 §5.5）：给 inventory 注入 2000ms 延迟 + 连发订单，`/rca` 应把 `inventory-service` 排第一。实测：

```text
traces= 200 top1= inventory-service
   {'service': 'inventory-service', 'score': 0.4805, 'excess_self_ms': 24061.3, 'baseline_self_ms': 0.0}
   {'service': 'order-service',     'score': 0.1945, 'excess_self_ms':  9739.9, 'baseline_self_ms': 0.0}
   {'service': 'gateway',           'score': 0.0172, 'excess_self_ms':   859.8, 'baseline_self_ms': 2.94}
RCA OK
```

误报回放与标注反馈为仅演示。SkyWalking 不部署，用 Jaeger API 代替。

### 5.5 §13 综合演示与故障注入（混合）

```text
用户 → Java gateway（JWT / 灰度头）→ order-service（Feign + Outbox）→ inventory / user
     → recommend-bff（超时 300/1000ms，降级非 null）→ Python recommend / recommend-canary（BentoML + PyTorch）
     → ai-governor（/route 选实例，/scale 建议副本）
     → aiops-detector（阈值告警、STL、IsolationForest、/rca）
     → Jaeger / Prometheus / Grafana
```

`scripts/chaos.sh` 依次做：

| 步骤 | 注入 | 断言 |
| ---- | ---- | ---- |
| 1 | inventory 延迟 2000ms | 12 笔下单至少一笔 `degraded:true` |
| 2 | （同上，等 10s 让 span 导出） | `/rca` 的 `top1 == inventory-service` |
| 3 | 清零 inventory；`recommend-canary` 延迟 300ms；向两个实例打 45s 流量 | `/route` 的 `best == recommend`，且 canary 预测延迟更高 |
| 4 | `recommend-canary` 延迟 2500ms（> bff 读超时） | 取一个金丝雀用户请求网关：响应体 `degraded:true`、头 `X-Degraded: true`、`items` 非空 |
| 清理 | `trap EXIT` 清零 inventory 与 canary 注入 | — |

实测（2026-11-19）：

```text
inventory chaos OK: degraded responses observed
RCA OK
route switch OK
canary user u10 degraded header: true items: 8
bff fallback OK
CHAOS OK
clear chaos
{"ok":true,"chaos_latency_ms":0}
```

**压测**：wrk + GPU 监控为讲义演示，lab 无 GPU（CPU 推理）。

---

## 6. 端到端 smoke 断言汇总

```bash
MS_LAB_HOST=103.198.127.21 bash scripts/smoke-e2e.sh
MS_LAB_HOST=103.198.127.21 bash scripts/chaos.sh
```

任一断言失败即非零退出。

| 步骤 | 断言 | 对应大纲 |
| ---- | ---- | -------- |
| 下单 | `code == CREATED` | §2 |
| Outbox | Redis Stream `order.created` 的 `XLEN ≥ 1` | §6 |
| Nacos 热更新 | 发布 `max-size=31`、`30`，`/health` 在 30 秒内跟随，`restartCount` 不变 | §3.2.2 |
| 池参数 | `/admin/reload` 改 25 后 `/health` 为 25；再经 Nacos 发布恢复 | §3.2.2 |
| 推荐（A/B） | `X-Experiment` 改变 `items[0].score` | §11 |
| 金丝雀 + A/B 分桶 | u1..u100：`X-Canary=true` 在 3–20；两桶各 ≥ 35 | §8.2 / §11.3 |
| 模型服务 | 网关响应带 `model_sha` | §9 |
| 模型热加载 | 重训 + `reload-model`：`sha` 与分数变化，`restartCount` 不变；随后恢复 | §9.2.2 |
| 幂等 | 同一 `X-Idempotency-Key` 两次：`RESERVED` → `DUPLICATE` | §8.1 |
| AIOps 健康 | `/health` 返回 `ok: true` | §12 |
| STL / 日志 / RCA（离线） | STL 在尖峰处检出；日志 burst 窗口被标记；合成 Trace 的 `top1 == inventory-service` | §12 |
| AIOps 在线接口 | `/anomaly/stl`、`/anomaly/logs`、`/rca` 可返回 | §12 |
| 智能路由 | 打流量后 `/route` 返回候选与预测延迟 | §10.1 |
| 扩缩容建议 | `/scale` 的 `engine == "prophet"`，1 ≤ 副本数 ≤ 3 | §10.2 |
| Grafana | `30890 /api/health` 为 `database: ok`；数据源含 `Prometheus` | §7.2 |
| Jaeger | `30891 /api/services` 含 `order-service` | §7.1 |
| Prometheus | `sum(orders_total)` 大于 0 | §7.2 |

**实测结果（2026-11-19，同一节点，旧两个 ns 删除后一次构建 → 部署 → 验收）**

| 脚本 | 结果 | 备注 |
| ---- | ---- | ---- |
| `smoke-e2e.sh` | `SMOKE OK`，退出码 0 | 三次运行才通过，见下方踩坑：JVM 冷启动 reserve 超时、Prophet 回退 |
| `chaos.sh` | `CHAOS OK`，退出码 0 | 一次通过 |

---

## 7. 大纲对标总表（讲义实操 ↔ 本实录）

| 讲义实操 / 能力 | 语言 | 实现 | 验收入口 | 状态 |
| --------------- | ---- | ---- | -------- | ---- |
| §1.2.2 拆分讨论 | — | 白板 | — | 仅讲义 |
| §2.1.2 Feign 调库存 | Java | `order-service` → `inventory-service`，超时降级非 null | §3.6 | 已实测 |
| §2.2 gRPC | — | 讲义 | — | 仅讲义 |
| §2.3 异步消息 | Java | Redis Streams（等价 Kafka） | §3.7 | 已实测 |
| §3.1 Nacos 注册发现 | Java | nacos standalone + `prefer-ip-address` | Nacos 实例列表 | 已实测 |
| §3.2.2 连接池热更新 | Java | Nacos `order-service.yaml` + `@RefreshScope` | §3.3.2 | 已实测 |
| §4.2.2 JWT + 灰度头 | Java | gateway `30888`，`X-Canary` / `X-Experiment` | §3.4 | 已实测 |
| §5.2.3 慢调用熔断 | Java | Feign 超时降级为主路径 | §3.6 | 已实测 |
| §6.2.4 事务消息 / Outbox | Java | Outbox + Redis Stream `order.created` | §3.7 | 已实测 |
| §7.1 / §7.3.2 链路追踪 | Java + Python | Java 五个服务与 Python `recommend` 的 OTLP → Jaeger，Feign 传播 trace | §3.8.1 | 已实测 |
| §7.2 指标 / Grafana | Java + Python | Prometheus 抓 Java 与 BentoML `/metrics` | §3.8.2 | 已实测 |
| §8.1.1 幂等 | Java | inventory Redis `SETNX` + `X-Idempotency-Key` | §4.1 | 已实测 |
| §8.2.2 10% 金丝雀 | Java + Python | 网关哈希 + `recommend` / `recommend-canary` | §4.2 | 已实测 |
| §9.2.1 BentoML 封装模型 | Python | `model-service`：BentoML + PyTorch(CPU) | §5.1 | 已实测 |
| §9.2.2 模型 v1→v2 无中断 | Python | `/admin/reload-model` 热加载 + 原子替换 | §5.1 | 已实测 |
| §10.1 智能路由 | Python | `ai-governor /route`：线性回归 | §5.2.1 | 已实测 |
| §10.2 预测扩缩容 | Python | `ai-governor /scale`：Prophet + Prometheus | §5.2.2 | 已实测 |
| §11.1 推荐三阶段 | Java + Python | bff 编排；Python 日志 `recall/rank/rearrange` | §5.3.3 | 已实测 |
| §11.3.2 A/B 实验层 | Java + Python | `X-Experiment` 驱动排序模型；crc32 分桶 + `ab_split` 日志 | §5.3 | 已实测 |
| §12.1 日志异常 | Python | IsolationForest | §5.4 | 已实测（合成数据 + 线上接口） |
| §12.2.1 STL | Python | `statsmodels` STL + MAD | §5.4 | 已实测（合成数据 + 线上接口） |
| §12.2.2 智能告警 | Python | `aiops-detector`（北京时间夜间窗口） | §5.4 | 已实测 |
| §12.3 根因分析 | Python | Jaeger Trace + 自耗时超额 + 错误起点 | §5.4.2 | 已实测（chaos） |
| §13 综合演示 | 混合 | `smoke-e2e.sh` + `chaos.sh` | §5.5 / §6 | 已实测 |

---

## 8. 踩坑摘要

| 问题 | 处理 |
| ---- | ---- |
| Docker Hub `i/o timeout` | `export DOCKER_MIRROR=docker.m.daocloud.io` 后重跑 `build-load.sh` |
| `curl 127.0.0.1:<NodePort>` connection refused | 改用节点 IP |
| pip 慢 | Dockerfile `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple` |
| `docker build` 里下 torch（175MB）卡住 | 宿主机预下载 wheel 再 `COPY`（见 §2.3） |
| `statsmodels 0.14.4` 报 `cannot import name '_lazywhere' from 'scipy._lib._util'` | 固定 `scipy==1.13.1`（`aiops-detector/requirements.txt`）；这会让 Pod 反复被 liveness 杀掉，`kubectl logs` 却是空的，要在宿主机 `docker run ... python -c "import statsmodels.api"` 才能看到真实报错 |
| Prophet 报 `'Prophet' object has no attribute 'stan_backend'` | 固定 `cmdstanpy==1.2.5`（`1.3.x` 校验内置 cmdstan 的 makefile 失败） |
| Maven 报 `io.micrometer:context-propagation:jar` 缺版本 | Spring Boot 3.2.5 BOM 不管理它，gateway 里显式写 `1.1.1` |
| JVM 冷启动：首个 reserve 请求约 5s，超过 Feign 读超时（800ms） | smoke 下单前对 `inventory` 预热一次 `POST .../reserve`（不仅是 GET） |
| 14 个 Pod 同时冷启动，Java 服务被 liveness 重启 1–4 次 | 属启动期现象，之后稳定；验收只看 Ready |
| Nacos Derby `service.properties` / Login timeout | 每次启动 `rm -rf` data；Memory emptyDir；Recreate；加大内存 |
| Nacos 重启后配置丢失 | Derby 随容器清空，`smoke-e2e.sh` 每次先 `publish-nacos-config.sh` |
| Nacos 发布内容与当前相同时不推送 | 测试热更新交替取值（31 ↔ 30） |
| 命名空间 ResourceQuota 要求 limits | 所有容器必须写 requests/limits |
| H2 双 Pod 抢锁 | order-service `strategy: Recreate` |
| `@Value` 不会热刷新 | 池参数用 `@RefreshScope` + `@ConfigurationProperties` |
| Gateway `lb://` 依赖 Nacos | 课堂路由用 K8s DNS |
| AIOps「夜间」判断错位 | 用 `TZ_NAME=Asia/Shanghai`，不用 UTC |
| AIOps 无流量误报 `ALERT ... rate=0` | PromQL 分母为 0 须过滤为空，不要 `clamp_min` 兜底成 0 |
| `kubectl exec` 传 stdin 失败 | 使用 `kubectl exec -i` |
| 内置 `hash()` 分桶重启后变化 | 用 `zlib.crc32` |
| 本地端口转发 18081 被占用 | smoke 用 38081–38085；先 `ss -ltnp`，**不要**停别人的容器 |
| `IfNotPresent` + 同名 `:dev` 镜像，重建后 Pod 不换新 | 重新 `ctr import` 后 `kubectl rollout restart` |
| curl 直接拼 PromQL，`{}` 被当作通配符 | 用 `curl -G --data-urlencode 'query=...'` |
| Grafana 首次启动数据库迁移慢（5–10 分钟） | 等 readiness 为 1 再验收 |
| `ssh host 'pkill -f build-load.sh'` 把 ssh 自己杀了（退出码 255） | 写成 `pkill -f "[b]uild-load.sh"`，让正则不匹配自身命令行 |

---

## 9. 不上机的内容与已知限制

**不在课堂默认部署**（讲义说明为主）：Seata AT、真实 Kafka / RocketMQ、Milvus、Triton、SkyWalking、ELK / Fluentd、GPU 压测。

**已知限制**：

- `recommend*` 不注册 Nacos，Java 用 K8s DNS 调用。
- `ai-governor` 默认只给扩缩容**建议**；`APPLY=true` 才会真正改副本数。
- 线上 STL / 日志检测刚部署时数据稀疏，`enough_data=False` 属正常；算法正确性由合成数据保证。
- 智能路由（`SMART_ROUTING=true`）默认关闭；开启后金丝雀比例不再由网关哈希保证。
- `model-service` 镜像 1.92GB，首次构建与 `ctr import` 各需数分钟。

---

## 10. 清理（可选）

```bash
kubectl delete ns ms-lab
# 镜像可保留：
ctr -n k8s.io images ls | grep 'ms-lab/'
```
