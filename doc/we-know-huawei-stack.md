## 华为云 Stack 开发侧工程实践讲义

## 注意 ⚠️

- _斜体表示引用或延伸阅读_
- **未经允许，禁止转载**
- 本讲义**不重复**华为云 Stack / K8S(CCE) / ServiceStage / OBS 产品概念课；默认学员已具备平台认知

参考：

1. [容器知识扩展阅读](https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/master/doc/kubernetes-best-practices.md?#22-containerd)
2. [K8S 扩展阅读](https://gitee.com/dev-99cloud/training-kubernetes/blob/master/doc/class-01-Kubernetes-Administration.md?#29-%E5%90%AF%E5%8A%A8%E4%B8%80%E4%B8%AA-pod)
3. [华为云 SWR 容器镜像服务](https://support.huaweicloud.com/productdesc-swr/swr_03_0001.html)，[容器镜像服务控制台](https://console.huaweicloud.com/swr/?region=cn-east-3#/swr/dashboard)
4. [华为云开发者 Python 软件开发工具包（Python SDK）](https://github.com/huaweicloud/huaweicloud-sdk-python-v3/blob/master/README_CN.md)

---

## 课程目录

| 场次   | 时间  | 主题                       | 章节                                                                     |
| ------ | ----- | -------------------------- | ------------------------------------------------------------------------ |
| 预备   | —     | 无 Stack 环境自学边界      | [0.1 自学目标与边界](#01-无-stack-环境自学目标与边界)                    |
| 第一晚 | 2 h   | 镜像构建与容器化研发约定   | [1.1 课程边界与 Stack 研发视角](#11-课程边界与-stack-研发视角)           |
|        |       |                            | [1.2 镜像与 Dockerfile：从源码到制品](#12-镜像与-dockerfile从源码到制品) |
|        |       |                            | [1.3 工程化构建习惯与安全](#13-工程化构建习惯与安全)                     |
|        |       |                            | [1.4 运行契约：健康检查、配置与日志](#14-运行契约健康检查配置与日志)     |
|        |       |                            | [1.5 制品入仓 SWR 与本地验证闭环](#15-制品入仓-swr-与本地验证闭环)       |
|        |       |                            | [1.6 第一晚小结与预习](#16-第一晚小结与预习)                             |
| 第二晚 | 2 h   | OBS 工程化接入与发布侧要点 | [2.1 发布与配置：研发侧交付清单](#21-发布与配置研发侧交付清单)           |
|        |       |                            | [2.2 OBS 代码层接入](#22-obs-代码层接入)                                 |
|        |       |                            | [2.3 OBS 工程化最佳实践](#23-obs-工程化最佳实践)                         |
|        |       |                            | [2.4 分布式主题：研发视角极简串联](#24-分布式主题研发视角极简串联)       |
|        |       |                            | [2.5 端到端价值流与 AI 辅助开发](#25-端到端价值流与-ai-辅助开发)         |
|        |       |                            | [2.6 第二晚小结与扩展阅读索引](#26-第二晚小结与扩展阅读索引)             |
| 自学   | 4–6 h | 无 Stack 环境跟练（可选）  | [第三部分：自学实验跟练手册](#第三部分无-stack-环境--自学实验跟练手册)   |

---

## 0. 先建立一张「地图」

在进两晚细节之前，先对齐**开发者在 Stack 里的位置**：

```text
开发者本机                华为云 Stack（泸州银行机房）
┌─────────────┐          ┌──────────────────────────────────────┐
│ Dockerfile  │ build    │  SWR（镜像仓库）                      │
│ docker CLI  │ ───────► │    ↓                                  │
│ git / CI    │ push     │  CCE / ServiceStage（运行平台）        │
│ Python/Java │          │    ↓                                  │
└─────────────┘          │  OBS（对象存储）←── 应用 SDK 访问       │
                         └──────────────────────────────────────┘
```

| 名词                    | What                                             | 与开发的关系                                             |
| ----------------------- | ------------------------------------------------ | -------------------------------------------------------- |
| **华为云 Stack（HCS）** | 部署在客户数据中心的私有云，API/产品与公有云同族 | endpoint、项目 ID 为**行内地址**，非 `myhuaweicloud.com` |
| **SWR**                 | 容器镜像仓库（OCI 镜像托管与分发）               | 研发 `docker push` 的**制品终点**                        |
| **CCE**                 | 托管 Kubernetes                                  | 运行容器；探针路径须与应用 `/health` `/ready` 对齐       |
| **ServiceStage**        | 应用托管与微服务治理（PaaS）                     | 消费 SWR 镜像；**本课不讲控制台逐步导览**                |
| **OBS**                 | 对象存储（S3 类 REST API）                       | 代码经 **SDK** 上传/下载/预签名                          |

**历史名称**（读老文档时会遇到）：FusionSphere OpenStack → FusionCloud → **Huawei Cloud Stack
(HCS)**。

### 0.1 无 Stack 环境：自学目标与边界

暂无泸州银行 **华为云 Stack** 内网权限时，可按 [第三部分](#第三部分无-stack-环境--自学实验跟练手册)
自行预习/备课/跟练。

| 依据类型                  | 含义                                                                            | 本课例子                                         |
| ------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| **与云厂商无关**          | 行业标准或通用运行时，换任何云都一样                                            | Docker、OCI 镜像、`/health` `/ready`             |
| **API 同族，换 endpoint** | Stack 与华为公有云 **同一套 REST API / SDK**，差异主要在 **域名、项目 ID、IAM** | SWR（`docker push`）、OBS（`esdk-obs-python`）   |
| **底座子集兼容**          | Stack **最下层 IaaS** 基于 OpenStack，DevStack 可练 Keystone/Nova 等 **子集**   | `openstack project list`（**可选**，非本课主线） |

**不是**「Stack 与 OpenStack 架构完全一样所以都能练」：本课主线 **SWR、OBS、ServiceStage 不在
OpenStack API 里**。

---

#### 逐项：能练什么、不能替代什么

**1. Dockerfile、本地构建、健康检查**

- **能练到**：本地 `docker build` / `docker run`，`/health`、`/ready` 与 CCE/K8s 探针路径对齐。
- **依据**：**与云平台无关**（OCI + Docker Engine 通用）。
- **不能替代**：Stack **内网 SWR registry 域名**、**行内 IAM 登录方式**（如 RAM 用户、VPN 后
  `docker login`）。
- **原因**：自学常用 `swr.<region>.myhuaweicloud.com` 与 `<region>@<AK>`；Stack 多为 **内网 FQDN +
  行内鉴权流程**，代码不变，**连线和登录步骤**要在现场重做一遍。

**2. 华为 SWR / OBS 的 API 与 SDK**

- **能练到**：`docker push`、OBS 上传/下载/预签名、`esdk-obs-python` 封装。
- **依据**：**API 同族**——Stack 与公有云共用 SWR/OBS API；自学时改 **endpoint / project_id / AK/SK**
  即可。
- **不能替代**：**ServiceStage** 控制台逐步发布、行内 **发布审批 / 配置界面**。
- **原因**：ServiceStage 是华为 **PaaS 托管层**，无完全等价的公有云自学沙箱；用 `docker run` 或自建
  K8s 只能练 **容器与探针**，**练不到** ServiceStage 的镜像落位、环境绑定与行内流程。

**3. 配置外置、tag 策略、日志规范**

- **能练到**：env 注入、`.gitignore` 密钥、tag 命名、stdout 日志。
- **依据**：**工程约定通用**（12-Factor），Stack / 公有云 / K8s 均适用。
- **不能替代**：**ManageOne** 服务发放、VDC/配额、工单式「申请资源再用云」。
- **原因**：ManageOne 是 Stack **云管平台**；DevStack/公网控制台 **没有同一套** 组织架构与发放
  UI。研发只需交付 **环境变量键名清单**；**不必**在自学环境复现 ManageOne。

**4. OpenStack IaaS 层概念（可选）**

- **能练到**：Keystone 鉴权、Project/租户、`openstack server list` 等 **IaaS 概念**。
- **依据**：Stack 底座 **部分兼容 OpenStack API**（Nova/Neutron/Keystone）。
- **不能替代**：Stack **全链路 E2E**——**SWR → ServiceStage/CCE → OBS** 在行内 **一次打通**（含内网
  endpoint）。
- **原因**：OpenStack 只是 Stack **最下一层**；DevStack **不提供** SWR、OBS、ServiceStage；单练 IaaS
  **凑不齐** 本课价值流。

---

**总结**：

- **能练的**：厂商无关的 Docker 约定，或华为 **API/SDK 同族**（换 endpoint），或可选的 OpenStack
  **IaaS 子集**。
- **不能替代的**：行内 **网络地址 + IAM + ManageOne 云管 + ServiceStage 托管**，以及上述能力
  **叠在一起的真实 Stack 现场**。

**原则**：本地 Docker 练「镜像与运行契约」；华为**公有云试用**练「SWR/OBS API 形态」；上 Stack
后只改 **endpoint / 区域 / 项目 ID**，代码结构尽量不动。分层对照见
[附录 B](#附录-bstack-vs-公有云-vs-openstack扩展)。

---

# 第一晚：镜像构建与容器化研发约定（2 小时）

[返回目录](#课程目录)

**今晚目标**：离开平台概念复述，建立「**可构建、可运行、可入仓**」的最小交付闭环。

| 时段      | 内容                          | 形式        |
| --------- | ----------------------------- | ----------- |
| 0:00–0:15 | 1.1 课程边界                  | 讲授        |
| 0:15–0:50 | 1.2–1.3 Dockerfile 与工程习惯 | 讲授 + Demo |
| 0:50–1:20 | 1.4 运行契约                  | 讲授 + Demo |
| 1:20–1:55 | 1.5 SWR 入仓                  | Demo 为主   |
| 1:55–2:00 | 1.6 小结                      | 收束        |

---

### 1.1 课程边界与 Stack 研发视角

[返回目录](#课程目录)

#### What：本课承诺交付什么？

「**最小可交付能力集**」——研发侧在容器化链路中必须负责的产物与约定：

1. **Dockerfile**（及 `.dockerignore`）——可审查、可复现的构建定义
2. **可运行镜像**——含启动入口、端口、非 root、配置外置
3. **探针契约**——`/health`（存活）、`/ready`（就绪）
4. **制品 tag 策略**——与版本/流水线对齐的命名
5. **SWR 推送**——认证、命名空间、权限要点（演示级）

#### Why

**不**讲什么？（同期平台课已覆盖）

- Stack 整体架构、VM vs 容器、ManageOne 导览
- ServiceStage 产品功能逐项演示
- OBS 桶/ACL/生命周期等产品概念体系
- 监控大盘、全链路追踪、DBA 级变更实施

#### Why：为什么要「解耦平台课」？

银行研发日常面对的是：**写 Dockerfile → CI 构建 → 推 SWR → 平台拉镜像部署**。\
平台课解决「云是什么」；本课解决「**我写的镜像/platform 能不能接住**」。

典型矛盾：

| 矛盾                       | 研发侧后果                   |
| -------------------------- | ---------------------------- |
| 镜像过大 / 构建慢          | 流水线超时、回滚慢           |
| 依赖装在不同层             | 本地能跑、CI 失败            |
| 密钥打进镜像               | 合规事故、层历史泄露         |
| 只有 `/health` 无 `/ready` | 滚动发布时流量打到未就绪实例 |
| tag 随意 `latest`          | 无法追溯、无法回滚           |

#### How：研发在组织中的责任边界

```text
研发负责                    平台/运维负责
─────────                   ─────────────
Dockerfile、应用代码         CCE/ServiceStage 集群
镜像 tag、API 契约           网络、存储类、配额
/health /ready 语义          探针配置引用路径（对接）
环境变量「键名」约定          密钥注入通道（K8s Secret 等）
日志格式（stdout）           采集、检索、告警
```

> **Reference**
>
> - [The Twelve-Factor App（配置、日志、进程）](https://12factor.net/) — 十二要素（★ =
>   与本课紧密相关）：
>   1. Codebase 一份代码库，多处部署
>   2. Dependencies 显式声明依赖
>   3. **Config** 配置外置（env），不进镜像/Git ★
>   4. **Backing services** DB/OBS/MQ 等当作可替换附加资源 ★
>   5. **Build, release, run** 构建、发布、运行严格分离 ★
>   6. **Processes** 无状态进程运行 ★
>   7. Port binding 端口绑定对外服务
>   8. Concurrency 进程模型水平扩展
>   9. **Disposability** 快速启动、优雅退出（SIGTERM、`/health`） ★
>   10. Dev/prod parity 开发/预发/生产环境尽量一致
>   11. **Logs** 日志写 stdout/stderr，作事件流 ★
>   12. Admin processes 迁移/批处理等用一次性进程
> - [华为云 Stack 解决方案描述](https://www.huaweicloud.com/solution/dedicated-cloud/forecloud-stack.html)
> - [Kubernetes Pod 生命周期与探针](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes)

---

### 1.2 镜像与 Dockerfile：从源码到制品

[返回目录](#课程目录)

#### What：镜像是什么？

- **What**：镜像 = 只读层叠文件系统 +
  元数据（入口命令、环境变量、端口声明等），运行时成为**容器**进程。
- **Why**：把「OS + 运行时 + 依赖 + 应用」打成**不可变制品**，消除「在我机器上能跑」环境漂移。
- **How**：用 **Dockerfile** 描述构建步骤；`docker build` 产生镜像；运行时 `docker run` / 平台从 SWR
  拉取同一 digest/tag。

镜像遵循 **OCI（Open Container Initiative）** 规范；Dockerfile 指令映射到一层层
**Layer**，每层有缓存 ID。

#### 核心指令：概念模型（非手册罗列）

| 指令                 | What               | Why                    | How（约定）                                         |
| -------------------- | ------------------ | ---------------------- | --------------------------------------------------- |
| `FROM`               | 基础镜像           | 决定 OS、glibc、CVE 面 | 优先 **slim / distroless**；固定 minor 版本         |
| `WORKDIR`            | 工作目录           | 相对路径基准           | 设 `/app`，后续 `COPY`/`RUN` 基于此                 |
| `COPY`               | 复制构建上下文文件 | 精确、可缓存           | **优先于 ADD**（ADD 含解压语义，易误用）            |
| `RUN`                | 构建期命令         | 装依赖、编译           | 合并同类项；**依赖文件单独一层**                    |
| `ENV`                | 运行时/构建期变量  | 默认配置               | **不放密钥**                                        |
| `EXPOSE`             | 文档化端口         | 协作、探针             | 与 `CMD` 监听端口一致                               |
| `USER`               | 运行用户           | 降权                   | 生产 **非 root**（如 `USER 10001`）                 |
| `CMD` / `ENTRYPOINT` | 进程入口           | 容器即进程             | 一个容器一个主进程；`ENTRYPOINT` 固定，`CMD` 可覆盖 |

**Python 叙事**：`requirements.txt` → `pip install` → `COPY app/` →
`uvicorn`/`gunicorn`（**Flask/FastAPI** 均可）\
**Java 对照**：多阶段 `mvn package` → 仅 `COPY target/*.jar` → `java -jar`（Fat Jar + JRE 镜像）\
**Node 对照**：`package.json` / lockfile 单独一层 → `npm ci` → 再 `COPY` 业务代码（与 Python
分层原则相同）

#### Demo 1：最小 Web 镜像（Python 主线）

| 项         | 说明                                                                               |
| ---------- | ---------------------------------------------------------------------------------- |
| **客户端** | Docker CLI（`docker build` / `docker run`）+ BuildKit（可选，`DOCKER_BUILDKIT=1`） |
| **服务端** | 本机 **Docker Engine**（或 Colima / Docker Desktop 自带的 engine）                 |
| **应用**   | FastAPI 示例（与第二晚 OBS 共用同一工程）                                          |

目录结构：

```text
lab-demo/
├── .dockerignore
├── Dockerfile
├── requirements.txt      # fastapi, uvicorn[standard]
└── app/
    └── main.py
```

`app/main.py`：

```python
import os
from fastapi import FastAPI

app = FastAPI()
_ready = False

@app.on_event("startup")
async def startup():
    global _ready
    # 真实场景：在此探测 DB、OBS、配置中心等
    _ready = True

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    if not _ready:
        return {"status": "not_ready"}, 503
    return {"status": "ready"}

@app.get("/")
def root():
    return {
        "msg": "lab-demo",
        "version": os.getenv("APP_VERSION", "unknown"),  # 构建时注入，与镜像 tag 同源
        "log_level": os.getenv("LOG_LEVEL", "info"),
    }
```

`requirements.txt`

```
fastapi==0.138.0
uvicorn[standard]==0.49.0
```

`Dockerfile`：

```dockerfile
FROM crpi-wbg5vm8h2xypwe6e.cn-chengdu.personal.cr.aliyuncs.com/gpufusion/python:3.11-slim-bookworm
WORKDIR /app
ARG APP_VERSION=0.0.0
ENV PYTHONUNBUFFERED=1 APP_VERSION=$APP_VERSION
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
```

手动运行：`uvicorn app.main:app --host 0.0.0.0 --port 8080`

`.dockerignore`（Why：减小上下文、避免密钥进层）：

```text
.venv/
__pycache__/
.git/
.env*
*.pem
```

**操作步骤**：

```bash
cd lab-demo
docker build --build-arg APP_VERSION=0.1.0 -t lab-demo:0.1.0 .
docker run --rm -p 8080:8080 -e LOG_LEVEL=info lab-demo:0.1.0
curl -s localhost:8080/health
curl -s localhost:8080/ready
curl -s localhost:8080/          # 应含 "version":"0.1.0"
```

**Java 平行对照（讲授 3 分钟，不现场敲）**：

```dockerfile
# stage 1: build
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q package -DskipTests

# stage 2: runtime
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY --from=build /src/target/*.jar app.jar
USER appuser
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
```

> **Reference**
>
> - [Dockerfile 参考](https://docs.docker.com/reference/dockerfile/)
> - [OCI Image Spec](https://github.com/opencontainers/image-spec)
> - [FastAPI 部署](https://fastapi.tiangolo.com/deployment/docker/)

---

### 1.3 工程化构建习惯与安全

[返回目录](#课程目录)

#### What / Why / How 对照表

| 主题                | What                    | Why                      | How                                                                |
| ------------------- | ----------------------- | ------------------------ | ------------------------------------------------------------------ |
| **层顺序与缓存**    | 每条 `RUN`/`COPY` 一层  | 上层失效则下层重建       | 先 `COPY requirements.txt` + `pip install`，再 `COPY` 业务代码     |
| **BuildKit**        | 新一代构建引擎          | 并行、缓存挂载           | `DOCKER_BUILDKIT=1 docker build`；`RUN --mount=type=cache`（纲要） |
| **`.dockerignore`** | 排除构建上下文          | 加速、防泄密             | 忽略 `venv`、`node_modules`、`.env`                                |
| **多阶段构建**      | 多 `FROM`，只保留运行时 | 镜像不含编译器、源码     | Java/Maven、Go build 典型                                          |
| **非 root**         | `USER` 非 0             | 容器逃逸面减小           | 行内规范常强制                                                     |
| **密钥不进镜像**    | 无 AK/SK/连接串         | 层历史可 forensic 恢复   | 运行时 **环境变量 / Secret 挂载**                                  |
| **`ARG` 风险**      | 构建参数                | 可能写入层历史           | 敏感构建参数用 **secret mount**；生产镜像避免 `ARG PASSWORD`       |
| **CI 同源**         | 同一 Dockerfile         | 消除「本地成功 CI 失败」 | 本地 `docker build` 与流水线同一文件、同一 context                 |
| **多架构 / 扫描**   | arm64 等与 CVE 扫描     | 信创与合规               | 本课**点到为止**；扩展见 FAQ Q4                                    |

#### Demo 2：观察层缓存

```bash
# 第一次：全量构建
docker build --build-arg APP_VERSION=0.1.0 -t lab-demo:0.1.0 .

# 改 app/main.py 一行，再构建——应只重建 COPY app 之后的层
# 改 requirements.txt——应从 pip install 层重建
docker history lab-demo:0.1.0 --no-trunc | head
```

**讲解要点**：`docker history` 可见每层命令；**Why** 密钥不能 `ENV OBS_SK=xxx`——会永久留在历史中。

> **Reference**
>
> - [Docker BuildKit](https://docs.docker.com/build/buildkit/)
> - [多阶段构建](https://docs.docker.com/build/building/multi-stage/)
> - [Docker 安全基线（非 root、扫描）](https://docs.docker.com/develop/security-best-practices/)

---

### 1.4 运行契约：健康检查、配置与日志

[返回目录](#课程目录)

#### 1.4.1 启动契约

| 项                   | What                        | Why                    | How                                        |
| -------------------- | --------------------------- | ---------------------- | ------------------------------------------ |
| 入口                 | 主进程命令                  | 平台重启、扩缩容依赖它 | `CMD`/`ENTRYPOINT` 与本地 IDE 运行方式一致 |
| `PYTHONUNBUFFERED=1` | 无缓冲 stdout               | 日志实时采集           | Python 容器 **必设**                       |
| Java 堆              | `-Xmx` / `MaxRAMPercentage` | 容器有 cgroup 内存上限 | 用 **百分比** 适配不同 limit               |
| 工作目录             | `WORKDIR`                   | 相对路径、脚本假设     | 文档化                                     |

#### 1.4.2 `/health` vs `/ready`

| 探针                   | What         | Why            | How                                 |
| ---------------------- | ------------ | -------------- | ----------------------------------- |
| **Liveness** `/health` | 进程是否活着 | 死锁时重启     | 不查外部依赖；快速 200              |
| **Readiness** `/ready` | 能否接流量   | 滚动发布、缩容 | DB/OBS/缓存就绪才 200；否则 **503** |

**Why 必须分开？**\
仅 Liveness：OBS 未就绪时进程仍「活着」，K8s 不会重启，但 **Service 已把流量打进来** → 500 风暴。

CCE / ServiceStage 在 Deployment 中配置 `livenessProbe` / `readinessProbe` 的
`httpGet.path`——**路径须与应用一致**（本课交付物）。

#### 1.4.3 SIGTERM 与优雅下线

- **What**：平台缩容/发布时发 **SIGTERM**，等待 `terminationGracePeriodSeconds` 后 SIGKILL。
- **Why**：在途 HTTP 请求需处理完，否则用户看到断连。
- **How**：Uvicorn/Gunicorn/Spring Boot 均支持 graceful shutdown；**不要**在 `CMD`
  里包一层忽略信号的 shell。

**分层理解**（勿混为一谈）：

| 层                   | 谁负责                                             | 本课做法                                                                   |
| -------------------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| **进程内 HTTP 收尾** | Uvicorn 收 SIGTERM 后停接新连接、等在途请求        | `CMD ["uvicorn", ...]`（exec 形式）；可选 `--timeout-graceful-shutdown 25` |
| **平台摘流量**       | K8s/CCE：Pod Terminating 时 Endpoint `ready=false` | 平台配置；研发保证探针路径正确                                             |
| **资源清理**         | 应用 `lifespan` shutdown                           | 关闭 OBS 客户端、连接池等（见下）                                          |

**lifespan：shutdown 阶段清理资源**（第二晚接入 OBS 后适用；与
[Demo 1](#12-镜像与-dockerfile从源码到制品) 的 `main.py` 对齐）：

```python
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from obs import ObsClient

_ready = False
_obs: ObsClient | None = None


def _build_obs() -> ObsClient:
    return ObsClient(
        access_key_id=os.environ["OBS_AK"],
        secret_access_key=os.environ["OBS_SK"],
        server=os.environ["OBS_ENDPOINT"],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ready, _obs
    _obs = _build_obs()
    # 真实场景：在此 listObjects / headBucket 等探测 OBS 可达后再 _ready = True
    _ready = True
    yield
    # shutdown：Uvicorn 已在 drain HTTP；此处只做资源释放
    _ready = False
    _obs = None  # esdk-obs-python 无长连接池时置空即可；有自定义连接池则 close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not _ready:
        return {"status": "not_ready"}, 503
    return {"status": "ready"}
```

Dockerfile 可与 graceful 超时对齐（grace 须小于 Pod `terminationGracePeriodSeconds`）：

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080",
     "--timeout-graceful-shutdown", "25"]
```

本地验证：`docker stop -t 10 <container>`，观察在途请求能返回后再退出（见
[Demo 3](#demo-3探针与配置外置)）。

#### 1.4.4 配置外置

- **What**：连接串、AK/SK、特性开关不进镜像、不进 Git。
- **Why**：同一镜像跑 dev/test/prod；合规。
- **How**：
  - **环境变量**：12-Factor 首选；键名由研发文档化（如 `OBS_ENDPOINT`）。
  - **配置文件挂载**：复杂配置、多文件；Stack 上常经 ConfigMap/Secret。
  - **原则**：研发提供 **「需要哪些键」**；平台提供 **「注入通道」**。

#### 1.4.5 日志

- **What**：业务日志写 **stdout / stderr**。
- **Why**：平台 agent 采集容器标准流；勿写本地文件（容器文件系统 ephemeral）。
- **How**：结构化 JSON 可选；至少含 `level`、`msg`、`trace_id`（与运维约定）。

#### Demo 3：探针与配置外置

| 项         | 说明                |
| ---------- | ------------------- |
| **客户端** | `curl` + Docker CLI |
| **服务端** | 本机容器内 FastAPI  |

```bash
# 模拟「未就绪」：启动前设 READY=false 的实现可在代码里用 env 控制（课堂可快速改）
docker run --rm -p 8888:8080 \
  -e LOG_LEVEL=debug \
  -e OBS_ENDPOINT=https://obs.example.internal \
  lab-demo:0.1.0

curl -i localhost:8888/ready
docker stop -t 5 $(docker ps -q --filter ancestor=lab-demo:0.1.0)  # 观察优雅退出
```

**nerdctl / crictl（带过，不 Demo）**：

| 工具        | 场景                                 | 与 docker 关系   |
| ----------- | ------------------------------------ | ---------------- |
| **docker**  | 研发本机构建验证                     | 完整 CLI         |
| **nerdctl** | 节点上 containerd 的 Docker 兼容 CLI | 构建仍多在 CI    |
| **crictl**  | K8s 节点排查 Pod/容器                | **不用于 build** |

> **Reference**
>
> - [K8s Configure Liveness/Readiness](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
> - [容器终止与优雅下线](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)
> - [12-Factor Config](https://12factor.net/config)

参考：<https://gitee.com/duicikeyihangaolou/lab-kubernetes/blob/master/doc/kubernetes-best-practices.md?#22-containerd>

---

### 1.5 制品入仓 SWR 与本地验证闭环

[返回目录](#课程目录)

#### What：SWR 在链路中的位置

**SWR（SoftWare Repository for Container）** = 华为容器镜像服务，托管 **OCI 镜像**，供 CCE /
ServiceStage 拉取。

```text
开发者                    SWR                         运行时
docker build  ──►  docker tag   ──►  docker push  ──►  kubelet/CCE  pull  ──►  Pod
```

#### Why：命名空间与 tag 策略

| 概念              | What                          | Why              |
| ----------------- | ----------------------------- | ---------------- |
| **组织/命名空间** | SWR 内镜像分组                | 权限隔离、多团队 |
| **镜像名**        | `registry/namespace/name:tag` | 全局唯一引用     |
| **tag**           | 可变的版本标签                | 部署、回滚依据   |
| **digest**        | 内容寻址 SHA256               | 不可变；审计用   |

**推荐 tag 约定**（团队文档化即可）：

- `1.4.2` — 语义化版本
- `1.4.2-a1b2c3d` — 版本 + Git 短 SHA
- **避免** 生产使用裸 `latest` 作为唯一标识

#### How：认证与推送

Stack 与公有云 **API 同族**，差异在 **registry 域名** 与 IAM。

**登录用户名格式（公有云常见）**：`<region>@<AK>`\
**密码**：SK

#### Demo 4：推送 SWR

| 项                     | 说明                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| **客户端（主推）**     | **Docker CLI** — `docker login` / `docker tag` / `docker push`                                   |
| **客户端（API 调试）** | **KooCLI (`hcloud`)** — 从 [API Explorer](https://console.huaweicloud.com/apiexplorer/) 生成命令 |
| **客户端（自动化）**   | **huaweicloud-sdk-python-v3** 中 SWR 模块（CI 脚本可选）                                         |
| **服务端**             | **华为 SWR**（Stack 内网 registry 或公有云 `swr.<region>.myhuaweicloud.com`）                    |

参考：`docker login -u cn-east-3@HST3W1LSC601KLBOLRU6 -p 83676402b12bff0613cc822e490761f2f0425ff635d3c4a0050c57a90d6e3923 swr.cn-east-3.myhuaweicloud.com`

```bash
export SWR_REGISTRY=swr.cn-east-3.myhuaweicloud.com   # Stack 现场换行内域名
export SWR_NAMESPACE=cloud-free
export HW_REGION=cn-east-3
export HW_ACCESS_KEY=HST3W1LSC601KLBOLRU6
export HW_SECRET_KEY=83676402b12bff0613cc822e490761f2f0425ff635d3c4a0050c57a90d6e3923

docker build --build-arg APP_VERSION=0.1.0 -t lab-demo:0.1.0 .

docker tag lab-demo:0.1.0 \
  ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.1.0

docker login -u ${HW_REGION}@${HW_ACCESS_KEY} -p ${HW_SECRET_KEY} ${SWR_REGISTRY}

docker push ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.1.0
```

**验证**：SWR 控制台 → 镜像列表 → 确认 tag 与大小。

**Stack 切换清单**（讲授 2 分钟）：

| 公有云自学                        | Stack 生产                |
| --------------------------------- | ------------------------- |
| `swr.cn-east-3.myhuaweicloud.com` | 行内 registry FQDN        |
| 控制台 AK/SK                      | RAM 子账号 / 临时密钥策略 |
| 公网 push                         | 通常需 VPN/专线           |

> **Reference**
>
> - [SWR 产品描述](https://support.huaweicloud.com/productdesc-swr/swr_03_0001.html)
> - [SWR 用户指南（推送镜像）](https://support.huaweicloud.com/usermanual-swr/swr_01_0011.html)
> - [KooCLI 快速入门](https://support.huaweicloud.com/qs-hcli/hcli_02_005.html)
> - [huaweicloud-sdk-python-v3（SWR）](https://github.com/huaweicloud/huaweicloud-sdk-python-v3)

端到端走通，参考：<https://gitee.com/dev-99cloud/training-kubernetes/blob/master/doc/class-01-Kubernetes-Administration.md#29-%E5%90%AF%E5%8A%A8%E4%B8%80%E4%B8%AA-pod>

---

### 1.6 第一晚小结与预习

[返回目录](#课程目录)

**今晚应带走**：

1. 能写出分层合理、非 root、无密钥的 Dockerfile
2. 能解释 `/health` 与 `/ready` 差异，并本地 curl 验证
3. 能把镜像 push 到 SWR（或理解 Stack 内网等价流程）
4. 知道 `docker`（构建）与 `crictl`（节点排查）的分工

**验收要点（展开）**：

**① 分层合理、非 root、无密钥**（范例见
[1.2 Demo 1](#12-镜像与-dockerfile从源码到制品)、[1.3](#13-工程化构建习惯与安全)）：

| 要求     | 怎么做                                                                         | 自测                                                         |
| -------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| 分层合理 | 先 `COPY requirements.txt` + `pip install`，再 `COPY app/`；配 `.dockerignore` | 改 `main.py` 只重建末层；改 `requirements.txt` 从 pip 层重建 |
| 非 root  | `RUN useradd` + `USER appuser`（如 uid 10001）                                 | `docker run --rm <img> id` → uid≠0                           |
| 无密钥   | 不写 `ENV OBS_SK=...`；`.dockerignore` 排除 `.env*`；运行时 `-e` 或 Secret     | `docker history <img>` 中无 AK/SK                            |

```dockerfile
# 最小骨架（与 Demo 1 一致）
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
USER appuser
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**④ `docker` 与 `crictl` 分工**（详见 [1.4](#14-运行契约健康检查配置与日志)）：

| 工具       | 谁用            | 做什么                                     | 不做什么         |
| ---------- | --------------- | ------------------------------------------ | ---------------- |
| **docker** | 研发本机 / CI   | `build` / `run` / `push` SWR               | 不在节点排 Pod   |
| **crictl** | 运维登 CCE 节点 | `crictl pods` / `ps` / `logs` 查运行时容器 | **不用于 build** |

一句话：**构建与推镜像用 `docker`；线上 Pod 已在节点 containerd 里跑，SSH 到 worker 用 `crictl`
排查。**

**第二晚预习**：

- 准备 OBS 桶名、endpoint、AK/SK（环境变量，勿提交 Git）
- 阅读
  [OBS Python SDK 开发指南](https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_0501.html) 前
  2 章

**无 Stack 权限时**：见 [第三部分 · 自学实验](#第三部分无-stack-环境--自学实验跟练手册)。

---

# 第二晚：OBS 工程化接入与发布侧要点（2 小时）

[返回目录](#课程目录)

**今晚目标**：在「镜像已入 SWR」前提下，补齐 **OBS
代码接入**、**发布侧研发责任**、**端到端价值流**。

| 时段      | 内容               | 形式        |
| --------- | ------------------ | ----------- |
| 0:00–0:25 | 2.1 发布与配置清单 | 讲授        |
| 0:25–1:05 | 2.2 OBS 接入       | 讲授 + Demo |
| 1:05–1:20 | 2.3 OBS 最佳实践   | 讲授        |
| 1:20–1:30 | 2.4 分布式补位     | 讲授        |
| 1:30–1:55 | 2.5 端到端 + AI    | Demo 串讲   |
| 1:55–2:00 | 2.6 小结           | 收束        |

---

### 2.1 发布与配置：研发侧交付清单

[返回目录](#课程目录)

#### What：滚动发布时长什么样？

多副本 Deployment **滚动/灰度**更新时，**新旧 Pod 可能同时在线**：

```text
时间 ─────────────────────────────────────►
Pod:  [v1] [v1] [v2] [v2] [v2]
流量:      ↑ 可能同时打到 v1 和 v2
```

#### Why：研发必须保证的三件事

| 主题                | Why                      | How（研发侧）                                              |
| ------------------- | ------------------------ | ---------------------------------------------------------- |
| **镜像 tag / 回滚** | 出问题需快速换回已知版本 | tag 与 Git tag / 流水线 build 号绑定；文档化回滚命令       |
| **密钥不进库**      | 泄露、审计               | `.env` 进 `.gitignore`；CI 用 Secret                       |
| **接口向前兼容**    | 新旧并存                 | 只增字段不删；Deprecated 周期                              |
| **DB 向前兼容**     | 迁移与发布解耦           | 先扩列 nullable → 双写 → 切读 → 删旧列（原则，不展开 DBA） |
| **readiness**       | 冷启动/OBS 慢            | `/ready` 含依赖探测；`initialDelaySeconds` 与平台对齐      |
| **会话**            | 多副本                   | 优先 **无状态 + 外置会话**；粘滞会话是架构抉择             |

#### How：与 ServiceStage / CCE 对接时研发交付物

不写控制台逐步点击，只交付 **清单**：

```markdown
## 应用交付清单（示例）

- 镜像：swr.xxx/bank/app:1.2.0+abc1234
- 端口：8080
- 探针：GET /health (liveness), GET /ready (readiness)
- 环境变量：
  - OBS_ENDPOINT（必填）
  - OBS_BUCKET（必填）
  - OBS_AK / OBS_SK（Secret 注入，键名固定）
  - LOG_LEVEL（可选，默认 info）
- 资源建议：cpu 500m, memory 512Mi（供平台参考）
```

> **Reference**
>
> - [滚动更新 Deployment](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
> - [数据库迁移与零停机发布（概念）](https://martinfowler.com/bliki/ParallelChange.html)

#### CCE 最小清单：`Deployment` + `Service`（接 [1.5 SWR 推送](#15-制品入仓-swr-与本地验证闭环) → Pod）

价值流补全（与 §1.5 图示一致）：

```text
docker build → docker push SWR → kubectl apply / set image → CCE 拉镜像 → Service → 流量
```

镜像地址与 [§1.5 Demo 4](#15-制品入仓-swr-与本地验证闭环) 推送结果一致，探针路径与
[§1.2 Demo 1](#12-镜像与-dockerfile从源码到制品) `/health` `/ready` 一致。

`deploy/lab-demo.yaml`：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: lab-demo-obs
type: Opaque
stringData:
  OBS_ENDPOINT: "https://obs.cn-east-3.myhuaweicloud.com"   # Stack：行内 endpoint
  OBS_BUCKET: "test9527-9527"
  OBS_AK: "your-ak"
  OBS_SK: "your-sk"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lab-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lab-demo
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0          # 滚动时至少保持原副本数，利于与 /ready 配合
  template:
    metadata:
      labels:
        app: lab-demo
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: app
          image: swr.cn-east-3.myhuaweicloud.com/cloud-free/lab-demo:0.1.0   # 与 docker push 一致
          ports:
            - containerPort: 8080
          envFrom:
            - secretRef:
                name: lab-demo-obs
          env:
            - name: LOG_LEVEL
              value: "info"
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: lab-demo
spec:
  type: NodePort
  selector:
    app: lab-demo
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 31111
```

**首次部署**：

```bash
# 1. 镜像已 push（§1.5 Demo 4）
export SWR_REGISTRY=swr.cn-east-3.myhuaweicloud.com
export SWR_NAMESPACE=cloud-free

# 2. 应用清单（Secret 也可用 --from-env-file，勿提交 Git）
kubectl apply -f deploy/lab-demo.yaml

# 3. 等待就绪
kubectl rollout status deployment/lab-demo
kubectl get pods -l app=lab-demo
kubectl get svc lab-demo   # 确认 NodePort 31111
curl -i http://<节点IP>:31111/health
curl -i http://<节点IP>:31111/ready
curl -s http://<节点IP>:31111/ | python3 -m json.tool   # 确认 version 与镜像 tag 一致
```

#### 滚动发布（rollout）与回滚

**版本标识**（用于课堂观测 v1/v2，勿在 Python 里 hardcode）：

| 方式       | 做法                                                                                                 |
| ---------- | ---------------------------------------------------------------------------------------------------- |
| **推荐**   | `docker build --build-arg APP_VERSION=0.1.0` → Dockerfile `ENV APP_VERSION` → `GET /` 返回 `version` |
| **不推荐** | 代码写死 `"version": "0.1.0"`，或与镜像 tag 脱节的 Deployment `env`                                  |

版本随**镜像制品**走；`kubectl set image` 只改镜像 tag，不必在 YAML 里再写一遍 `APP_VERSION`。

改代码 → 构建 v2 → push 后触发滚动：

```bash
docker build --build-arg APP_VERSION=0.2.0 -t lab-demo:0.2.0 .
docker tag lab-demo:0.2.0 ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.2.0
docker push ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.2.0

export NEW_TAG=0.2.0

kubectl set image deployment/lab-demo \
  app=${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:${NEW_TAG} \
  --record

kubectl rollout status deployment/lab-demo    # 等待新 Pod Ready、旧 Pod 终止
kubectl get rs -l app=lab-demo               # 可见新旧 ReplicaSet
```

**观察滚动过程**（对应上文「新旧 Pod 同时在线」）：

```bash
kubectl get pods -l app=lab-demo -w
```

#### 课堂验证：无中断 + v1/v2 并存

两终端对照（NodePort **31111**）：

**终端 1 — 持续发包**（打业务路由 `/`，**不要**打 `/ready`；冷启动 503 不等于服务中断）：

```bash
NODE_IP=<节点IP>
while true; do
  body=$(curl -sf --connect-timeout 2 "http://${NODE_IP}:31111/" 2>/dev/null) \
    || { echo "$(date +%T) ERR"; sleep 0.3; continue; }
  ver=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "?")
  echo "$(date +%T) $ver"
  sleep 0.3
done
```

**终端 2 — 触发滚动**（见上 `kubectl set image`）。

**验收**：

| 观测                                    | 说明                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------- |
| 终端 1 长时间无 `ERR`                   | 滚动期间 Service 始终有可服务 Pod（配合 `maxUnavailable: 0` + readiness） |
| 终端 1 出现 `0.1.0` 与 `0.2.0` 交替     | **数据面**：流量同时打到两代镜像                                          |
| 终端 2 曾同时 Running 多个 Pod、两个 RS | **控制面**：v1/v2 并存                                                    |
| 滚动结束后只剩 `0.2.0`                  | 发布完成                                                                  |

**研发侧约束**（并存期间别踩坑，见 §2.1 Why 表）：接口 JSON **只增字段**；OBS Key 带前缀；新 Pod OBS
未就绪时 `/ready` 503（不应因此用 `/ready` 做用户无感探测）。

**回滚**（镜像 tag 与 Git / 流水线 build 号绑定，便于定位）：

```bash
kubectl rollout history deployment/lab-demo
kubectl rollout undo deployment/lab-demo              # 回滚到上一版
kubectl rollout undo deployment/lab-demo --to-revision=2
kubectl rollout status deployment/lab-demo
```

- 新镜像须已 push SWR；CCE 拉取失败时检查 imagePullSecret（同账号 SWR 常可免密）。
- ServiceStage 控制台发布等价于改镜像 + 探针/env；有 CCE 权限时用本 YAML 自学替身。

---

### 2.2 OBS 代码层接入

[返回目录](#课程目录)

#### What：OBS 与开发 API

**OBS（Object Storage Service）** 提供 **RESTful 对象存储**（桶 Bucket、对象 Key、字节流）。\
与本地磁盘差异：**无目录树实体**，Key 是字符串；** eventual consistency** 在列举场景需注意。

**Stack 上 OBS** 与公有云 **SDK/API 同族**，替换 **endpoint** 即可（行内 HTTPS 地址）。\
上传、下载、列举为必讲；**异常处理、重试**见 [2.3.4](#234-重试与幂等)；**大文件分片**（multipart
upload）视课时择优展开，见 OBS SDK 文档。

#### Why：分层封装

| 反模式                             | 问题             |
| ---------------------------------- | ---------------- |
| Controller 里直接 `ObsClient(...)` | AK/SK 散落、难测 |
| Key 硬编码                         | 冲突、难治理     |
| catch 所有 Exception 吞掉          | 排障困难         |

**目标**：`storage` 模块统一 OBS；业务只调 `ObjectStorage.upload/download`。

#### How：SDK 选型

| 包 / 仓库                      | What                                                                                                                                              | 本课用途                                              |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **huaweicloud-sdk-python-obs** | 华为 **OBS 官方 Python SDK**（[GitHub](https://github.com/huaweicloud/huaweicloud-sdk-python-obs)）；`from obs import ObsClient`，`putContent` 等 | ✅ **第二晚主线**（上传/下载/预签名，见 Demo 5–7）    |
| **esdk-obs-python**（PyPI）    | 上表同一套 SDK 的 **安装包名**（`pip install` 用此名，非第三个 SDK）                                                                              | ✅ 与官方仓配套，钉 `==3.26.2`                        |
| **huaweicloud-sdk-python-v3**  | 华为云 **统一** SDK（SWR/ECS/IAM… 各服务子包）                                                                                                    | ⚠️ **仅** §1.5 SWR API 自动化可选；**不**用于 OBS 实验 |
| **huaweicloudsdkobs**          | 统一 SDK 里的 OBS 子包，API 与官方 OBS SDK **不同**                                                                                               | ❌ 本课不用（需重写 `putContent` 等调用）             |

| 语言       | 客户端 SDK                         | 服务端                     |
| ---------- | ---------------------------------- | -------------------------- |
| **Python** | **esdk-obs-python**（`ObsClient`） | 华为 OBS（Stack / 公有云） |
| Java       | **esdk-obs-java**（`ObsClient`）   | 同上                       |
| 通用 REST  | SigV4 风格签名 HTTP                | 不推荐手写，用 SDK         |

**装哪个？** 官方仓库是
**[huaweicloud-sdk-python-obs](https://github.com/huaweicloud/huaweicloud-sdk-python-obs)**；`pip install`
时包名写 **`esdk-obs-python`**（同一套代码）。与下文 `from obs import ObsClient` 一致。**不要**为
OBS 去装 `huaweicloud-sdk-python-v3` / `huaweicloudsdkobs`。

安装（钉版本，写入 `requirements.txt`）：

```bash
pip install "esdk-obs-python==3.26.2"
```

```text
# requirements.txt（第二晚起与 fastapi 并列）
esdk-obs-python==3.26.2
fastapi==0.138.0
uvicorn[standard]==0.49.0
```

> 官方源码仓
> [huaweicloud-sdk-python-obs](https://github.com/huaweicloud/huaweicloud-sdk-python-obs)；PyPI
> 发布名为 `esdk-obs-python`（版本号与 REST API 配套，如 `3.26.2`）。与统一 SDK 子包
> `huaweicloudsdkobs`（`3.1.x`）**不是同一条版本线**。课堂/CI 用 `==` 钉死，升级时对照
> [OBS Python SDK 发布说明](https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_0501.html)。

#### 环境变量契约

OBS 控制台，我的凭证，访问密钥。

```bash
OBS_ENDPOINT=https://obs.cn-east-3.myhuaweicloud.com   # Stack：行内 endpoint
OBS_BUCKET=test9527-9527
OBS_AK=...
OBS_SK=...
```

#### Demo 5：OBS smoke test

| 项           | 说明                                                                       |
| ------------ | -------------------------------------------------------------------------- |
| **客户端**   | **esdk-obs-python** — `ObsClient.putContent` / `getObject` / `listObjects` |
| **服务端**   | **华为 OBS**（桶需事先创建；权限含 `PutObject`/`GetObject`/`ListBucket`）  |
| **运行方式** | 本机 Python 脚本（或第一晚 FastAPI 容器外挂 `--env-file`）                 |

`storage/obs_client.py`：

```python
import os
from obs import ObsClient, PutObjectHeader

def build_obs_client() -> ObsClient:
    return ObsClient(
        access_key_id=os.environ["OBS_AK"],
        secret_access_key=os.environ["OBS_SK"],
        server=os.environ["OBS_ENDPOINT"],
    )


class ObjectStorage:
    def __init__(self, client: ObsClient, bucket: str):
        self._client = client
        self._bucket = bucket

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        resp = self._client.putContent(
            self._bucket,
            key,
            data,
            headers=PutObjectHeader(contentType=content_type),
        )
        if resp.status >= 300:
            raise RuntimeError(f"OBS putContent failed: status={resp.status}, reason={resp.reason}")
        return key

    def download_bytes(self, key: str) -> bytes:
        resp = self._client.getObject(self._bucket, key, loadStreamInMemory=True)
        if resp.status >= 300:
            raise RuntimeError(f"OBS getObject failed: status={resp.status}")
        return resp.body.buffer

    def list_keys(self, prefix: str = ""):
        resp = self._client.listObjects(self._bucket, prefix=prefix)
        if resp.status >= 300:
            raise RuntimeError(f"OBS listObjects failed: status={resp.status}")
        for obj in resp.body.contents or []:
            yield obj.key
```

`scripts/obs_smoke_test.py`：

```python
import os
from datetime import date
from storage.obs_client import build_obs_client, ObjectStorage

def main():
    store = ObjectStorage(build_obs_client(), os.environ["OBS_BUCKET"])
    key = f"lab/{date.today().isoformat()}/hello.txt"
    store.upload_bytes(key, b"hello obs", content_type="text/plain; charset=utf-8")
    assert store.download_bytes(key) == b"hello obs"
    print("OK", key)

if __name__ == "__main__":
    main()
```

```bash
source .env.local   # 含 OBS_* 变量
python scripts/obs_smoke_test.py
```

#### Demo 6：Web 上传最短路径（FastAPI）

| 项              | 说明                               |
| --------------- | ---------------------------------- |
| **客户端**      | 浏览器 / `curl` → **FastAPI 应用** |
| **应用 → 存储** | **esdk-obs-python** → **OBS**      |

在 `app/main.py` 增加：

```python
from fastapi import UploadFile, File
from app.storage.obs_client import build_obs_client, ObjectStorage
import os
from uuid import uuid4

def get_store() -> ObjectStorage:
    return ObjectStorage(build_obs_client(), os.environ["OBS_BUCKET"])

@app.post("/files")
async def upload_file(file: UploadFile = File(...)):
    body = await file.read()
    key = f"uploads/{uuid4().hex}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"
    get_store().upload_bytes(key, body, content_type=content_type)
    return {"key": key, "content_type": content_type}
```

```bash
# curl -F "file=@./README.md" http://localhost:8080/files
curl -X POST http://127.0.0.1:8089/files -F "file=@/root/lab-demo/app/obs_smoke_test.py"
```

**`/ready` 增强（Why 呼应 2.1）**：startup 时 `listObjects` 探测桶可达，失败则 `_ready=False`。

```python
@app.get("/ready")
def ready():
    try:
        get_store().probe_bucket()
    except Exception:
        logger.exception("OBS bucket probe failed")
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
```

> **Reference**
>
> - [OBS Python SDK 开发指南](https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_0501.html)
> - [OBS API 参考（REST）](https://support.huaweicloud.com/api-obs/obs_04_0001.html)
> - [OBS Python SDK 官方仓库（huaweicloud-sdk-python-obs）](https://github.com/huaweicloud/huaweicloud-sdk-python-obs)（PyPI：`esdk-obs-python`）
> - [OBS Java SDK](https://support.huaweicloud.com/sdk-java-devg-obs/obs_22_0501.html)

---

### 2.3 OBS 工程化最佳实践

[返回目录](#课程目录)

#### 2.3.1 预签名 URL

|                | What                 | Why                                     | How                                                  |
| -------------- | -------------------- | --------------------------------------- | ---------------------------------------------------- |
| **预签名 URL** | 带时效的临时授权 URL | 大文件/前端直传，**业务网关不中转字节** | `ObsClient.createSignedUrl`（方法名以 SDK 文档为准） |

```text
小文件：Client → App → OBS（Demo 6）
大文件：Client → App 申请 URL → Client 直传 OBS
```

| 场景           | 路径                                       | `method` | 客户端动作                     |
| -------------- | ------------------------------------------ | -------- | ------------------------------ |
| **预签名下载** | Client → App 申请 URL → Client **GET** OBS | `GET`    | 浏览器打开 URL / `curl -O`     |
| **预签名上传** | Client → App 申请 URL → Client **PUT** OBS | `PUT`    | 前端/curl 直传字节，App 不中转 |

**Demo 7-A：预签名下载**

| 项         | 说明                                            |
| ---------- | ----------------------------------------------- |
| **客户端** | 浏览器打开 URL / `curl -O`                      |
| **签发端** | FastAPI + **esdk-obs-python** `createSignedUrl` |
| **服务端** | OBS 验证签名后返回对象字节流                    |

```python
@app.get("/files/{key:path}/download-url")
def presigned_download(key: str, expires: int = 3600):
    client = build_obs_client()
    signed = client.createSignedUrl(
        method="GET",
        bucketName=os.environ["OBS_BUCKET"],
        objectKey=key,
        expires=expires,
    )
    return {"url": signed.signedUrl, "expires_in": expires}
```

**Demo 7-B：预签名上传（大文件直传）**

| 项         | 说明                                                              |
| ---------- | ----------------------------------------------------------------- |
| **客户端** | 浏览器 `fetch` PUT / `curl --data-binary`                         |
| **签发端** | FastAPI 生成 `PUT` URL；`Content-Type` 参与签名时前端必须带相同头 |
| **前置**   | 桶需配 **CORS**（浏览器直传）；`curl` 本机调试可跳过              |

```python
@app.post("/files/upload-url")
def presigned_upload(filename: str, content_type: str = "application/octet-stream"):
    key = f"uploads/{uuid4().hex}/{filename}"
    client = build_obs_client()
    signed = client.createSignedUrl(
        method="PUT",
        bucketName=os.environ["OBS_BUCKET"],
        objectKey=key,
        expires=3600,
        headers={"Content-Type": content_type},
    )
    return {
        "key": key,
        "url": signed.signedUrl,
        "headers": signed.actualSignedRequestHeaders,
        "expires_in": 3600,
    }
```

##### 大文件预签名上传 / 下载（8089）

**准备测试文件**

```bash
dd if=/dev/urandom of=/tmp/big-test.bin bs=1M count=2 status=none
sha256sum /tmp/big-test.bin
```

**Demo 7-B：预签名上传（Client 直传 OBS）**

Step 1 — 向 App 申请上传 URL：

```bash
curl -s -X POST \
  "http://127.0.0.1:8089/files/upload-url?filename=big-test.bin&content_type=application/octet-stream"
```

示例返回：

```json
{
  "key": "uploads/f04dc5b9952c4f4ea50464715b2b2b46/big-test.bin",
  "url": "https://test9527-9527.obs.cn-east-3.myhuaweicloud.com/uploads/...?Expires=...&AccessKeyId=...&Signature=...",
  "headers": {
    "Content-Type": "application/octet-stream",
    "Host": "test9527-9527.obs.cn-east-3.myhuaweicloud.com"
  },
  "expires_in": 3600
}
```

Step 2 — 用返回的 `url` 直传 OBS（不经过 App）：

```bash
# 把 <signedUrl> 换成上一步返回的 url
curl -X PUT \
  -H "Content-Type: application/octet-stream" \
  --data-binary @/tmp/big-test.bin \
  "<signedUrl>"
```

`Content-Type` 必须与 Step 1 申请时一致。

**Demo 7-A：预签名下载（Client 直访 OBS）**

Step 3 — 向 App 申请下载 URL：

```bash
# 把 <key> 换成 Step 1 返回的 key
curl -s \
  "http://127.0.0.1:8089/files/<key>/download-url"
```

示例（key 含 `/`，可直接写路径）：

```bash
curl -s \
  "http://127.0.0.1:8089/files/uploads/f04dc5b9952c4f4ea50464715b2b2b46/big-test.bin/download-url"
```

示例返回：

```json
{
  "url": "https://test9527-9527.obs.cn-east-3.myhuaweicloud.com/uploads/...?Expires=...&AccessKeyId=...&Signature=...",
  "expires_in": 3600
}
```

Step 4 — 用返回的 `url` 直访 OBS 下载：

```bash
# 把 <signedUrl> 换成上一步返回的 url
curl -O "<signedUrl>"

# 或指定输出路径
curl -o /tmp/big-downloaded.bin "<signedUrl>"
```

**一键串联（含校验）**

```bash
# 1) 生成测试文件
dd if=/dev/urandom of=/tmp/big-test.bin bs=1M count=2 status=none
ORIG_SHA=$(sha256sum /tmp/big-test.bin | awk '{print $1}')

# 2) 申请上传 URL
UPLOAD_RESP=$(curl -s -X POST \
  "http://127.0.0.1:8089/files/upload-url?filename=big-test.bin&content_type=application/octet-stream")

KEY=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])")
SIGNED_PUT_URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

echo "key=$KEY"

# 3) PUT 直传 OBS
curl -s -o /dev/null -w "PUT HTTP %{http_code}\n" \
  -X PUT \
  -H "Content-Type: application/octet-stream" \
  --data-binary @/tmp/big-test.bin \
  "$SIGNED_PUT_URL"

# 4) 申请下载 URL
DOWNLOAD_RESP=$(curl -s \
  "http://127.0.0.1:8089/files/$(python3 -c "import urllib.parse; print(urllib.parse.quote('$KEY', safe=''))")/download-url")

SIGNED_GET_URL=$(echo "$DOWNLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")

# 5) GET 直访 OBS 下载
curl -s -o /tmp/big-downloaded.bin -w "GET HTTP %{http_code}\n" \
  "$SIGNED_GET_URL"

# 6) 校验
DOWN_SHA=$(sha256sum /tmp/big-downloaded.bin | awk '{print $1}')
echo "original:   $ORIG_SHA"
echo "downloaded: $DOWN_SHA"
[ "$ORIG_SHA" = "$DOWN_SHA" ] && echo "OK" || echo "FAIL"
```

**对照：小文件经 App 中转（Demo 6）**

```bash
curl -X POST "http://127.0.0.1:8089/files" \
  -F "file=@/tmp/big-test.bin"
```

```text
小文件：Client → App → OBS          POST /files
大文件：Client → App 申请 URL → Client PUT/GET OBS
         ↑ 只签 URL，不中转字节
```

> **Reference**
>
> - [生成带授权信息的 URL（Python SDK）](https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_1301.html)
> - [OBS 预签名 URL（控制台说明）](https://support.huaweicloud.com/usermanual-obs/obs_03_0340.html)
> - [配置 CORS 实现跨域访问 OBS](https://support.huaweicloud.com/usermanual-obs/zh-cn_topic_0066036542.html)（浏览器直传必配）
> - [AWS S3 Presigned URLs 概念对照](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)（理解模型）

#### 2.3.2 Key 治理

- **What**：对象键是 flat 字符串，用 `/` 只是约定。
- **Why**：检索、生命周期、租户隔离。
- **How**：`{业务}/{日期}/{租户}/{uuid}.{ext}`，例：`loan/2026-06-17/tenant-a/uuid.pdf`

#### 2.3.3 Content-Type 与元数据

- 上传时指定 `content_type`；图片/PDF 错类型会导致浏览器乱码或下载行为异常。

#### 2.3.4 重试与幂等

**重试（有限次 + 指数退避）**

| 可重试                  | 勿重试（或先查状态再决定）  |
| ----------------------- | --------------------------- |
| 超时、`ConnectionError` | 403 权限、404 对象不存在    |
| HTTP 408 / 429 / 5xx    | 400 参数错误、签名/Key 非法 |

在 `ObjectStorage` 外包一层（示例：最多 3 次，初始间隔 0.5s）：

```python
import time

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 3

def _call_obs_with_retry(call):
    delay = 0.5
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = call()
            if resp.status < 300:
                return resp
            if resp.status not in RETRYABLE_STATUS:
                raise RuntimeError(f"OBS failed: status={resp.status}, reason={resp.reason}")
            last_err = RuntimeError(f"OBS failed: status={resp.status}")
        except (TimeoutError, ConnectionError) as e:
            last_err = e
        if attempt == MAX_RETRIES - 1:
            raise last_err
        time.sleep(delay)
        delay *= 2

# 在 upload_bytes 中使用：
def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    def _put():
        return self._client.putContent(
            self._bucket, key, data,
            headers=PutObjectHeader(contentType=content_type),
        )
    resp = _call_obs_with_retry(_put)
    return key
```

**幂等（Key 策略需书面约定）**

| 策略               | Key 示例                          | 重试行为           | 适用                     |
| ------------------ | --------------------------------- | ------------------ | ------------------------ |
| **写入即新版本**   | `uploads/{uuid}/{filename}`       | 重试生成新对象     | 默认推荐（Demo 6/7-B）   |
| **固定 Key 覆盖**  | `reports/2026-06/daily.pdf`       | 重试可能覆盖旧文件 | 日报、快照等明确覆盖场景 |
| **业务幂等键查表** | DB 记 `idempotency_key → obs_key` | 同键返回已有 key   | 支付回执、表单重复提交   |

```python
# 策略 1：每次上传新 Key（与 Demo 6 一致，天然幂等）
key = f"uploads/{uuid4().hex}/{file.filename}"

# 策略 2：固定 Key — 须在 README/运维文档写明「允许覆盖」
key = f"reports/{date.today():%Y-%m}/daily.pdf"

# 策略 3：客户端带 Idempotency-Key，服务端去重（示意）
def upload_with_idempotency(idem_key: str, data: bytes) -> str:
    if existing := db.get_obs_key(idem_key):
        return existing
    key = f"uploads/{uuid4().hex}/file.bin"
    store.upload_bytes(key, data)
    db.save(idem_key, key)
    return key
```

#### 2.3.5 成本意识

- OBS ≠ 无限磁盘；冷热分层、生命周期由平台策略承载；研发避免无限期堆积临时 Key。

---

### 2.4 分布式主题：研发视角极简串联

[返回目录](#课程目录)

**不展开体系课**，只建立与今晚代码的挂钩：

| 主题          | What               | Why（与开发相关）                               |
| ------------- | ------------------ | ----------------------------------------------- |
| **服务拆分**  | 单体 → 多服务      | 镜像、配置、OBS Key 前缀按边界划分              |
| **外置配置**  | 配置不在镜像       | 见 1.4.4；与 Stack Secret 注入衔接              |
| **熔断/限流** | 下游 OBS 慢/挂     | 避免线程打满；**知道有这回事**，实现交框架/网关 |
| **无会话**    | JWT + 外置会话存储 | 多副本无需粘滞                                  |

> **Reference**
>
> - [Release It!（稳定性模式）](https://pragprog.com/titles/mnee2/release-it-second-edition/)
> - [华为 CCE 服务网格 / 熔断（产品文档）](https://support.huaweicloud.com/asm/index.html)

---

### 2.5 端到端价值流与 AI 辅助开发

[返回目录](#课程目录)

#### What：一条完整价值流

```text
1. 改业务代码 + Dockerfile（lab-demo / 课程约定基准应用）
2. docker build → docker push SWR
3. ServiceStage/CCE 拉镜像部署（平台课范畴，此处只述节点；无权限时用 docker run 代替）
4. 用户 HTTP → FastAPI → OBS 存证/读文件
5. 观测：stdout 日志、/ready 状态
6. 收束：何种业务宜代码侧接入 OBS、镜像与配置协作的边界
```

#### Demo 8：端到端串讲（讲师演示，学员跟思路）

| 步骤   | 客户端                         | 服务端                      |
| ------ | ------------------------------ | --------------------------- |
| 构建   | Docker CLI                     | Docker Engine               |
| 入仓   | `docker push`                  | SWR                         |
| 运行   | `docker run --env-file` 或 CCE | 容器内 FastAPI              |
| 存文件 | `curl -F`                      | App → esdk-obs-python → OBS |
| 读文件 | `curl` 预签名 URL              | OBS                         |

**无 CCE 权限时**：用 `docker run` 代替 ServiceStage 步骤，价值流仍成立。

#### AI 适宜介入的环节

| 环节            | AI 可帮                   | 人必须核对                       |
| --------------- | ------------------------- | -------------------------------- |
| Dockerfile 初稿 | 生成多阶段、非 root 模板  | 基础镜像版本、端口、是否含密钥   |
| OBS 封装代码    | 生成 `ObjectStorage` 类   | endpoint、异常处理、Content-Type |
| 构建报错        | 解释 `failed to solve` 层 | 是否掩盖真实安全问题             |
| `/ready` 逻辑   | 生成探测伪代码            | 依赖顺序、503 语义               |

**人工复核清单（强制）**：

1. 基础镜像 CVE / 版本是否 LTS
2. `EXPOSE` 与进程监听端口
3. 无 `ENV`/`ARG` 密钥
4. `/health` ≠ `/ready`
5. OBS endpoint 区域与桶一致
6. 预签名过期时间与 HTTP 方法
7. Key 前缀是否含租户/合规边界

> **Reference**
>
> - [第三部分 · 自学实验跟练](#第三部分无-stack-环境--自学实验跟练手册)
> - [Cursor / AI 编程边界（姊妹篇 we-know-python-coding-with-ai.md）](we-know-python-coding-with-ai.md)

---

### 2.6 第二晚小结与扩展阅读索引

[返回目录](#课程目录)

**两晚合成能力矩阵**：

| 能力       | 第一晚            | 第二晚               |
| ---------- | ----------------- | -------------------- |
| Dockerfile | ✅                | 与 CI 同源           |
| SWR        | ✅ push           | tag 与回滚           |
| 探针       | ✅ /health /ready | readiness + OBS 依赖 |
| OBS        | —                 | ✅ SDK 封装 + 预签名 |
| 配置/密钥  | ✅ 原则           | ✅ 交付清单          |
| AI 辅助    | —                 | ✅ 环节 + 复核清单   |

---

# 第三部分：无 Stack 环境 · 自学实验（跟练手册）

[返回目录](#课程目录)

> 适用场景：暂无 Stack 内网权限，需自行预习/备课/跟练。实验编号与上文 Demo 对应：**实验 1-A ≈ Demo
> 1**，以此类推。\
> **能练什么、不能替代什么**：见 [§0.1](#01-无-stack-环境自学目标与边界)。

## 环境准备（约 30 分钟）

### 本机工具

```bash
docker --version          # 建议 24+
docker buildx version     # 可选，BuildKit
python3 --version         # 建议 3.10+
```

### 华为公有云账号（SWR / OBS 实验用）

1. 注册 [华为云](https://www.huaweicloud.com/) 并完成实名（试用通常需要）。
2. 控制台 → **我的凭证 → 访问密钥**，创建 **AK/SK**（勿提交 Git）。
3. 开通 **SWR**、**OBS**（按区域，建议固定一个 region，如 `cn-east-3`）。
4. OBS 控制台创建一个 **桶（Bucket）**，记下桶名与区域。

### 环境变量模板

复制为 `.env.local`（**加入 `.gitignore`**）：

```bash
# --- SWR（docker login / SDK）---
export SWR_REGISTRY=swr.cn-east-3.myhuaweicloud.com
export SWR_NAMESPACE=your-namespace      # SWR 组织/命名空间
export HW_ACCESS_KEY=your-ak
export HW_SECRET_KEY=your-sk
export HW_REGION=cn-east-3
export HW_PROJECT_ID=your-project-id     # 控制台「我的凭证」可查

# --- OBS ---
export OBS_ENDPOINT=https://obs.cn-east-3.myhuaweicloud.com
export OBS_BUCKET=test9527-9527
export OBS_AK=$HW_ACCESS_KEY
export OBS_SK=$HW_SECRET_KEY

# --- 应用（本地 Docker 运行）---
export APP_PORT=8080
export LOG_LEVEL=info
```

> **Stack 现场**：向管理员索取内网 `SWR_REGISTRY`、`OBS_ENDPOINT`、项目/租户
> ID；变量名保持不变，只换值。

### Python 依赖（OBS 实验）

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "esdk-obs-python==3.26.2" fastapi "uvicorn[standard]"
```

### 可选：OpenStack IaaS 体验

- [DevStack](https://docs.openstack.org/devstack/latest/) 或课程级 OpenStack 实验环境
- 仅用于理解 Keystone / Project / `openstack server list`，**不覆盖 SWR/OBS**。详见
  [附录 B](#附录-bstack-vs-公有云-vs-openstack扩展) 与
  [实验 · OpenStack 补位](#实验--openstack-iaas-补位约-1-小时)。

---

## 第一晚 · 镜像与容器运行契约

### 实验 1-A：最小 Dockerfile + 分层缓存（45 min）

**目标**：对齐大纲「依赖分层、`.dockerignore`、非 root、配置外置」。\
**代码与讲解**：见 [1.2 Demo 1](#12-镜像与-dockerfile从源码到制品)（含 `/` 根路由便于自检）。

**验收**：

```bash
cd lab-demo
docker build --build-arg APP_VERSION=local -t lab-demo:local .
docker run --rm -p 8080:8080 -e LOG_LEVEL=debug lab-demo:local
curl -s localhost:8080/health
curl -s localhost:8080/ready
curl -s localhost:8080/          # 应含 "version":"local"
docker logs <container_id>   # 日志应在 stdout
```

**自检**：

- 镜像内是否无 AK/SK
- 是否非 root：`docker run --rm lab-demo:local id`（应显示 uid=10001）

**层缓存**：见 [1.3 Demo 2](#13-工程化构建习惯与安全)。

---

### 实验 1-B：健康检查与 SIGTERM（20 min）

**目标**：对齐 `/health` vs `/ready`、优雅下线行为。\
**讲解**：见 [1.4 Demo 3](#14-运行契约健康检查配置与日志)。

```bash
docker run -d --name lab-demo -p 8080:8080 lab-demo:local
docker stop lab-demo    # 发送 SIGTERM，观察退出码与日志
```

Dockerfile 中 `HEALTHCHECK` 配置见 [1.2 Demo 1](#12-镜像与-dockerfile从源码到制品) 的 Dockerfile
示例。

---

### 实验 1-C：推送 SWR（30 min，需公有云账号）

**目标**：对齐「命名空间、tag、docker login、制品入仓」。\
**讲解与命令**：见 [1.5 Demo 4](#15-制品入仓-swr-与本地验证闭环)。

1. SWR 控制台创建 **组织（命名空间）**。
2. 登录与打 tag：

```bash
source .env.local
docker tag lab-demo:local ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.1.0-local
docker login -u ${HW_REGION}@${HW_ACCESS_KEY} -p ${HW_SECRET_KEY} ${SWR_REGISTRY}
docker push ${SWR_REGISTRY}/${SWR_NAMESPACE}/lab-demo:0.1.0-local
```

3. SWR 控制台确认镜像与 tag。

**tag 约定练习**（写进团队规范即可）：

| tag 示例         | 含义                       |
| ---------------- | -------------------------- |
| `1.2.3`          | 发布版本                   |
| `1.2.3-abc1234`  | 版本 + Git 短 SHA          |
| `build-20260122` | 仅用于个人实验，勿用于生产 |

**Stack 差异**：registry 主机名一般为内网域名；login 用户名/域可能由行内文档规定，以现场为准。

---

## 第二晚 · OBS 接入与发布侧约定

### 实验 2-A：OBS 分层封装（40 min）

**目标**：AK/SK、endpoint 环境变量注入；业务层不直接接触密钥。\
**代码**：见 [2.2 Demo 5](#22-obs-代码层接入)（`storage/obs_client.py` 与
`scripts/obs_smoke_test.py`）。

**验收**：

```bash
source .env.local
python scripts/obs_smoke_test.py
```

- 脚本能上传、下载、列举
- Key 带 `lab/日期/` 前缀

---

### 实验 2-B：Web 最短路径 — 上传 + 预签名（30 min）

**目标**：对齐「预签名 URL、Content-Type、Key 治理」。\
**上传代码**：见 [2.2 Demo 6](#22-obs-代码层接入)。\
**预签名代码**：见 [2.3.1 预签名 URL](#231-预签名-url)（Demo 7-A 下载 / 7-B 上传）。\
**跟练命令**：见 [大文件预签名上传 / 下载（8089）](#大文件预签名上传--下载8089)（含一键串联与 sha256
校验）。

```text
小文件：Client → App → OBS（Demo 6）
大文件：Client → App 申请 URL → Client 直传 OBS
```

**验收**：浏览器或 curl 能经预签名 URL 下载；`sha256sum` 上传前后一致；响应头 `Content-Type` 正确。

---

### 实验 2-C：配置与发布清单演练（20 min，无云平台也可做）

**目标**：对齐 [2.1 研发侧交付清单](#21-发布与配置研发侧交付清单)。

在仓库根目录维护 `deploy/checklist.md`（自测勾选）：

- [ ] 镜像 tag 与 Git 标签/流水线 build 号一致
- [ ] 仓库内无 `.env`、无 AK/SK、Dockerfile 无 `ENV OBS_SK=...`
- [ ] `/ready` 在依赖（OBS 桶可达）就绪前返回 503
- [ ] 接口 JSON 字段只增不删（滚动发布兼容）
- [ ] OBS Key 前缀规范已文档化

---

### 实验 2-D：端到端串讲（30 min，公有云 + 本地）

**价值流**（对应大纲第四节与 [2.5 Demo 8](#25-端到端价值流与-ai-辅助开发)）：

1. 改代码 → `docker build` → `docker push` SWR
2. （若有 CCE 权限）从 SWR 镜像部署到 CCE；无 CCE 则 `docker run --env-file .env.local` 本地代替
   ServiceStage
3. 调用应用 API → 触发 OBS 上传/下载
4. 用 AI 生成 Dockerfile 草稿 / OBS 封装，再按 [AI 人工复核清单](#ai-辅助--须人工核对项) 逐项核对

---

## 实验 · OpenStack IaaS 补位（约 1 小时）

仅在已搭 DevStack 或培训 OpenStack 环境时做：

```bash
source openrc
openstack project list
openstack server list
openstack network list
```

**对照 Stack**：租户 ≈ Project；Keystone V3 鉴权；与 SWR/OBS **无直接关系**。

---

## Stack 上线前切换清单

| 项           | 公有云自学                               | Stack 生产                  |
| ------------ | ---------------------------------------- | --------------------------- |
| SWR 地址     | `swr.<region>.myhuaweicloud.com`         | 行内 registry 域名          |
| OBS endpoint | `https://obs.<region>.myhuaweicloud.com` | 行内 OBS 域名               |
| 区域 / 项目  | 控制台 project_id                        | ManageOne / Service OM 分配 |
| 凭证         | 个人 AK/SK                               | 行内 RAM 用户或临时密钥策略 |
| ServiceStage | 可用 CCE 代替练习                        | 按行内发布流程              |

Stack 内网到位后：**完成 1-A → 1-C → 2-A → 2-D 一次 endpoint 切换验证即可**。

---

## AI 辅助 · 须人工核对项

使用大模型生成 Dockerfile / OBS 代码 / 排障建议后，**至少核对**（与
[2.5 节](#25-端到端价值流与-ai-辅助开发) 复核清单一致）：

1. 基础镜像版本是否 LTS、是否有已知 CVE
2. `EXPOSE` 端口与 `CMD` 一致
3. 无密钥、连接串、`ARG` 误用导致层缓存泄露
4. `/health` 与 `/ready` 语义是否混淆
5. OBS endpoint 是否 HTTPS、是否与桶区域一致
6. 预签名 URL 过期时间、HTTP 方法是否匹配
7. Key 前缀是否满足租户/合规隔离

---

## 建议自学节奏（约 4～6 小时）

| 顺序 | 内容                        | 时长  | 对应章节                |
| ---- | --------------------------- | ----- | ----------------------- |
| 1    | 环境准备                    | 0.5 h | 第三部分 · 环境准备     |
| 2    | 1-A / 1-B Dockerfile 与探针 | 1 h   | 1.2–1.4 + 实验 1-A/1-B  |
| 3    | 1-C 推送 SWR                | 0.5 h | 1.5 + 实验 1-C          |
| 4    | 2-A / 2-B OBS 封装与预签名  | 1.5 h | 2.2–2.3 + 实验 2-A/2-B  |
| 5    | 2-C / 2-D 清单 + 端到端     | 1 h   | 2.1、2.5 + 实验 2-C/2-D |
| 6    | 可选 OpenStack              | 1 h   | OpenStack 补位 + 附录 B |

完成 **1-A → 1-C → 2-A → 2-D** 即覆盖大纲「最小可交付能力集」的主体。

---

## 附录 A：Demo 与客户端/服务端速查

| Demo | 目的      | 客户端                                      | 服务端           |
| ---- | --------- | ------------------------------------------- | ---------------- |
| 1    | 最小镜像  | Docker CLI + BuildKit                       | Docker Engine    |
| 2    | 层缓存    | Docker CLI                                  | Docker Engine    |
| 3    | 探针/配置 | curl + Docker CLI                           | 容器内 FastAPI   |
| 4    | 制品入仓  | Docker CLI；可选 KooCLI / huaweicloud-sdk   | SWR              |
| 5    | OBS 读写  | esdk-obs-python                             | OBS              |
| 6    | Web 上传  | curl / 浏览器 → FastAPI                     | OBS              |
| 7    | 预签名    | 浏览器 / curl（7-A 下载 GET；7-B 上传 PUT） | OBS              |
| 8    | 端到端    | 上述组合                                    | SWR + 容器 + OBS |

---

## 附录 B：Stack vs 公有云 vs OpenStack（扩展）

与 [§0.1 自学边界](#01-无-stack-环境自学目标与边界) 对照：下表按 **Stack 技术层次**
说明自学时可用什么环境、以及 **不能替代 Stack 现场的具体项**。

| 层次     | 技术                     | 客户端                 | 自学可练（依据）                              | 不能替代 Stack 的什么                        |
| -------- | ------------------------ | ---------------------- | --------------------------------------------- | -------------------------------------------- |
| IaaS     | Nova/Neutron/Keystone    | python-openstackclient | ✅ DevStack：**OpenStack API 子集**           | 行内 ManageOne 发放、VDC/配额流程            |
| 容器制品 | SWR                      | docker CLI             | ✅ 公有云 SWR：**API 同族**，换 registry 域名 | 内网 registry FQDN、行内 `docker login`      |
| 编排     | CCE (K8s)                | kubectl                | ⚠️ 任意 K8s：探针/YAML **与厂商无关**          | CCE 控制台、行内集群权限与网络               |
| 应用托管 | ServiceStage             | 控制台/API             | ⚠️ 仅 `docker run` 代替「跑容器」              | **ServiceStage 发布 UI、行内审批与配置绑定** |
| 对象存储 | OBS                      | esdk-obs-python        | ✅ 公有云 OBS：**API 同族**，换 endpoint      | 内网 OBS endpoint、桶策略与合规边界          |
| 全链路   | SWR→CCE/ServiceStage→OBS | 组合                   | ❌ 单练任一层都不够                           | **四层在行内一次 E2E 打通**（含 VPN/专线）   |

> MinIO 等 S3 兼容存储 **仅近似** OBS API，**不能**替代 Stack 生产 OBS + 行内 SDK/endpoint。

> **Reference**
>
> - [python-openstackclient](https://github.com/openstack/python-openstackclient)
> - [华为云 Stack 8.5.x 资源发放指南（Keystone V3）](https://support.huawei.com/enterprise/zh/doc/EDOC1100453333/ed5caf48)
> - [API Explorer](https://console.huaweicloud.com/apiexplorer/)
> - [华为云 Stack 企业培训（E2E 实验环境）](https://e.huawei.com/cn/solutions/services/hcs-professional-services/consulting-training-services)

---

## 附录 C：常见问题 FAQ

**Q1：没有 Stack 内网，如何备课？**\
按 [§0.1](#01-无-stack-环境自学目标与边界)：Docker 练通用约定；**公有云**练 SWR/OBS（API 同族，换
endpoint）；可选 DevStack 补 OpenStack IaaS。**不能替代**内网 IAM、ServiceStage 发布、ManageOne
发放与全链路 E2E。动手步骤见 [第三部分](#第三部分无-stack-环境--自学实验跟练手册)。

**Q2：Java 栈学员如何对齐？**\
Dockerfile 用多阶段 Fat Jar；OBS 用 esdk-obs-java；探针与 env 契约与 Python 相同。

**Q3：ServiceStage 为何不讲？**\
同期平台课已覆盖；本课只交付镜像、探针、环境变量清单。

**Q4：镜像扫描、多架构？**\
本课点到为止；扩展见 SWR 镜像安全扫描文档与 `docker buildx build --platform`。

**Q5：OBS 和 MinIO 一样吗？**\
API 模型类似 S3；生产 Stack 用华为 SDK + 行内 endpoint，不要用 MinIO 客户端直打 OBS。

---

## 附录 D：推荐阅读顺序（自学 1 周）

| 天 | 内容                          | 文档                                                                                                     |
| -- | ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1  | Docker 基础 + 第一晚 Demo 1–3 | 本讲义 1.2–1.4 + [Docker Docs](https://docs.docker.com/)                                                 |
| 2  | SWR 推送 Demo 4               | 本讲义 1.5 + [SWR 用户指南（推送镜像）](https://support.huaweicloud.com/usermanual-swr/swr_01_0011.html) |
| 3  | OBS SDK Demo 5–6              | 本讲义 2.2 + [OBS Python SDK](https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_0501.html)      |
| 4  | 预签名 + 发布清单             | 本讲义 2.1、2.3                                                                                          |
| 5  | 端到端 Demo 8 + AI 复核       | 本讲义 2.5 + [第三部分](#第三部分无-stack-环境--自学实验跟练手册)                                        |

---

## 附录 E：扩展参考资料索引

| 主题                        | 链接                                                                                              |
| --------------------------- | ------------------------------------------------------------------------------------------------- |
| API Explorer / CLI 示例     | https://console.huaweicloud.com/apiexplorer/                                                      |
| SWR 产品文档                | https://support.huaweicloud.com/swr/index.html                                                    |
| OBS Python SDK              | https://support.huaweicloud.com/sdk-python-devg-obs/obs_22_0501.html                              |
| Python SDK（通用）          | https://github.com/huaweicloud/huaweicloud-sdk-python-v3                                          |
| OpenStack CLI               | https://github.com/openstack/python-openstackclient                                               |
| Stack 培训（企业 E2E 环境） | https://e.huawei.com/cn/solutions/services/hcs-professional-services/consulting-training-services |
| 开发者云实验（公有云）      | https://developer.huaweicloud.com/                                                                |
| AI 编程姊妹篇               | [we-know-python-coding-with-ai.md](we-know-python-coding-with-ai.md)                              |

_讲义版本：2026-06。_
