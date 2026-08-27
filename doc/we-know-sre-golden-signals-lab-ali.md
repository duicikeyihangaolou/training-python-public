# SRE 黄金指标 — lab 实录（ali-k8s-lab / k8s-lab）

配套讲义：[`we-know-sre-golden-signals.md`](./we-know-sre-golden-signals.md)\
配套代码：[`../demo/sre-golden-signals/`](../demo/sre-golden-signals/)

> **与讲义的关系**：讲义按 **12 课**编排课堂实验；本文是 lab 机器上的 **实录**（KubeClipper + K8s +
> Compose 同机、命令、实测数据、踩坑）。**上课只需 Compose 即可**，不必照抄 §0–§4
> 环境准备。架构图见讲义 「文档与 Demo 如何串联」。

| Lab           | SSH 别名      | 公网 IP         | 内网 IP          | 区域     | 实录日期   |
| ------------- | ------------- | --------------- | ---------------- | -------- | ---------- |
| ali-k8s-lab   | `ali-k8s-lab` | `8.130.175.43`  | `172.25.209.127` | 大陆 ECS | 2026-08-27 |
| k8s-lab（HK） | `k8s-lab`     | `47.83.175.124` | `172.31.246.190` | 香港 ECS | 2026-08-27 |

下文命令中 **`$NODE` = 该机器 eth0 内网 IP**；rsync / ssh 别名按上表替换。

**目标**：在 lab 上验证讲义 **第 6–12 课**实验链路；§0–§4 为 **本机环境准备**（可选）。

### 讲义 12 课 ↔ 本实录章节

| 讲义课次   | 实验要点                             | 本实录章节                                                                                                                 | 实录           |
| ---------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **1–5**    | 理论 / 口述 / 埋点对照               | —                                                                                                                          | 无（课堂完成） |
| **6**      | 拉栈、Targets UP                     | [§5](#5-拉起-compose-栈讲义--第-6-课--demo-a-1)、[§5.1](#51-web-页面演示指南demo-看什么)、[§6.1](#61-targets讲义--第-6-课) | 有             |
| **7**      | `rules.yml` 四条规则                 | [§7](#7-告警规则-rulesyml讲义--第-7-课)                                                                                    | 有             |
| **8**      | `loadgen` + 四信号 PromQL            | [§6.2](#62-promql-四信号讲义--第-8-课)                                                                                     | 有             |
| **9**      | Grafana 四面板                       | [§8](#8-demo-b--grafana-看板讲义--第-9-课)                                                                                 | 有             |
| **10**     | 手工加面板（可选）                   | —                                                                                                                          | 未实录         |
| **11**     | chaos + webhook 闭环                 | [§9](#9-demo-c--故障注入与告警闭环讲义--第-11-课)                                                                          | 有             |
| **12**     | `aiops_agent`（默认 `--rules-only`） | [§13](#13-aiops-端到端讲义--第-12-课)                                                                                      | 有             |
| **附录 G** | Demo D 思维演练                      | —                                                                                                                          | 未实录         |
| **环境**   | KC + K8s + Docker 共存               | [§0–§4](#0-基线探测)                                                                                                       | 仅 lab 读者    |

**谁该读哪段**：

| 读者             | 阅读范围                                                                                                          |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| 本机 / WSL 上课  | 讲义正文 + Demo；踩坑见讲义 [附录 H](./we-know-sre-golden-signals.md#h-lab-ali-实录ali-k8s) / lab §9              |
| ali-k8s-lab 备课 | 全文；课堂实验从 §5 起                                                                                            |
| k8s-lab（香港）  | 全文；§1 用**默认**下载源（勿 `KC_REGION=cn`）；其余与 ali-k8s-lab 相同，见 [§14](#14-k8s-lab香港实录-2026-08-27) |

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
# 大陆 ECS（ali-k8s-lab）：国内源
curl -sfLk https://oss.kubeclipper.io/get-kubeclipper.sh | KC_REGION=cn bash -

# 香港 / 海外 ECS（k8s-lab）：默认源，勿设 KC_REGION=cn
curl -sfLk https://oss.kubeclipper.io/get-kubeclipper.sh | bash -

kcctl version
```

### 实测结果

- 脚本提示：`The v1.6.0 version will be installed`
- 包地址：`https://kubeclipper.oss-ap-southeast-1.aliyuncs.com/kc/v1.6.0/kc-linux-amd64.tar.gz`（约
  61MB；ali-k8s-lab 约 2 分钟；k8s-lab 约 **9 秒**）
- 安装路径：`/usr/local/bin/kcctl`
- 版本输出（摘要）：

```text
kcctl version: ... GitVersion:"v1.6.0-3+87d297f125e91b" ... Platform:"linux/amd64"
```

大陆机器会生成 `/etc/kc/kc.env`（`KC_REGION=cn`）；香港机器无此文件亦可。

---

## 2. 部署 KubeClipper 平台（AIO）

```bash
# All-In-One：本机既做 server 也做 agent；etcd 自动错开端口（12379/12380/12381）
kcctl deploy
```

> **`kcctl deploy` 会再下载 ~1.27GB 的 `kc-amd64.tar.gz`**（与 §1 的 61MB kcctl CLI 不是同一个包）。
> `KC_REGION=cn` **只加速后续 K8s 组件镜像**，不加速此包。大陆 ECS 跨区拉 `oss-ap-southeast-1`
> 时，默认 `wget` 单线程可能只有 ~200KB/s（需 1–2 小时）。**推荐 aria2 多线程 +
> 本地包部署**（2026-08-27 ali-k8s-lab 实测 ~5.3MiB/s，约 3–4 分钟）：
>
> ```bash
> apt-get install -y aria2
> aria2c -x16 -s16 -c -k1M --file-allocation=none -d /tmp/kc -o kc-amd64.tar.gz \
>   "https://kubeclipper.oss-ap-southeast-1.aliyuncs.com/release/v1.6.0/kc-amd64.tar.gz"
> kcctl deploy --pkg /tmp/kc/kc-amd64.tar.gz
> ```
>
> 香港 ECS 直连默认源往往更快（k8s-lab 约 **4 分钟**整包 `deploy`），可不 aria2。

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
NODE=$(ip -4 -br a show eth0 | awk '{print $3}' | cut -d/ -f1)   # 或手写内网 IP
kcctl create cluster --name sre-aio --master "$NODE" --untaint-master
# ali-k8s-lab: NODE=172.25.209.127  |  k8s-lab: NODE=172.31.246.190
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
# 裸机首次需加 Docker 官方源（已装可跳过）
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -qq
# containerd.io 会提示是否覆盖 /etc/containerd/config.toml — 必须保留 K8s 配置
apt-get -y -o Dpkg::Options::="--force-confold" install \
  docker-ce docker-ce-cli containerd.io docker-compose-plugin
# 首次若卡在 conffile 交互导致失败，用 force-confold 收尾：
# apt-get -y -o Dpkg::Options::="--force-confold" install -f
systemctl enable --now docker
systemctl restart containerd   # 确认 kubelet 侧 containerd 仍正常
kubectl get nodes              # 仍应为 Ready
docker --version
docker compose version
```

### 实测版本

- Docker **29.7.2**（docker-ce）或 **29.1.3**（`docker.io` 备选，见下）
- Docker Compose **v5.5.0** / **v2.40.3**（`docker-compose-v2`）
- 安装后 `kubectl get nodes` 仍为 **Ready**

**docker-ce 装不上时**（`download.docker.com` GPG/连接失败，2026-08-27 ali-k8s-lab 踩坑）：

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get -y -o Dpkg::Options::="--force-confold" install docker.io docker-compose-v2 python3.12-venv
systemctl enable --now docker && systemctl restart containerd
kubectl get nodes   # 仍应为 Ready
```

**Compose 拉镜像**：Docker Hub 超时时，配置 `registry-mirrors` 并/或经 DaoCloud 预拉后
`docker tag`：

```bash
cat > /etc/docker/daemon.json <<'EOF'
{ "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"] }
EOF
systemctl restart docker
docker pull docker.m.daocloud.io/grafana/grafana:11.2.0 && docker tag docker.m.daocloud.io/grafana/grafana:11.2.0 grafana/grafana:11.2.0
docker pull docker.m.daocloud.io/library/python:3.12-slim && docker tag docker.m.daocloud.io/library/python:3.12-slim python:3.12-slim
```

API 镜像构建时 `pip` 也可能超时，可在 `api/Dockerfile` 的 `pip install` 加
`-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`。

### 4.2 Demo 配置纠正（已合入仓库）

相对最初讲义，在 Linux + KubeClipper 同机上必须改：

| 问题                            | 纠正                                                              |
| ------------------------------- | ----------------------------------------------------------------- |
| KC `:8080` vs Demo API `:8080`  | Compose 改为 `"8088:8080"`                                        |
| Linux 无 `host.docker.internal` | `alertmanager.extra_hosts: ["host.docker.internal:host-gateway"]` |
| `nohup` 下 webhook 日志缓冲     | `python3 -u` + `print(..., flush=True)`                           |

本地修正后同步：

```bash
# 在开发机（LAB 别名按 § 开头表格替换）
rsync -az --exclude '__pycache__' \
  demo/sre-golden-signals/ ali-k8s-lab:/root/sre-golden-signals/
# 或：demo/sre-golden-signals/ k8s-lab:/root/sre-golden-signals/
```

---

## 5. 拉起 Compose 栈（讲义 · 第 6 课 · Demo A-1）

```bash
ssh ali-k8s-lab
cd /root/sre-golden-signals
docker compose up -d --build
docker compose ps
curl -s http://127.0.0.1:8088/health
curl -s http://127.0.0.1:9090/-/ready
curl -s http://127.0.0.1:3000/api/health   # Grafana 刚起可能需等 5–10s
```

### 实测结果

全部容器 `Up`；健康检查（Grafana 就绪后）：

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

### 5.1 Web 页面演示指南（Demo 看什么）

栈拉起后即可用浏览器演示。**本机**用 `localhost`；**远程 lab** 将下表 `localhost` 换为公网
IP（见文首 表格），或 SSH 隧道：

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 k8s-lab
# 浏览器仍访问 http://localhost:3000 等
```

#### 页面总览

| 页面                   | URL                                             | 账号                      | 对应 Demo                 | 浏览器      |
| ---------------------- | ----------------------------------------------- | ------------------------- | ------------------------- | ----------- |
| **Grafana 看板**       | `:3000/d/sre-golden-signals/sre-golden-signals` | admin / admin             | Demo B（第 9 课）         | ✅ 主看板   |
| **Prometheus**         | `:9090`                                         | —                         | Demo A/C（第 6–8、11 课） | ✅          |
| **Alertmanager**       | `:9093`                                         | —                         | Demo C（第 11 课）        | ✅          |
| **Demo API**           | `:8088/health`、`/metrics`                      | —                         | 健康检查 / chaos          | ⚠️ 仅 JSON   |
| **Node Exporter**      | `:9100/metrics`                                 | —                         | Saturation 数据源         | ⚠️ 原始文本  |
| **KubeClipper 控制台** | `:80`                                           | admin / Thinkbig1（常见） | 环境准备                  | ✅ 可选     |
| **Webhook 接收器**     | `:9999`                                         | —                         | Demo C / AIOps            | ❌ 终端输出 |

> Demo API 映射 **8088** 是为避开 KubeClipper API **8080**。

#### Demo A — Prometheus（第 6–8 课）

**配合终端**：`python3 loadgen.py --base http://127.0.0.1:8088 --qps 10 --seconds 240`

| 页面        | URL             | 重点                                                                                                |
| ----------- | --------------- | --------------------------------------------------------------------------------------------------- |
| **Targets** | `:9090/targets` | `api` / `node` / `prometheus` 必须全 **UP**；任一下线则后续 PromQL、告警无效                        |
| **Graph**   | `:9090/graph`   | 打流后用 PromQL 实算四信号：Traffic（QPS）、Errors（5xx 占比）、Latency（P95）、Saturation（CPU %） |
| **Rules**   | `:9090/rules`   | 四条 alert 规则；打流/注入后看 `inactive` → `pending` → `firing`                                    |

**课堂要点**：Prometheus 是「算出来的」；Graph 曲线随 loadgen 动起来，说明 metrics → 查询链路 OK。

#### Demo B — Grafana（第 9 课）

**URL**：`:3000/d/sre-golden-signals/sre-golden-signals`

**配合终端**：`loadgen --qps 10 --seconds 300`

| 面板                        | 重点                                          |
| --------------------------- | --------------------------------------------- |
| **Traffic — QPS by method** | GET/POST 随 loadgen 上升（**T**）             |
| **Errors — Error Rate**     | 红色告警线 **5%**；chaos 注入后应越过         |
| **Latency — P50/P95/P99**   | P95 常用作 SLO；`latency-ms=800` 注入后应抬升 |
| **Saturation — Host CPU %** | 基础设施饱和度；本 demo 通常 10–30%           |

**课堂要点**：Grafana 给值班/业务看「一屏四信号」；Prometheus Graph 给 SRE 查数——同一套
metrics，两种视角。

#### Demo C — 告警闭环（第 11 课）

**三终端 + 两 Web 页**：

```bash
# T1：webhook（看终端 JSON，非网页）
PYTHONUNBUFFERED=1 python3 -u webhook_receiver.py
# T2：打流
python3 loadgen.py --base http://127.0.0.1:8088 --qps 12 --seconds 300
# T3：注入
curl -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.2'
```

| 页面                  | URL            | 重点                                                                                                              |
| --------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Prometheus Alerts** | `:9090/alerts` | 打流 ~30s → `HighRequestRate` firing；注入 error-rate ~40s → `HighErrorRate` **critical** firing；回滚后 inactive |
| **Alertmanager**      | `:9093`        | firing 告警分组；critical → `critical-webhook`，warning → `default-webhook`                                       |
| **Webhook 终端**      | —              | 看 `status: firing` / `resolved`，`alertname`、`description`                                                      |

**完整链路**：chaos 注入 → metrics 恶化 → Prometheus rules → Alertmanager 路由 → webhook JSON。\
Grafana 看**现象**，Prometheus Alerts 看**规则触发**，Alertmanager 看**分发**，webhook
看**下游收到什么**。

**可选**：`curl -X POST ':8088/chaos/latency-ms?ms=800'` → Grafana Latency 面板 + `HighLatencyP95`
规则。

#### Demo E / AIOps（第 12 课）

以**终端**为主（`aiops_agent.py`）；可辅助打开 `:9090/alerts`（execute 前后告警是否 resolved）与
Grafana Errors 面板（回滚后是否回落）。K8s 扩容用 `kubectl get pods -l app=sre-load`，无 Web UI。

#### 推荐 Tab 布局

```
Tab 1: Grafana 看板（全程）
Tab 2: Prometheus /alerts（Demo C 重点）
Tab 3: Alertmanager（Demo C）
终端: loadgen + webhook + curl chaos
```

**30 秒口述**：Targets 全 UP → Grafana 四面板随打流动 → chaos 注入 → Prometheus Alerts firing →
Alertmanager active → webhook JSON → 回滚 resolved。

---

## 6. Demo A — 采集与 PromQL

> 讲义拆为两课：**§6.1** =
> [第 6 课](./we-know-sre-golden-signals.md#第-6-课-采集分析与-demo-a-拉栈)（Targets）；\
> **§6.2** = [第 8 课](./we-know-sre-golden-signals.md#第-8-课-demo-a-promql-四信号实算)（PromQL +
> loadgen）。\
> [第 3–4 课](./we-know-sre-golden-signals.md#第-3-课-latency-与-traffic)可在 §6.1 无打流时用 Graph
> 试基线。

### 6.1 Targets（讲义 · 第 6 课）

```bash
curl -s http://127.0.0.1:9090/api/v1/targets | python3 -c '
import sys,json
for t in json.load(sys.stdin)["data"]["activeTargets"]:
    print(t["labels"].get("job"), t["health"], t["labels"].get("instance"))
'
```

### 实测 Targets

```text
api up api:8080
node up node-exporter:9100
prometheus up localhost:9090
```

### 6.2 PromQL 四信号（讲义 · 第 8 课）

```bash
# 打流
python3 loadgen.py --base http://127.0.0.1:8088 --qps 10 --seconds 240
```

### 实测 PromQL（打流约 45s 后）

| 信号           | 查询摘要                                                       | 结果量级                    |
| -------------- | -------------------------------------------------------------- | --------------------------- |
| Traffic        | `sum by (method) (rate(http_requests_total{job="api"}[1m]))`   | GET ≈ 3.27/s，POST ≈ 1.51/s |
| Errors         | 5xx / 全量                                                     | ≈ **1.1%**（默认注入 2%）   |
| Latency P95    | `histogram_quantile(0.95, ...)`                                | ≈ **0.145 s**               |
| Saturation CPU | `100 - avg(rate(node_cpu_seconds_total{mode="idle"}[2m]))*100` | ≈ **31%**                   |

---

## 7. 告警规则 rules.yml（讲义 · 第 7 课）

对照讲义 [第 7 课](./we-know-sre-golden-signals.md#第-7-课-告警策略) 打开
`prometheus/rules.yml`，四条规则与 L/T/E/S 映射如下：

| 规则              | 信号       | severity     | `for` | 课堂触发方式                           |
| ----------------- | ---------- | ------------ | ----- | -------------------------------------- |
| `HighRequestRate` | Traffic    | warning      | 30s   | `loadgen` QPS>5（见 §6.2 / §9）        |
| `HighErrorRate`   | Errors     | **critical** | 30s   | `chaos/error-rate≥0.2`（见 §9）        |
| `HighCPUUsage`    | Saturation | warning      | 1m    | 主机 CPU 持续高位（本 lab 通常未触发） |
| `HighLatencyP95`  | Latency    | warning      | 1m    | `chaos/latency-ms=800`（可选，见 §9）  |

```bash
cd /root/sre-golden-signals
grep -E 'alert:|severity:' prometheus/rules.yml
curl -s http://127.0.0.1:9090/api/v1/rules | python3 -c '
import sys,json
for g in json.load(sys.stdin)["data"]["groups"]:
    for r in g.get("rules",[]):
        if r.get("type")=="alerting":
            print(r["name"], r.get("labels",{}).get("severity"))
'
```

**验收**：四条 alert 名与 severity 与上表一致；打流后可在 Prometheus → Rules 看到 `HighRequestRate`
评估中。

---

## 8. Demo B — Grafana 看板（讲义 · 第 9 课）

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

## 9. Demo C — 故障注入与告警闭环（讲义 · 第 11 课）

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

## 10. 可复现命令序列（精简）

```bash
# --- 一次性：KC + K8s ---
# 大陆：KC_REGION=cn bash -  |  香港/海外：bash -（勿 cn）
curl -sfLk https://oss.kubeclipper.io/get-kubeclipper.sh | bash -
# deploy 慢时：aria2 下 kc-amd64.tar.gz 后 kcctl deploy --pkg /tmp/kc/kc-amd64.tar.gz（见 §2）
kcctl deploy
NODE=$(ip -4 -br a show eth0 | awk '{print $3}' | cut -d/ -f1)
kcctl create cluster --name sre-aio --master "$NODE" --untaint-master
# 轮询：kcctl get cluster 直到 Running；kubectl get nodes 为 Ready（约 2–4 分钟）

# --- Docker（保留 K8s containerd 配置）---
# ... 按 §4.1 force-confold 安装 docker-ce ...

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

## 11. 资源占用（Demo 跑完后抽样）

| 项   | 约值                                        |
| ---- | ------------------------------------------- |
| 内存 | 已用 ~2.1 GiB / 14 GiB（available ~12 GiB） |
| 根盘 | ~12G 已用 / 99G（含 KC 包、镜像、TSDB）     |

K8s + Compose 同机可并存；课上勿再装 Istio / kube-prometheus 全栈，除非升到更高规格。

---

## 12. 结论

1. **KubeClipper v1.6.0** AIO 平台 + **K8s v1.36.1** 单节点（`--untaint-master`）在本 ECS 上可顺利
   Running。
2. 讲义 Demo **无需迁入 K8s**；Compose 在同机走通采集 → Grafana → 告警 webhook。
3. 同机必改：**API 8088**、**host-gateway**、**webhook 无缓冲启动**。
4. 安装 Docker 时 **切勿覆盖** K8s 的 `/etc/containerd/config.toml`。

---

## 13. AIOps 端到端（讲义 · 第 12 课）

> 开源方案大表见讲义
> [附录 F.1](./we-know-sre-golden-signals.md#f1-开源-aiops-方案-reference对比表)。\
> **课堂默认**（与讲义
> [第 12 课](./we-know-sre-golden-signals.md#第-12-课-简易-aiops-与-ai-场景扩展)
> 一致）：**`--rules-only`**，无需 API Key。\
> 本节 **§13.3** 为 lab 上已跑的 **GLM 进阶**；**§13.4** 为 K8s `sre-load` 扩容进阶。

### 13.1 方法论

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

### 13.2 课堂路径：`--rules-only`（与讲义默认一致）

**前置**：§9 Demo C 已 `HighErrorRate` firing，或重新注入：

```bash
curl -s -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.25'
# 约 30–40s 后 firing
```

```bash
cd /root/sre-golden-signals
python3 aiops_agent.py --mode advise --rules-only
python3 aiops_agent.py --mode execute --confirm --rules-only
# 输入 yes → chaos 回 0.02
```

**验收**：`recommended_action` 为 `rollback_chaos`；execute 后 §9 告警应 Resolved。

### 13.3 GLM 进阶（可选，已实跑 2026-08-21）

lab 无 Node.js，未装 `runbook-agent`；采用 `aiops_agent.py` + 智谱 **GLM**（OpenAI 兼容）。\
**API Key 只放环境变量，禁止写入本仓库/本文。** 若曾贴过 Key，请在智谱控制台**轮换**。

#### 前置

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
kubectl wait --for=condition=available deploy/sre-load --timeout=120s
kubectl get deploy,pods -l app=sre-load
```

> **说明**：`aiops_agent.py` 无独立 `--mode observe`；`advise` / `execute` 会先打印
> `=== OBSERVE ===` 再输出 `=== ADVICE ===` / `=== EXECUTE ===`。

#### 闭环：建议 + 回滚（GLM）

```bash
PYTHONUNBUFFERED=1 /root/sre-aiops-venv/bin/python -u webhook_receiver.py &
python3 loadgen.py --base http://127.0.0.1:8088 --qps 15 --seconds 400 &
curl -s -X POST 'http://127.0.0.1:8088/chaos/error-rate?rate=0.3'
# 约 40s 后 HighErrorRate -> firing
/root/sre-aiops-venv/bin/python aiops_agent.py --mode advise
/root/sre-aiops-venv/bin/python aiops_agent.py --mode execute --auto-execute
```

**实测 OBSERVE（摘要，ali-k8s-lab）**：`HighErrorRate`
firing，`error_rate≈0.308`，`qps≈8.73`，`cpu_pct≈5.1`。

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

### 13.4 K8s 扩容 / 缩容进阶（可选，已实跑）

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

### 13.5 实跑结果汇总

| 步骤                          | 状态 | 摘要                                                 |
| ----------------------------- | ---- | ---------------------------------------------------- |
| Compose + AM + webhook        | 通过 | Demo C 链路可用                                      |
| chaos → HighErrorRate firing  | 通过 | error_rate≈31%，约 40s 进入 firing                   |
| GLM advise                    | 通过 | `recommended_action=rollback_chaos`，confidence 0.95 |
| execute rollback_chaos        | 通过 | error_rate 恢复 0.02                                 |
| kubectl scale 1→3→1           | 通过 | `sre-load` + Aliyun pause 镜像                       |
| `--rules-only` advise/execute | 通过 | 与讲义第 12 课默认路径一致                           |
| runbook-agent                 | 未装 | lab 无 Node；讲义 F.1 作 Reference                   |

**踩坑**：`pkill -f loadgen` 可能误杀 SSH 会话；用 pid 文件或 `fuser -k 9999/tcp` 结束 webhook。
`registry.k8s.io/pause` 超时，改用 `registry.aliyuncs.com/google_containers/pause:3.9`。Ubuntu 24.04
需 `python3.12-venv`。GLM 需 `response_format=json_object` 并收紧 system
prompt，否则易复述模板占位符。

---

## 14. 2026-08-27 复跑实录（ali-k8s-lab + k8s-lab）

### 14.0 ali-k8s-lab 复跑（公网 IP 换为 `8.130.175.43`）

在 **ali-k8s-lab** 从零重装 KC + K8s + Compose + AIOps，全链路通过。与 2026-08-21 相比的补充：

| 项             | 2026-08-27 实测                                                               |
| -------------- | ----------------------------------------------------------------------------- |
| `kcctl deploy` | aria2 多线程下 1.27GB 包约 **3–4 分钟**；`deploy --pkg` 装平台约 **1 分钟**   |
| K8s `sre-aio`  | `Installing` → `Running` 约 **3 分钟**；**v1.36.1** Ready                     |
| Docker         | `docker-ce` GPG 失败 → 改 `docker.io` + `docker-compose-v2`；节点仍 Ready     |
| Compose        | Hub 超时 → DaoCloud 预拉 grafana/python；pip 用阿里云镜像                     |
| Demo A/B/C     | Targets 全 up；Grafana `sre-golden-signals`；`HighErrorRate` pending → firing |
| AIOps GLM      | `rollback_chaos` + `scale_out` 1→3→1 均通过                                   |

### 14.1 k8s-lab（香港）

在 **k8s-lab**（`ssh k8s-lab`，内网 `172.31.246.190`）按本文 §0–§13 完整复跑，与 ali-k8s-lab
结论一致。差异与补充实测如下。

### 14.2 环境准备差异（k8s-lab）

| 项             | k8s-lab 实测                                                          |
| -------------- | --------------------------------------------------------------------- |
| kcctl 安装     | **无** `KC_REGION=cn`；61MB 包约 **9s** 下完                          |
| `kcctl deploy` | 约 **4 分钟**                                                         |
| K8s 就绪       | `Installing` → `Running` 约 **3 分钟**；节点 hostname **`k8s-lab`**   |
| Docker         | **29.7.2** + Compose **v5.5.0**；`force-confold` 保留 containerd 配置 |
| 节点仍 Ready   | 是                                                                    |

### 14.3 Demo A/B/C（k8s-lab）

| 步骤        | 结果                                                                |
| ----------- | ------------------------------------------------------------------- |
| Targets     | api / node / prometheus 均 **up**                                   |
| PromQL 打流 | GET ≈ **3.20/s**，POST ≈ **1.28/s**                                 |
| Grafana     | 文件夹 SRE；看板 uid `sre-golden-signals`；Prometheus 默认数据源 OK |
| Demo C      | `HighErrorRate` pending → **firing**（≈19–30%）；webhook 收到 JSON  |

### 14.4 AIOps GLM（k8s-lab）

**OBSERVE**：`error_rate≈0.297`，`qps≈16.93`，`cpu_pct≈7.8`，`HighErrorRate` + `HighRequestRate`
firing。

**ADVICE**（`glm-4-flash`，engine=llm）：`recommended_action=rollback_chaos`，`confidence=0.9`。

**EXECUTE**：`rollback_chaos` 成功，`error_rate` 恢复 **0.02**。

**scale_out / scale_in**：`sre-load` **1 → 3（全 Running）→ 1**。

### 14.5 资源占用（k8s-lab 跑完后）

| 项   | 约值                                        |
| ---- | ------------------------------------------- |
| 内存 | 已用 ~2.2 GiB / 14 GiB（available ~12 GiB） |
| 根盘 | ~13G 已用 / 99G                             |

**结论**：香港 ECS 走默认 KubeClipper 下载源即可；讲义 Demo A/B/C + AIOps 全链路在 k8s-lab 通过。
