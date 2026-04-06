# AI 大模型赋能软件开发

## 注意 ⚠️

- _斜体表示引用或补充说明_
- **未经允许，禁止转载**

本教案教授 AI 大模型赋能软件开发的一般原理、方法论和工具链。AI 大模型可以是私有化部署，也可以是在线服务。串联 **IDE / CLI Router / OpenClaw（或同类 Agent
工具）** 的工程化使用。重心在**可复现的安装配置、连通性验证与全链路实战**。

## 课程目录

| 日程    | 时间 | 课程模块                 | 内容                                                             |
| ----- | -- | -------------------- | -------------------------------------------------------------- |
| 第 1 天 | 上午 | 原理 + 模型接入            | [1.1 课程定位与日程说明](#11-课程定位与日程说明)                                 |
|       |    |                      | [2.1 Agent、Harness 与 Agent 循环](#21-agentharness-与-agent-循环原理)  |
|       |    |                      | [2.2 Vibe Coding 与 Spec Coding](#22-vibe-coding-与-spec-coding) |
|       |    |                      | [2.3 Spec Coding 端到端落地](#23-spec-coding-端到端落地实操清单)             |
|       |    |                      | [3.1 大模型与 AI 编码扫盲（压缩）](#31-大模型与-ai-编码扫盲压缩)                     |
|       |    |                      | [3.2 在线 API 端到端走通](#32-在线-api-端到端走通)                           |
|       |    |                      | [3.3 私有化部署（可选 Demo）](#33-私有化部署可选-demo)                         |
|       |    |                      | [3.4 使用入门与课堂练习](#34-使用入门与课堂练习)                                 |
| 第 1 天 | 下午 | IDE / Router / Agent | [4.1 IDE 对接模型服务](#41-ide-对接模型服务)                               |
|       |    |                      | [4.2 OpenClaw、Router 与冒烟路径](#42-openclawrouter-与冒烟路径)          |
| 第 2 天 | 上午 | 全栈开发实战（技能 + 数据）      | [5.1 AI 助手技能（Skills）开发入门](#51-ai-助手技能skills开发入门)               |
|       |    |                      | [5.2 Python 数据分析与自动化](#52-python-数据分析与自动化)                     |
| 第 2 天 | 下午 | 云原生与高阶实战             | [6.1 前后端一体化快速开发](#61-前后端一体化快速开发)                               |
|       |    |                      | [6.2 云原生与微服务架构开发](#62-云原生与微服务架构开发)                             |
|       |    |                      | [6.3 高阶技巧与工作流复盘](#63-高阶技巧与工作流复盘)                               |
| 结课    | —  | 自查与扩展阅读              | [7.1 学员自查清单](#71-学员自查清单)                                       |
|       |    |                      | [7.2 延伸阅读与课程衔接](#72-延伸阅读与课程衔接)                                 |
|       |    |                      | [7.3 扩展阅读：AI 编程新进展与工具](#73-扩展阅读ai-编程新进展与工具)                    |
|       |    |                      | [7.4 讲义维护说明（给讲师）](#74-讲义维护说明给讲师)                               |

---

## 1. 课程总览

[返回目录](#课程目录)

### 1.1 课程定位与日程说明

[返回目录](#课程目录)

**课程定位**：面向一线开发、测试与运维工程技术人员，完成「**模型可连（优先在线 API）** → **IDE/Agent 可连** → **Spec/Vibe 选型** →
**技能与场景复制**」的闭环。课程假设学员具备常规命令行、一门后端语言（以 Python 为主）与基础 Web 概念；不展开 Transformer 数学推导。

**教学目标（两天结束后，学员应能）**：

1. **说清楚**：Agent 与 Harness 的概念和分工；代码大模型能力边界；在线 API 与私有化路线的取舍（合规、成本、运维、效果）。
2. **做得出**：任选一家**在线 API**（如 MiniMax / 通义千问 / GLM / Kimi / DeepSeek 云等）完成**注册 → 鉴权 → 最小请求 → IDE
   或脚本验证**；有条件时跟完**私有化最短 Demo**（不要求全员有 GPU）。
3. **接得上**：VS Code / Cursor 等指向可用端点；理解 **CLI Router / OpenAI 兼容网关**；完成 **OpenClaw 或同类 Agent**
   的冒烟路径（读仓库、改文件或跑一条命令）。
4. **方法论**：能说明 **Vibe Coding** 与 **Spec Coding** 的适用场景；能按 **S-R-T-P** 写一页 Spec 并驱动 AI 分任务落地。
5. **扩展开**：最小 Skill（工具契约）+ 数据分析 / 全栈 / 云原生脚手架的人机协同迭代。

**日程与节奏建议**：

- 第 1 天上午：**原理压缩讲清**（Agent/Harness、Spec/Vibe、Spec 端到端清单）+ **在线 API 全员走通** + 私有化**演示或录像**（15–30
  分钟量级，视客户环境而定）。
- 第 1 天下午：**IDE + Router + Agent** 真值闭环。
- 第 2 天：**Spec 驱动下的**技能与场景（数据、Web、云原生），复盘个人工作流。

**教学原则**（与 `we-know-python.md` 中 AI 辅助编程观一致）：

- **人主导决策，模型辅助执行**：架构、安全、合规、上线责任在人；对模型输出做必要性与完备性校验。
- **规范优先于一次性代码**：Spec、OpenAPI、环境变量约定、验收标准应可版本化；与 **Spec Coding** 一致。

### 1.2 环境与物料清单

[返回目录](#课程目录)

**必备（在线 API 路线）**：

- 可访问公网控制台的账号（由组织方指定 1–2 家供应商做标准演示，其余列表供自选）。
- **API Key** 仅放本机环境变量或密钥管理，**禁止进仓库与截图外传**。
- **Python 3.10+**、`httpx` 或 `openai` 兼容客户端；可选 `curl`。

**软件**：

- IDE：**VS Code**、**Cursor**
- CLI：**Cloud Code Router**
- 其它：**OpenClaw** 等

**讲义与代码仓库**（建议组织方提供）：

- 各厂商 **base URL、鉴权头、模型名** 对照表（见 [3.2](#32-在线-api-端到端走通)）。
- 最小 `curl` 与 `hello_llm.py` 模板。
- 空项目模板：含 `AGENTS.md` 或 `specs/` 目录占位，便于 Spec 练习。

---

## 2. 原理篇：Agent、Harness 与编程范式（Spec / Vibe）

[返回目录](#课程目录)

_下列内容与
[we-know-python-coding-with-ai.md §3.1「Agent
是什么」](we-know-python-coding-with-ai.md#31-agent-是什么概念组成与实现)及「两种 AI
编程范式」一致，本教案压缩为课堂版；学员课后可回姊妹篇查细节与代码。_

### 2.1 Agent、Harness 与 Agent 循环（原理）

[返回目录](#课程目录)

**2.1.1 两个容易混淆的概念**

| 概念       | 含义                    | 例子                     |
| -------- | --------------------- | ---------------------- |
| AI 大模型编程 | 用 LLM 帮你写代码（补全、对话、生成） | Cursor、Copilot 生成函数    |
| 实现 Agent | 构建能自主感知、决策、行动的系统      | 读仓库、改代码、跑测试的 CLI Agent |

本课程**侧重前者**：用 AI 编程工具提高写代码效率，同时也讲述原理，帮助同学们理解 **Agent 系统**在工程里如何落地（工具、权限、观测）。

**2.1.2 定义与 Harness**

- 经典定义（Russell & Norvig）：

> **Agent 是一个能够感知环境并采取行动以实现目标的系统。**

- 四要素：

```
Agent = 感知(Perception) + 决策(Decision) + 行动(Action) + 目标(Goal)
```

- **强化学习传统**：Agent 在环境里通过试错学策略（如 AlphaGo）。
- **大模型时代**：**Agent = 预训练模型（决策核心）+ Harness（感知与行动环境）**。\
  **Harness** 负责：读文件、执行命令、调用 API、管理消息历史、工具注册与安全策略。\
  **Cursor、Claude Code、OpenClaw** 等本质是「模型 + 不同形态的 Harness」。

**2.1.3 现代 Agent 组成（课堂版框图）**

```
┌─────────────────────────────────────────────────────┐
│                    Agent 系统                        │
│  ┌─────────────┐         ┌─────────────┐            │
│  │   感知层    │────────▶│   决策层    │            │
│  │ Perception  │         │  (LLM)      │            │
│  └─────────────┘         └─────────────┘            │
│                                 │                    │
│                                 ▼                    │
│                          ┌─────────────┐            │
│                          │   行动层    │            │
│                          │ 工具 / Shell │            │
│                          └─────────────┘            │
│  辅助：记忆、工具注册表、权限、日志与可观测性              │
└─────────────────────────────────────────────────────┘
```

**2.1.4 Agent 主循环（伪代码）**

与姊妹篇一致，核心是：**LLM 决策 → 是否调用工具 → 执行工具 → 结果写回消息 → 再决策**。

```python
def agent_loop(messages, tools, max_iterations=10):
    for _ in range(max_iterations):
        response = llm.chat(messages, tools=tools)
        if response.stop_reason != "tool_use":
            return response.content
        tool_results = execute_tool_calls(response.tool_calls)
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
    return "达到最大迭代次数，任务未完成"
```

**2.1.5 为什么需要 Agent**

| 需求   | 传统方案   | Agent 方案       |
| ---- | ------ | -------------- |
| 复杂任务 | 多脚本拼接  | 单一循环内规划 + 工具执行 |
| 交互   | 表单与命令行 | 自然语言 + 可执行动作   |

**一句话**：让模型做**决策**，让 Harness 做**执行与约束**，让人保留**目标与验收**。

**2.1.6 与本课工具链的对应**

| 工具              | 类型        | 说明                            |
| --------------- | --------- | ----------------------------- |
| **Cursor**      | IDE Agent | 仓库上下文、编辑、重构                   |
| **Claude Code** | CLI Agent | 终端驱动任务流                       |
| **OpenClaw**    | CLI Agent | 多模型、本地化与国产模型友好                |
| **Router**      | API 网关    | OpenAI 兼容 `base_url` 统一接入多家后端 |

完整对比表与安装链接见
[we-know-python-coding-with-ai.md §3.1.6](we-know-python-coding-with-ai.md#316-ai-编程工具如何高效开发-agent)。

### 2.2 Vibe Coding 与 Spec Coding

[返回目录](#课程目录)

_来源：[we-know-python-coding-with-ai.md](we-know-python-coding-with-ai.md)「两种 AI 编程范式」一节。_

**Vibe Coding（氛围编码）**

"Vibe Coding" 一词由 Andrej Karpathy 在 2025 年提出，指**以对话为主**的编程方式：

- **特点**：自然语言描述需求 → AI 生成代码 → 看效果 → 继续对话迭代。
- **适合**：快速原型、探索新技术、个人或小范围试错。
- **风险**：结构漂移、难以审查、大项目易欠技术债。

**Spec Coding（规格编码）**

- **特点**：先写**可验收的规格**（需求、约束、接口、测试标准），再让 AI **按 Spec 实现**，人按 Spec **审查**。
- **适合**：团队协作、需要可追溯与 Code Review 的工程交付。
- **工具**：Cursor、Claude Code、OpenClaw、配合仓库内的 Spec 文件与 CI。

**对比（课堂版）**

| 维度 | Vibe Coding | Spec Coding  |
| -- | ----------- | ------------ |
| 驱动 | 对话          | 规格 / 契约      |
| 场景 | 探索、原型       | 交付、协作、维护     |
| 质量 | 依赖模型与提示     | 依赖 Spec 与验收  |
| 迭代 | 继续聊         | 改 Spec → 再实现 |

> **建议**：探索阶段用 Vibe；**进入多人协作或上线路径时切换到 Spec**。

### 2.3 Spec Coding 端到端落地（实操清单）

[返回目录](#课程目录)

**2.3.1 四要素 S-R-T-P**（与姊妹篇一致）

| 要素          | 含义      | 示例                             |
| ----------- | ------- | ------------------------------ |
| **S**pecs   | 要做什么    | 解析某格式日志，输出状态码分布、Top IP         |
| **R**ules   | 边界与规约   | Python 3.10+、禁止某依赖、错误处理策略、安全约束 |
| **T**asks   | 当前一步    | 先实现 `parse_log_line()`，附 3 条单测 |
| **P**rompts | 如何告诉 AI | 把 S-R-T 组装成一条可执行指令（含验收命令）      |

**流程**：**Specs → Rules → Tasks → Prompts**；每完成一个 Task，用**命令或测试**验收后再开下一 Task。

**2.3.2 端到端落地步骤（建议写进团队模板）**

1. **立项一页纸 Spec**：背景、用户故事、非目标（不做什么）、成功标准（可测）。
2. **技术规格**：目录结构、公开 API（可先用 OpenAPI 草稿）、数据流、环境变量表。
3. **任务拆解**：每个 Task 对应小 PR 或小提交；依赖顺序明确。
4. **Prompt 模板**：固定「上下文 + 当前 Task + 验收命令 + 禁止项」。
5. **自动化门槛**：每个 Task 至少绑定 `lint` / `test` / `build` 之一通过才可合并。
6. **复盘**：Spec 与实现偏差记入「ADR 或变更记录」，更新 Rules。

**2.3.3 与第 2 天实战的衔接**

- **5.1 Skills**：工具 I/O 即小型 **Spec**。
- **6.1 全栈**：**OpenAPI 契约先行** 即 Spec Coding 的标准用法。

**2.3.4 与业界工具的对照（扩展）**

- GitHub **Spec Kit** 将「规格 → 计划 → 任务 → 实现」做成可与多种 Agent 配合的流程，见 [7.3](#73-扩展阅读ai-编程新进展与工具)。

---

## 3. 第一天上午：在线 API 为主、私有化可选

[返回目录](#课程目录)

### 3.1 大模型与 AI 编码扫盲（压缩）

[返回目录](#课程目录)

**目标**：约 20–30 分钟，与第 2 节理论互补，不重复展开。

- **输入 / 输出**：上下文窗口内文本进，采样续写出代码、JSON、工具调用等。
- **边界**：擅长样板与转换；弱于隐式业务规则与无文档遗留系统「猜意图」。
- **在线 vs 私有化**：在线低运维、注意合规与密钥；私有化数据可控、运维与算力成本高。详见第 1 天下午 IDE 配置中的**数据出境**提醒。

### 3.2 在线 API 端到端走通

[返回目录](#课程目录)

**本节目标**：每位学员任选一家（或跟讲师统一一家）完成 **控制台 → Key → 最小 HTTP 请求 → 打印回复**；再可选配置到 IDE。

**通用步骤（OpenAI 兼容类）**

1. 在厂商控制台**创建 API Key**，导出为环境变量（示例名 `LLM_API_KEY`，勿提交代码）。
2. 查文档确认 **`base_url`**（是否含 `/v1`）、**鉴权头**（`Authorization: Bearer ...` 或厂商自定义）、**模型 ID 字符串**。
3. **冒烟请求**（二选一）：
   - `curl` POST chat/completions（或厂商等价路径）；
   - Python：`OpenAI(base_url=..., api_key=...)` 或 `httpx` 直连。
4. **成功标准**：HTTP 200，返回中可见模型文本回复；错误时保存**完整错误 JSON** 用于排障课。
5. **IDE**：在 Cursor / VS Code 插件中填入同一 `base_url` + `model` + Key，发一条对话测试。

**国内常用在线 API（课堂对照表）**

_链接与产品线以厂商当前文档为准；讲课时应用「控制台实际菜单」校对。_

| 厂商 / 品牌        | 典型控制台 / 文档入口                                            | 备注                |
| -------------- | ------------------------------------------------------- | ----------------- |
| **MiniMax**    | [platform.minimaxi.com](https://platform.minimaxi.com/) | 长文本等能力因模型而异       |
| **通义千问（阿里云）**  | [dashscope.aliyun.com](https://dashscope.aliyun.com/)   | 模型名与地域以控制台为准      |
| **智谱 GLM**     | [open.bigmodel.cn](https://open.bigmodel.cn/)           | 注意 OpenAPI 兼容端点说明 |
| **Kimi（月之暗面）** | [platform.moonshot.cn](https://platform.moonshot.cn/)   | 上下文长，注意计费与限流      |
| **DeepSeek**   | [platform.deepseek.com](https://platform.deepseek.com/) | 编程场景性价比高，可作默认演示   |

**课堂练习**：填写「API 走通记录表」：厂商、`base_url`、模型名、一条成功请求的截图或脱敏日志、失败时错误码与原因。

**排障速查**：Key 无效、模型名拼写、`base_url` 多写路径、公司代理、地域限制、余额与配额。

### 3.3 私有化部署（可选 Demo）

[返回目录](#课程目录)

**最短路径**

1. 硬件：GPU 与驱动可见性（`nvidia-smi`，国产 GPU 有对应命令）。
2. 交付形态：官方容器或课程 Compose；**监听地址、卷、模型路径**三要素。
3. **验收**：本机 `curl` 推理接口；内网另一台可访问（若需要）。
4. **安全**：不外挂公网、密钥与内网 ACL、日志不落敏感提示词。

下面按**工程可用的开源编程模型**（原则上不用 7B 级「玩具」做主模型）给出 **vLLM 端到端主路径**，并对比
**SGLang**、**Ollama**。显存与命令以常见单节点为基准；**实际以你安装的 vLLM/SGLang 版本文档为准**（见
[vLLM 文档](https://docs.vllm.ai/)、[SGLang 安装与 Docker](https://sgl-project.github.io/get_started/install.html)）。

- **dense 32B 档通常不够**作为「对标顶级闭源、复杂仓库 + 长链路 Agent /
  SWE」的**唯一**内网基座——它更适合：**算力受限时的折中**、**中等复杂度编码**、或课堂**先把 serving / IDE / Router 链路跑通**。
- **要追开源能力上限**（而非仅「能跑」），应把讲义里的**目标模型**抬到：
  - **阿里最新一代编码 Agent 向模型**：[**Qwen3-Coder-Next**](https://huggingface.co/Qwen/Qwen3-Coder-Next)（约
    **80B 总参数、约 3B 激活/token** 的 MoE，256K 上下文；技术报告
    [arXiv:2603.00729](https://arxiv.org/abs/2603.00729)）。
  - **智谱旗舰开源线**：以 Hugging Face
    [**zai-org/GLM-5**](https://huggingface.co/zai-org/GLM-5)、[**zai-org/GLM-5-FP8**](https://huggingface.co/zai-org/GLM-5-FP8)
    等模型卡为准——属于**大规模 MoE 旗舰**（总参、激活参、许可证与下载条款**以官方 Model Card 为准**）。
- **落地分工建议**：**演示链路与全员练习**仍可用 **AWQ 32B / 30B-A3B** 降低门槛；**内网标杆与效果预期**应对齐 **Qwen3-Coder-Next /
  GLM-5** 或**在线旗舰 API**。

#### 编程向模型推荐（开源、可私有化）

| 档位                           | 模型（Hugging Face 示例 ID）                                                   | 定位与硬件粗算（含权重 + KV 余量，随上下文与并发上浮）                                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **旗舰 / Agent 向（优先讲这个）**      | **Qwen/Qwen3-Coder-Next**                                                | 面向 **coding agents**；总参约 **80B 级、激活约 3B/token**（见模型卡）。**BF16 权重体积大**，单节点常需 **多卡张量并行 + 大显存** 或依赖 **vLLM/SGLang 支持的 FP8/量化变体**；具体以引擎版本与 Qwen 发布的权重分支为准。 |
| **旗舰 / 智谱系**                 | **zai-org/GLM-5**、**zai-org/GLM-5-FP8** 等                                | **大规模 MoE 开源权重**，面向 Agent / 长上下文与复杂任务；**显存与卡数通常明显高于** Next/32B 档，多属**多卡或机房级**规划，以官方部署说明为准。                                                            |
| **中单卡可教（新一代但轻一档）**           | **Qwen/Qwen3-Coder-30B-A3B-Instruct**                                    | MoE，激活约 3.3B；**FP16/BF16 全量**常见为 **60–80GB 单卡**或 **2×40GB TP**；有量化权重时或可压到 **24–48GB** 档（视仓库与引擎支持）。                                                    |
| **legacy / 基线对照（仍实用但不代表上限）** | **Qwen/Qwen2.5-Coder-32B-Instruct** 与 **Qwen2.5-Coder-32B-Instruct-AWQ** | **2.5 代**：文档与范例多，适合对照实验。**BF16**：**2×40GB TP** 或 **80GB 单卡**；**24GB 单卡**优先 **AWQ** + `vllm serve ... --quantization awq`。                             |
| **经典对照**                     | **deepseek-ai/deepseek-coder-33b-instruct**                              | 与 32B dense 同级量级：**80GB 或多卡 TP**；量化版按 HF 与 vLLM 支持情况选用。                                                                                               |

_说明：**Qwen3-Coder-Next / GLM-5** 类旗舰更适合「**效果标杆**」与**有条件的讲师 Demo**；两日课**全员跟做**默认题仍可保留 **AWQ 32B 或
30B-A3B**，但须在口头与 PPT 上与**天花板模型**对齐预期，避免学员以为「32B = 企业内唯一正确答案」。_

#### 软件与驱动基线（讲师机 / 实验机）

- **OS**：Ubuntu 22.04 / 24.04 LTS（或等价服务器发行版）。
- **GPU**：NVIDIA，驱动与 **NVIDIA Container Toolkit** 就绪；`nvidia-smi` 正常。
- **CUDA / PyTorch**：与当前 **vLLM 发行说明**一致（不同 vLLM 版本绑定不同 CUDA；用 Docker 可少踩坑）。
- **Hugging Face**：若模型需许可，提前准备 **`HF_TOKEN`**（勿写入仓库）。
- **磁盘**：模型权重 **数十 GB～百 GB**；缓存目录建议单独卷（如 `/data/hf`）。

#### 方案一：vLLM 端到端（OpenAI 兼容，推荐主演示）

vLLM 对外提供 **OpenAI 风格 HTTP API**，默认监听 **`http://0.0.0.0:8000`**，路径前缀 **`/v1`**（详见
[vLLM Quickstart：OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/getting_started/quickstart.html#openai-compatible-server)）。

**1）安装（二选一）**

- **pip/uv（本机虚拟环境）**：按
  [vLLM Installation](https://docs.vllm.ai/en/latest/getting_started/installation.html) 安装与当前 CUDA
  匹配的 wheel；然后使用 CLI `vllm serve ...`。
- **Docker（推荐课堂复现）**：使用官方镜像（名称以文档为准，常见为 **`vllm/vllm-openai`** 一类），挂载 HF 缓存目录，例如：

```bash
# 默认：全员易跟做 —— Qwen2.5-Coder-32B AWQ（legacy 档，非能力上限）
docker run -d --name vllm-coder --gpus all --shm-size 16g \
  -p 8000:8000 \
  -v /data/hf-cache:/root/.cache/huggingface \
  -e HF_TOKEN="你的token" \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-Coder-32B-Instruct-AWQ \
  --quantization awq \
  --host 0.0.0.0 --port 8000 \
  --max-model-len 8192
```

_镜像名、entrypoint 与参数以 [vLLM Docker 文档](https://docs.vllm.ai/en/latest/deployment/docker.html) 为准。_

**有条件时（能力 Demo，取代「32B 就够」的预期）**：改为 **Qwen3-Coder-Next** 或 **GLM-5（FP8 等）**，通常需要 **更大显存或多卡
`--tensor-parallel-size`**，有时还需 **`--trust-remote-code`** 或引擎指定的量化参数——**以当前 vLLM 版本 + 模型卡中的 Serving
说明为准**，例如：

```bash
# 示意：多卡跑 Next（TP 大小按显存实测调整；model 名以 HF 为准）
vllm serve Qwen/Qwen3-Coder-Next \
  --tensor-parallel-size 2 \
  --host 0.0.0.0 --port 8000 \
  --max-model-len 65536
```

**多卡张量并行示例（2×GPU 跑 Qwen2.5 dense 32B BF16，作 legacy 对照）**：

```bash
vllm serve Qwen/Qwen2.5-Coder-32B-Instruct \
  --tensor-parallel-size 2 \
  --host 0.0.0.0 --port 8000
```

**2）可选鉴权**

启动时传入 **`--api-key your-secret`**（或环境变量 **`VLLM_API_KEY`**），请求头需带
`Authorization: Bearer your-secret`。

**3）拉起后测试**

```bash
# 列出模型
curl -s http://127.0.0.1:8000/v1/models | head

# Chat Completions（model 字符串与 vllm serve 的 --model 一致）
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ",
    "messages": [
      {"role": "system", "content": "You are a coding assistant."},
      {"role": "user", "content": "用 Python 写一个带类型标注的函数，把 CSV 读成 list[dict]。"}
    ],
    "temperature": 0.2,
    "max_tokens": 512
  }'
```

若服务端加载的是 **Qwen3-Coder-Next** / **GLM-5** 等，把上面 JSON 里的 **`model` 改成与 `vllm serve --model` 完全相同**的
HF 路径即可。

**4）对接 IDE / Router**

- **Base URL**：`http://<内网IP>:8000/v1`
- **API Key**：若未启用可填占位（部分客户端用 `EMPTY`）；若启用则填与 `--api-key` 一致。
- **Model**：与 `vllm serve` 的 `--model` 字符串一致。

**5）验收标准（课堂）**

- `GET /v1/models` 返回 200；
- `chat/completions` 返回可执行级代码片段且无持续 OOM；
- 同网段另一台机器仅能按 ACL 访问（若做内网演示）。

#### 方案二：SGLang（高性能服务，OpenAI 兼容）

[SGLang](https://github.com/sgl-project/sglang) 同样提供 **OpenAI 兼容 API**（文档示例端口常为 **30000**）。适合与 vLLM
**对照评测延迟与吞吐**，部署形态与 vLLM 类似：**Docker + GPU + 挂载 HF 缓存**。

**Docker 示意**（`--model-path` 可换为 **Qwen3-Coder-Next** / **GLM-5** 等，以 SGLang 对该权重的支持列表为准；镜像名以官方为准，如
`lmsysorg/sglang:latest`）：

```bash
docker run --gpus all --shm-size 32g --ipc=host \
  -p 30000:30000 \
  -v /data/hf-cache:/root/.cache/huggingface \
  -e HF_TOKEN="你的token" \
  lmsysorg/sglang:latest \
  python3 -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-Coder-32B-Instruct-AWQ \
    --host 0.0.0.0 --port 30000
```

**测试**：`curl http://127.0.0.1:30000/v1/models` 或打开文档中给出的 **`/docs`、`/openapi.json`**（以当前版本为准）。IDE 中将
Base URL 设为 **`http://<host>:30000/v1`**。

与 vLLM 的选型一句话：**两者都能 serving；同一模型在相同卡上请以实测吞吐与显存占用为准，不先验谁更快**。

#### 方案三：Ollama（本机拉模型、快速试用）

[Ollama](https://ollama.com/) 侧重 **一条命令拉取 Modelfile、本地运行**，对学员友好，但**默认生态是 Ollama 自有 API**；若要对接只认
OpenAI 协议的 IDE，往往需要 **额外网关/适配层**。

**典型流程**：

1. 安装 Ollama（Linux/macOS/Windows 按官网）。
2. 选择**较大编程模型**标签（名称随库更新；**能力优先**时优先查是否已提供与 **Qwen3-Coder-Next** 对应的标签，其次 **`qwen3-coder:30b`**
   等；**qwen2.5-coder:32b** 属旧代但仍常用于本地试跑。均以 [Ollama 模型库](https://ollama.com/library) 实时列表为准）：

```bash
# 示例之一（标签请用 ollama.com 上实际存在的 name:tag）
ollama pull qwen2.5-coder:32b
ollama run qwen2.5-coder:32b
```

3. **本机探测**：另开终端 `curl http://127.0.0.1:11434/api/tags` 或按官方 REST 说明发 **`/api/chat`**。
4. **课堂定位**：适合「**先证明大模型编程可用**」与**无 Docker 环境**的演示；正式内网服务仍建议 **vLLM/SGLang** 统一 OpenAI 接口。

#### 三种方案对比

| 维度               | vLLM    | SGLang | Ollama        |
| ---------------- | ------- | ------ | ------------- |
| OpenAI 兼容 HTTP   | 原生主路径   | 支持     | 需适配或侧车        |
| 大模型工程化（TP、量化、多卡） | 强       | 强      | 偏单机快捷         |
| 课堂推荐             | **主演示** | 选做对比   | **快速体验 / 备选** |

**与在线 API 的关系**：私有化推理服务同样可通过 **OpenAI 兼容适配** 接到 IDE 与 Router；课堂强调**接口形态统一**降低切换成本。

### 3.4 使用入门与课堂练习

[返回目录](#课程目录)

- **Prompt 习惯**：意图 + 约束 + 输出格式 + 验收方式（与旧版 2.3 节相同，课堂快速带过）。
- **最小闭环**：需求 → 生成 → 运行/测试 → 错误栈回灌 → 修正。
- **第一天上午收尾作业**：用已走通的 API 或 IDE 完成「一个小脚本 + README 一条运行命令」，主题由组织方指定。

---

## 4. 第一天下午：IDE 与 Router / Agent

[返回目录](#课程目录)

### 4.1 IDE 对接模型服务

[返回目录](#课程目录)

**目标**：对接**第 3.2 节已验证的在线端点**或**私有化 Demo 端点**；不再默认「必须私有化」。

- **VS Code**：OpenAI 兼容类插件配置 `base_url`、模型名、Key；注意公司代理与 `NO_PROXY`。
- **Cursor**：自定义模型 / Override OpenAI Base URL；**`.cursorignore`** 排除密钥与大二进制；说明隐私模式与索引范围。

**练习**：同一任务（如加类型标注 + 单测）用对话完成，并记录是否符合 **Spec**（若上午已写微型 Spec）。

### 4.2 OpenClaw、Router 与冒烟路径

[返回目录](#课程目录)

**目标**：理解 **Agent 循环**（第 2.1 节）在 CLI 中的体现；**Router** 统一多后端；完成一次冒烟。

1. **Router**：配置 `base_url`、`api_key`、模型别名；可选同时指向在线 API 与内网私有化。
2. **OpenClaw（或讲义选定 CLI Agent）**：安装与登录按官方文档；环境变量指向 Router 或直连某厂商 API。
3. **冒烟**：在示例仓库中执行「读 README → 改一小处 → 运行 `pytest` 或 `npm test`」之一，日志无权限事故。

**安全**：默认最小可写目录、敏感命令需确认；生产需审计。

**第一天小结**：在线 API ✓、IDE ✓、Agent 冒烟 ✓；布置预习：带一个想自动化的「小任务」写半页 Spec（S-R-T-P）。

---

## 5. 第二天上午：技能与数据分析

[返回目录](#课程目录)

### 5.1 AI 助手技能（Skills）开发入门

[返回目录](#课程目录)

**说明**：Skills 可对应 MCP 工具、CLI 子命令或内部微服务；**输入输出 Schema 即 Spec 的缩小版**。

- **规范**：单一职责、JSON 或固定字段 I/O、超时与错误码、权限白名单。
- **实战**：文档片段生成 / `ruff` 封装 / 静态检查封装三选一，要求 `README` + 示例请求/响应。
- **集成**：在 OpenClaw 或 IDE Agent 中调用技能，完成闭环。

**作业**：一组交付一个技能 + 调用日志或录屏。

### 5.2 Python 数据分析与自动化

[返回目录](#课程目录)

- 先人工写「字段与异常类型」表，再让 AI 生成 `pandas` 流水线；强调可解释与可验收。
- 规模：向量化、分块读、`dtype`；可视化需核对**统计口径**。
- **关联**：[we-know-python-coding-with-ai.md](we-know-python-coding-with-ai.md) 中对象模型与异常章节，便于写成可维护脚本。

---

## 6. 第二天下午：全栈与云原生

[返回目录](#课程目录)

### 6.1 前后端一体化快速开发

[返回目录](#课程目录)

- **Spec 驱动**：**OpenAPI 先行的 CRUD**；前后端从契约并行生成再对齐。
- 前端：设计令牌与目录约定；后端：校验、错误码、`request_id` 日志。

**课堂实战**：最小全栈 + 中途改需求一次，考察「改 Spec → 再生成 → 再测」是否成立。

### 6.2 云原生与微服务架构开发

[返回目录](#课程目录)

- Dockerfile 多阶段、非 root；K8s 最小清单与探针；CI 阶段拆分；密钥不进库。
- 微服务：契约版本、超时重试熔断的**假设写进 Spec**。

### 6.3 高阶技巧与工作流复盘

[返回目录](#课程目录)

- Bug：最小复现 + 观测数据 + 分诊式提示；遗留系统：小步、可回滚、先补测试再重构。
- **工作流**：每人写一页「默认工作流」——何时 Vibe、何时 Spec、谁 Review、哪些命令是门禁。

---

## 7. 结课、自查与扩展阅读

[返回目录](#课程目录)

### 7.1 学员自查清单

[返回目录](#课程目录)

- [ ] 至少一家**在线 API** 端到端走通（或组织指定供应商），有脱敏记录
- [ ] IDE 指向正确端点，**仓库无密钥**
- [ ] Router / OpenClaw（或同类）冒烟路径可重复
- [ ] 能口述 **Agent vs Harness**，并画出一轮 Agent 循环
- [ ] 完成一页 **S-R-T-P** Spec，并对应至少一个可运行 Task
- [ ] （可选）观看或跟做私有化 Demo 步骤，能说出验收命令
- [ ] 技能 / 全栈 / 云原生任一场景有可运行说明与最小验证

### 7.2 延伸阅读与课程衔接

[返回目录](#课程目录)

- [we-know-python.md](we-know-python.md) — Python 基础与 AI 时代学习观
- [we-know-python-coding-with-ai.md](we-know-python-coding-with-ai.md) — LLM API、工具调用、Agent
  循环完整代码与第三天项目线

### 7.3 扩展阅读：AI 编程新进展与工具

[返回目录](#课程目录)

_下列条目用于讲师备课与学员自学，**链接以官方为准**；产品迭代快，需自行核对版本与条款。_

| 方向                              | 说明                                         | 入口示例                                                                                                                                                                                                                                                                                                 |
| ------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Spec-driven + Agent**         | 将规格、计划、任务与编码 Agent 衔接的可复现流程                | [GitHub Blog：Spec-driven development with AI](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit)、开源仓库 [github/spec-kit](https://github.com/github/spec-kit)、文档站 [github.github.io/spec-kit](https://github.github.io/spec-kit/) |
| **MCP（Model Context Protocol）** | 用标准协议暴露工具与资源，供多编辑器 / Agent 消费              | [modelcontextprotocol.io](https://modelcontextprotocol.io/)                                                                                                                                                                                                                                          |
| **终端 Agent / 多模型**              | 与 OpenClaw、Claude Code、Aider 等同类：长任务、仓库级编辑 | 各项目官方 README（选型看团队习惯与合规）                                                                                                                                                                                                                                                                             |
| **评测与基准**                       | 理解「模型在编码任务上测什么」有助于设验收标准                    | SWE-bench 等公开基准（搜索最新论文与榜单）                                                                                                                                                                                                                                                                           |
| **安全与供应链**                      | Agent 自动执行命令与依赖安装带来的风险                     | 组织内部安全基线 + OWASP LLM / 供应链相关导读                                                                                                                                                                                                                                                                       |

**讨论题（可选）**：「Vibe 何时必须收束为 Spec？」「Spec Kit 的四阶段与 S-R-T-P 如何映射到你司模板？」
