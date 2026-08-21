# SRE 黄金指标 — 阿里云 lab 实录（ali-k8s-lab）

配套讲义：[`we-know-sre-golden-signals.md`](./we-know-sre-golden-signals.md)\
配套代码：[`../demo/sre-golden-signals/`](../demo/sre-golden-signals/)

> 与讲义的关系：讲义定义「四大黄金指标 + Demo A/B/C」；本文记录在 **ali-k8s-lab** 上用 KubeClipper
> 装 K8s、再跑通同一套 Compose Demo 的命令与踩坑。架构串联图见讲义开头「文档与 Demo 如何串联」。

**主机**：`ssh ali-k8s-lab` → `root@8.130.159.149`（内网 `172.25.209.127`）\
**日期**：2026-08-21\
**目标**：KubeClipper 最新稳定版部署 AIO K8s，再按讲义用 Docker Compose 走通 Demo A/B/C。

---

## 0. 基线探测

```bash
ssh ali-k8s-lab
uname -a
nproc; free -h; df -h /
ip -br a
ss -lntup | head
command -v docker kcctl kubectl || true
```

### 实测结果

| 项                | 值                                                      |
| ----------------- | ------------------------------------------------------- |
| OS                | Ubuntu 24.04.4 LTS（Noble），内核 `6.8.0-137-generic`   |
| CPU / 内存 / 磁盘 | **8 vCPU / 14 GiB / 99G**（可用约 92G）                 |
| 内网 IP           | `172.25.209.127/20`（eth0）                             |
| 初始软件          | 有 Python 3.12.3、curl；**无** Docker / kcctl / kubectl |
| 初始监听          | 仅 SSH `:22`                                            |

资源高于讲义最低要求（4C8G），可继续。

---

## 1. 安装 KubeClipper（kcctl）

```bash
# 国内源；默认安装最新稳定版
curl -sfLk https://oss.kubeclipper.io/get-kubeclipper.sh | KC_REGION=cn bash -
kcctl version
```

### 实测结果

- 脚本提示：`The v1.6.0 version will be installed`
- 包地址：`https://kubeclipper.oss-ap-southeast-1.aliyuncs.com/kc/v1.6.0/kc-linux-amd64.tar.gz`（约
  61MB，本机约 2 分钟下完）
- 安装路径：`/usr/local/bin/kcctl`
- 版本输出（摘要）：

```text
kcctl version: ... GitVersion:"v1.6.0-3+87d297f125e91b" ... Platform:"linux/amd64"
```

同时生成 `/etc/kc/kc.env`（`KC_REGION=cn`）。

---

## 2. 部署 KubeClipper 平台（AIO）

```bash
# All-In-One：本机既做 server 也做 agent；etcd 自动错开端口（12379/12380/12381）
kcctl deploy
```

> 说明：本实录机器上 `kcctl deploy` 已在同日更早完成（`/root/.kc/deploy-config.yaml` 时间戳约
> `2026-08-21 00:14`）。复验时 `kcctl version` 已能连上 `kubeclipper-server`，`kcctl get node`
> 可见节点。

### 部署配置要点（摘自 `/root/.kc/deploy-config.yaml`）

| 项                | 值                                              |
| ----------------- | ----------------------------------------------- |
| pkg               | `.../release/v1.6.0/kc-amd64.tar.gz`            |
| serverPort        | **8080**（API）                                 |
| consolePort       | **80**（Web 控制台）                            |
| server / agent IP | `172.25.209.127`                                |
| etcd              | client `12379` / peer `12380` / metrics `12381` |

### 复验

```bash
kcctl get node
ss -lnt | grep -E '80|8080|12379'
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/
```

结果：节点 `ali-k8s-lab` 已注册；控制台 `:80` 返回 **200**；API `:8080` 在 `172.25.209.127` 监听。

> **端口冲突预判**：KC API 占用 **8080**，故 Demo API 宿主机映射改为 **8088→8080**（见第 4 节）。

控制台默认账号以官方文档 / 部署输出为准（常见为 `admin` / `Thinkbig1`）；本实录以 CLI
为主，未依赖控制台。

---

## 3. 创建 AIO Kubernetes 集群

```bash
NODE=172.25.209.127
kcctl create cluster --name sre-aio --master "$NODE" --untaint-master
```

### 自动选用版本（kcctl 日志）

| 组件       | 版本        |
| ---------- | ----------- |
| Kubernetes | **v1.36.1** |
| containerd | **2.2.4**   |
| Calico     | **v3.31.5** |

创建后状态先为 `Installing`，约 **2–3 分钟**后变为 `Running`：

```bash
# 轮询示例
kcctl get cluster
kubectl get nodes -o wide
kubectl get pods -A
```

### 实测结果

```text
NAME      REGION   MASTER COUNT  WORKER COUNT  STATUS
sre-aio   default  1             0             Running

NAME          STATUS  ROLES           VERSION   INTERNAL-IP      CONTAINER-RUNTIME
ali-k8s-lab   Ready   control-plane   v1.36.1   172.25.209.127   containerd://2.2.4
```

`kube-system` / `calico-system` / `tigera-operator` 下核心 Pod 均为
`Running`（coredns、etcd、apiserver、calico-node 等）。\
Client/Server：`kubectl version` → **v1.36.1**。

---

## 4. 安装 Docker（与 K8s containerd 共存）并修正 Demo

### 4.1 安装踩坑与纠正

官方 Docker CE 安装时，`containerd.io` 包提示覆盖 `/etc/containerd/config.toml`（K8s
已在用）。**必须保留旧配置**：

```bash
export DEBIAN_FRONTEND=noninteractive
# 首次若卡在 conffile 交互导致失败，用 force-confold 收尾
apt-get -y -o Dpkg::Options::="--force-confold" install -f
apt-get -y -o Dpkg::Options::="--force-confold" install \
  docker-ce docker-ce-cli docker-compose-plugin
systemctl enable --now docker
systemctl restart containerd   # 确认 kubelet 侧 containerd 仍正常
kubectl get nodes              # 仍应为 Ready
docker --version
docker compose version
```

### 实测版本

- Docker **29.7.2**
- Docker Compose **v5.5.0**
- 安装后 `kubectl get nodes` 仍为 **Ready**

可选镜像加速（本机写入 `/etc/docker/daemon.json` 的 `registry-mirrors` 后
`systemctl restart docker`）。

### 4.2 Demo 配置纠正（已合入仓库）

相对最初讲义，在 Linux + KubeClipper 同机上必须改：

| 问题                            | 纠正                                                              |
| ------------------------------- | ----------------------------------------------------------------- |
| KC `:8080` vs Demo API `:8080`  | Compose 改为 `"8088:8080"`                                        |
| Linux 无 `host.docker.internal` | `alertmanager.extra_hosts: ["host.docker.internal:host-gateway"]` |
| `nohup` 下 webhook 日志缓冲     | `python3 -u` + `print(..., flush=True)`                           |

本地修正后同步：

```bash
# 在开发机
rsync -az --exclude '__pycache__' \
  demo/sre-golden-signals/ ali-k8s-lab:/root/sre-golden-signals/
```

---

## 5. 拉起 Compose 栈

```bash
ssh ali-k8s-lab
cd /root/sre-golden-signals
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1:8088/health
curl -s http://127.0.0.1:9090/-/ready
curl -s http://127.0.0.1:3000/api/health
```

### 实测结果

全部容器 `Up`；健康检查：

```text
{"status":"ok"}                 # API :8088
Prometheus Server is Ready.
{"database":"ok","version":"11.2.0",...}  # Grafana
```

| 服务            | 宿主机端口                  |
| --------------- | --------------------------- |
| Grafana         | 3000（admin/admin）         |
| Prometheus      | 9090                        |
| Alertmanager    | 9093                        |
| Demo API        | **8088**                    |
| Node Exporter   | 9100                        |
| KC 控制台 / API | **80** / **8080**（勿占用） |

---

## 6. Demo A — 采集与 PromQL

```bash
# Targets
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -c '
import sys,json
for t in json.load(sys.stdin)["data"]["activeTargets"]:
    print(t["labels"].get("job"), t["health"], t["labels"].get("instance"))
'

# 打流
python3 loadgen.py --base http://127.0.0.1:8088 --qps 10 --seconds 240
```

### 实测 Targets

```text
api up api:8080
node up node-exporter:9100
prometheus up localhost:9090
```

### 实测 PromQL（打流约 45s 后）

| 信号           | 查询摘要                                                       | 结果量级                    |
| -------------- | -------------------------------------------------------------- | --------------------------- |
| Traffic        | `sum by (method) (rate(http_requests_total{job="api"}[1m]))`   | GET ≈ 3.27/s，POST ≈ 1.51/s |
| Errors         | 5xx / 全量                                                     | ≈ **1.1%**（默认注入 2%）   |
| Latency P95    | `histogram_quantile(0.95, ...)`                                | ≈ **0.145 s**               |
| Saturation CPU | `100 - avg(rate(node_cpu_seconds_total{mode="idle"}[2m]))*100` | ≈ **31%**                   |

---

## 7. Demo B — Grafana 看板

```bash
curl -s -u admin:admin 'http://127.0.0.1:3000/api/search?query=SRE'
curl -s -u admin:admin 'http://127.0.0.1:3000/api/datasources'
```

### 实测结果

- 文件夹 **SRE**，看板 **SRE Golden Signals**（uid `sre-golden-signals`）
- 数据源 **Prometheus** → `http://prometheus:9090`，`isDefault: true`
- UI：`http://<公网IP>:3000/d/sre-golden-signals/sre-golden-signals`（需安全组放行 3000，或 SSH
  隧道）

---

## 8. Demo C — 故障注入与告警闭环

```bash
# 终端 1：webhook（务必 -u，避免 nohup 缓冲）
cd /root/sre-golden-signals
PYTHONUNBUFFERED=1 python3 -u webhook_receiver.py

# 终端 2：打流
python3 loadgen.py --base http://127.0.0.1:8088 --qps 12 --seconds 300

# 终端 3：注入错误
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.2'
```

### 验收命令

```bash
# Prometheus 告警状态
curl -s http://127.0.0.1:9090/api/v1/alerts | python3 -m json.tool | head

# Alertmanager
curl -s http://127.0.0.1:9093/api/v2/alerts | python3 -m json.tool | head
```

### 实测时间线

1. `HighErrorRate` 先 `pending`（规则 `for: 30s`），约 40s 内变为 **`firing` / critical**
2. 同期可能出现 `HighRequestRate` **firing** / warning（演示阈值 QPS>5）
3. Alertmanager 中状态为 **active**，receiver 含 `critical-webhook` / `default-webhook`
4. webhook 收到 JSON，关键字段：

```json
{
  "receiver": "critical-webhook",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighErrorRate",
        "severity": "critical"
      },
      "annotations": {
        "summary": "API 错误率超过 5%",
        "description": "当前错误率=31.96%。"
      }
    }
  ]
}
```

5. 恢复：

```bash
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.02'
```

随后 webhook 收到 `"status": "resolved"`。

### Demo C 踩坑

| 现象                                      | 原因                                    | 处理                                                                               |
| ----------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------- |
| AM 有告警但 `/tmp/webhook.log` 为空       | Python stdout 在非 TTY/`nohup` 下块缓冲 | `python3 -u` + `flush=True`                                                        |
| `pkill -f webhook_receiver` 误杀 SSH 会话 | `-f` 匹配到远程 `bash -c` 命令行        | 用 `fuser -k 9999/tcp` 或按 PID 结束                                               |
| 容器访问宿主机 webhook                    | Linux 默认无 Docker Desktop 主机名      | Compose `extra_hosts: host.docker.internal:host-gateway`（已验证容器内 POST 可达） |

---

## 9. 可复现命令序列（精简）

```bash
# --- 一次性：KC + K8s ---
curl -sfLk https://oss.kubeclipper.io/get-kubeclipper.sh | KC_REGION=cn bash -
kcctl deploy
kcctl create cluster --name sre-aio --master 172.25.209.127 --untaint-master
# 等待 kcctl get cluster 显示 Running；kubectl get nodes 为 Ready

# --- Docker（保留 K8s containerd 配置）---
# ... 按第 4.1 节 force-confold 安装 docker-ce ...

# --- Demo ---
cd /root/sre-golden-signals   # 或 rsync 同步后的路径
docker compose up -d --build
python3 loadgen.py --base http://127.0.0.1:8088 --qps 10 --seconds 180 &
PYTHONUNBUFFERED=1 python3 -u webhook_receiver.py &
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.2'
# 观察 :9090/alerts 、:9093 、webhook 输出
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.02'
```

---

## 10. 资源占用（Demo 跑完后抽样）

| 项   | 约值                                        |
| ---- | ------------------------------------------- |
| 内存 | 已用 ~2.1 GiB / 14 GiB（available ~12 GiB） |
| 根盘 | ~12G 已用 / 99G（含 KC 包、镜像、TSDB）     |

K8s + Compose 同机可并存；课上勿再装 Istio / kube-prometheus 全栈，除非升到更高规格。

---

## 11. 结论

1. **KubeClipper v1.6.0** AIO 平台 + **K8s v1.36.1** 单节点（`--untaint-master`）在本 ECS 上可顺利
   Running。
2. 讲义 Demo **无需迁入 K8s**；Compose 在同机走通采集 → Grafana → 告警 webhook。
3. 同机必改：**API 8088**、**host-gateway**、**webhook 无缓冲启动**。
4. 安装 Docker 时 **切勿覆盖** K8s 的 `/etc/containerd/config.toml`。

---

## 12. AIOps 端到端（方法论 + 待实跑清单）

> 开源方案大表见讲义附录 F.1。本节写 **ali-k8s-lab 实操路径**。\
> **说明（2026-08-21）**：lab 上无 Node.js，故不装 `runbook-agent`；采用课堂薄脚本
> `aiops_agent.py` + 智谱 **GLM**（OpenAI 兼容）。**API Key 只放环境变量，禁止写入本仓库/本文。**\
> 若你在对话中贴过 Key，请尽快在智谱控制台**轮换**。

### 12.1 方法论

```text
chaos 注入 → Metrics 恶化 → Alertmanager firing → webhook JSONL
  → AIOps observe → LLM(GLM) 摘要/根因/Runbook/推荐动作
  → 人工确认 → rollback_chaos 或 kubectl scale → 再 observe 验证
```

| 动作             | 含义         | 命令级落点                                   |
| ---------------- | ------------ | -------------------------------------------- |
| `rollback_chaos` | 应用故障回滚 | `POST :8088/chaos/error-rate?rate=0.02`      |
| `scale_out`      | 演示扩容     | `kubectl scale deploy/sre-load --replicas=N` |
| `scale_in`       | 缩回         | `--replicas=1`                               |

### 12.2 前置

```bash
ssh ali-k8s-lab
cd /root/sre-golden-signals
docker compose ps
python3 -m venv /root/sre-aiops-venv   # 需 apt install python3.12-venv
/root/sre-aiops-venv/bin/pip install -r requirements-aiops.txt
export GLM_API_KEY='<your-key>'          # 勿写入 git；智谱 OpenAI 兼容
export GLM_BASE_URL='https://open.bigmodel.cn/api/paas/v4/'
export GLM_MODEL='glm-4-flash'
export SRE_AIOPS_ALERTS_JSONL=/tmp/sre-aiops-alerts.jsonl
# pause 镜像若拉不动 registry.k8s.io，用阿里云：
# registry.aliyuncs.com/google_containers/pause:3.9
kubectl apply -f k8s/sre-load-deploy.yaml
kubectl get deploy sre-load
```

### 12.3 闭环 1：建议 + 回滚（已实跑 2026-08-21）

```bash
PYTHONUNBUFFERED=1 /root/sre-aiops-venv/bin/python -u webhook_receiver.py &
python3 loadgen.py --base http://127.0.0.1:8088 --qps 15 --seconds 400 &
curl -s -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.3'
# 约 40s 后 HighErrorRate -> firing
/root/sre-aiops-venv/bin/python aiops_agent.py --mode advise
/root/sre-aiops-venv/bin/python aiops_agent.py --mode execute --auto-execute
```

**实测 OBSERVE（摘要）**：`HighErrorRate` firing，`error_rate≈0.308`，`qps≈8.73`，`cpu_pct≈5.1`。

**实测 ADVICE（GLM `glm-4-flash`，engine=llm）**：

```json
{
  "summary": "API 错误率超过 5%，当前错误率=30.79%，QPS 为 8.7333，CPU 使用率 5.1012%。",
  "root_cause_hypothesis": "应用故障",
  "runbook": [
    "检查 API 代码逻辑",
    "检查数据库连接和查询效率",
    "检查缓存配置和命中率",
    "重启服务查看是否解决",
    "联系开发团队进行代码审查"
  ],
  "recommended_action": "rollback_chaos",
  "scale_replicas": 3,
  "confidence": 0.95,
  "engine": "llm"
}
```

**实测 EXECUTE**：

```json
{
  "action": "rollback_chaos",
  "result": {
    "/chaos/error-rate": { "error_rate": 0.02 },
    "/chaos/latency-ms": { "extra_latency_ms": 0.0 }
  }
}
```

Webhook JSONL：`/tmp/sre-aiops-alerts.jsonl` 实测含 `HighErrorRate` **firing** 与随后
**resolved**，以及 `HighRequestRate` firing（负载演示阈值）。

### 12.4 闭环 2：自动扩容 / 缩容（已实跑）

```bash
# 强制扩容演示（与当前 LLM 建议解耦时可用 --force-action）
/root/sre-aiops-venv/bin/python aiops_agent.py --mode execute --auto-execute --force-action scale_out --deploy sre-load
kubectl get deploy,pods -l app=sre-load -o wide
/root/sre-aiops-venv/bin/python aiops_agent.py --mode execute --auto-execute --force-action scale_in --deploy sre-load
```

**实测**：`sre-load` Ready 副本 **1 → 3（全部 Running）→ 1**。

| 阶段   | Deployment | Pods      |
| ------ | ---------- | --------- |
| 扩容前 | 1/1        | 1 Running |
| 扩容后 | 3/3        | 3 Running |
| 缩容后 | 1/1        | 1 Running |

### 12.5 实跑结果汇总

| 步骤                         | 状态 | 摘要                                                 |
| ---------------------------- | ---- | ---------------------------------------------------- |
| Compose + AM + webhook       | 通过 | Demo C 链路可用                                      |
| chaos → HighErrorRate firing | 通过 | error_rate≈31%，约 40s 进入 firing                   |
| GLM advise                   | 通过 | `recommended_action=rollback_chaos`，confidence 0.95 |
| execute rollback_chaos       | 通过 | error_rate 恢复 0.02                                 |
| kubectl scale 1→3→1          | 通过 | `sre-load` + Aliyun pause 镜像                       |
| runbook-agent                | 未装 | lab 无 Node；讲义 F.1 作 Reference                   |

**踩坑**：`pkill -f loadgen` 可能误杀 SSH 会话；用 pid 文件结束进程。`registry.k8s.io/pause`
超时，改用 `registry.aliyuncs.com/google_containers/pause:3.9`。Ubuntu 24.04 需
`python3.12-venv`。GLM 需 `response_format=json_object` 并收紧 system prompt，否则易复述模板占位符。
