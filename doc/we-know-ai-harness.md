# Coding Agent Engineering & Harness 平台实战讲义

## 注意 ⚠️

- _斜体表示引用或延伸阅读_
- **未经允许，禁止转载**
- 本讲义对应课纲
  [`20260618-AI-Coding.md`](../../training-python/Case/DongFangRuiTong/dagang/20260618-AI-Coding.md)（2
  天 × 6 h）
- 默认学员已具备 Python 基础、LLM API 调用经验；**不重复** AI 大模型原理与 MCP 协议入门（见姊妹篇
  [`we-know-ai-agent.md`](we-know-ai-agent.md)、[`we-know-ai-coding.md`](we-know-ai-coding.md)）

---

## 课程目录

| 日期  | 时段        | 主题                     | 章节                                                       |
| ----- | ----------- | ------------------------ | ---------------------------------------------------------- |
| Day 1 | 09:00–12:00 | Agent 运行内核（上）     | [1.1 核心观](#11-coding-agent-engineering-核心观)          |
|       |             |                          | [1.2 状态持久化与恢复](#12-状态持久化与恢复机制)           |
| Day 1 | 14:00–17:00 | Agent 运行内核（下）     | [1.3 上下文压缩与记忆](#13-上下文压缩与任务记忆保持)       |
|       |             |                          | [1.4 运行时干预与治理](#14-运行时干预与扩展治理)           |
| Day 2 | 09:00–12:00 | 架构 + 评测 + 方法论闭环 | [2.1 Agent 架构模式](#21-agent-架构模式与任务编排)         |
|       |             |                          | [2.2 评测与可观测](#22-评测可观测回放与调试)               |
|       |             |                          | [2.3 方法论闭环](#23-上午复盘方法论闭环)                   |
| Day 2 | 14:00–17:00 | Harness 平台 + 生产落地  | [2.4 Harness 定制扩展](#24-harness-平台深度定制与扩展开发) |
|       |             |                          | [2.5 多租户与性能](#25-多租户权限与大规模并发)             |
|       |             |                          | [2.6 Multi-Agent 实战](#26-multi-agent-协同专项实战)       |
|       |             |                          | [2.7 生产线综合实战](#27-生产线全链路综合实战)             |
|       |             |                          | [2.8 生产上线规范](#28-生产上线规范)                       |
| 自学  | 4–6 h       | 无 API Key 跟练（可选）  | [第三部分：自学实验跟练手册](#第三部分自学实验跟练手册)    |

---

## 0. 先建立一张「地图」

在进两天细节之前，先对齐 **Coding Agent 工程** 在整条链路里的位置：

```text
人（目标 / 验收 / 风险）          Harness（工程骨架）              模型（决策核心）
┌──────────────┐          ┌────────────────────────────────┐          ┌─────────────┐
│ Goal / Spec  │          │ State   会话树 / Checkpoint     │          │             │
│ 人工审批     │ ───────► │ Context 压缩 / 分支摘要         │ ───────► │  LLM Agent  │
│ 评测指标     │          │ Tools   注册 / Guard / Hook     │ ◄─────── │  (预训练)   │
└──────────────┘          │ Runtime 循环 / 多 Agent 编排    │          └─────────────┘
                          │ Governance 权限 / 租户 / 配额   │
                          └────────────────────────────────┘
                                        │
                                        ▼
                          文件系统 / Shell / API / MCP / 业务 DB
```

| 名词                  | What                                      | 与开发的关系                                                         |
| --------------------- | ----------------------------------------- | -------------------------------------------------------------------- |
| **Agent（决策核心）** | 预训练 LLM，在上下文中推理并选择工具      | **不是你写的 if-else**；Harness 给它「手和记忆」                     |
| **Harness**           | 工具 + 知识 + 上下文 + 权限 + 运行时      | **本课主角**；Cursor / Claude Code / OpenClaw 都是不同形态的 Harness |
| **State**             | Append-only Session Log、分支、Checkpoint | 长任务不断点、可回放、可审计                                         |
| **Context**           | 活跃 messages[] + 压缩/摘要策略           | 窗口有限；工程上必须主动腾地方                                       |
| **Governance**        | Hook、Tool Guard、人工审批、租户隔离      | 生产环境的「安全带」                                                 |

**历史脉络**（读论文与老文档时会遇到）：

- **ReAct**（Yao et al., 2022）：Reason + Act 交错，现代 Coding Agent 循环的理论原型 →
  [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- **LangGraph Checkpoint**：图状态持久化与 time-travel 调试 →
  [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- **Claude Code / learn-claude-code**：12 步渐进式 Harness 教学实现 →
  [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)
- **OpenClaw / claw0**：生产级会话、Gateway、多通道 Harness 参考 →
  [shareAI-lab/claw0](https://github.com/shareAI-lab/claw0)

**本课开源素材索引**（讲师 Demo 默认路径）：

| 仓库                     | 路径                                                                                                        | 覆盖能力                                |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `training-python-public` | [`demo/ai-agent/`](../demo/ai-agent/)                                                                       | s01 主循环、s02 工具分发、s03 会话+压缩 |
| `training-claude-code`   | [`agents/s01`–`s12`](https://github.com/shareAI-lab/learn-claude-code/tree/main/agents)                     | 完整 12 层 Harness 递进                 |
| `training-claw0`         | [`sessions/zh/s03_sessions.md`](https://github.com/shareAI-lab/claw0/blob/main/sessions/zh/s03_sessions.md) | JSONL 会话 + ContextGuard               |

---

# 第一天：Agent 运行内核 —— 状态 / 上下文 / 运行时治理

[返回目录](#课程目录)

**今日目标**：离开「调 prompt 碰运气」，搭出一套 **能跑、能恢复、能压缩、能干预** 的最小 Agent
工程骨架。

| 时段        | 模块           | 形式        |
| ----------- | -------------- | ----------- |
| 09:00–09:30 | 1.1 核心观     | 讲授 + 画图 |
| 09:30–11:30 | 1.2 状态持久化 | 讲授 + Demo |
| 14:00–15:30 | 1.3 上下文压缩 | 讲授 + Demo |
| 15:30–17:00 | 1.4 运行时治理 | 讲授 + Demo |

---

## 1.1 Coding Agent Engineering 核心观

[返回目录](#课程目录)

### 1.1.1 Agent 与普通工作流的区别

| 维度     | 普通工作流（DAG / 规则引擎） | Coding Agent                       |
| -------- | ---------------------------- | ---------------------------------- |
| 控制流   | 人预先画好节点与边           | 模型在循环中**动态决定**下一步     |
| 失败处理 | 固定重试 / 告警              | 模型可**改计划**（Reflect）再 Act  |
| 状态     | 通常只存业务字段             | **完整对话 + 工具轨迹** 即状态     |
| 适用     | 步骤固定、输入结构化         | 目标明确、路径不确定、需与环境交互 |

_参考：Russell & Norvig《Artificial Intelligence: A Modern Approach》将 Agent
定义为「感知环境并采取行动以实现目标的系统」；LLM 时代 **决策核** 换成预训练模型，**Harness**
提供感知与行动接口。_

**一句话**：工作流是「剧本」；Agent 是「带工具的即兴演奏」——Harness 负责舞台、道具和安全绳。

### 1.1.2 Coding Agent 完整生命周期

课纲提出的闭环（与 ReAct / Reflexion 文献一致）：

```text
Goal → Plan → Act → Observe → Reflect → Commit
  │      │      │       │         │         │
  │      │      │       │         │         └─ 写入仓库 / 提交 PR / 持久化 Checkpoint
  │      │      │       │         └─ 失败归因、改计划、是否请求人工
  │      │      │       └─ 工具 stdout、测试报告、diff
  │      │      └─ 调工具：读文件、跑测试、调 API
  │      └─ 任务图 / Todo / 子目标拆解（s07 Task System）
  └─ 用户意图、Spec、验收标准
```

_参考：Reflexion（Shinn et al., 2023）在 Act–Observe 后增加语言化反思以改进后续决策 →
[arXiv:2303.11366](https://arxiv.org/abs/2303.11366)_

### 1.1.3 五大核心抽象

| 抽象           | 职责                                | 本课对应章节                                                         |
| -------------- | ----------------------------------- | -------------------------------------------------------------------- |
| **State**      | 会话树、Append-only Log、Checkpoint | [1.2](#12-状态持久化与恢复机制)                                      |
| **Context**    | 活跃 messages[]、压缩、分支摘要     | [1.3](#13-上下文压缩与任务记忆保持)                                  |
| **Tools**      | Schema + Handler、原子可组合        | [`s02_tool_dispatch`](../demo/ai-agent/s02_tool_dispatch/)           |
| **Runtime**    | 主循环、Hook、Guard、多 Agent 调度  | [1.4](#14-运行时干预与扩展治理)、[2.6](#26-multi-agent-协同专项实战) |
| **Governance** | 审批、权限、租户、配额              | [1.4](#14-运行时干预与扩展治理)、[2.5](#25-多租户权限与大规模并发)   |

_参考：learn-claude-code
[`agent-philosophy.md`](https://github.com/shareAI-lab/learn-claude-code/blob/main/skills/agent-builder/references/agent-philosophy.md)
— **模型是驾驶者，Harness 是载具**。_

### 1.1.4 最小可运行 Agent 结构图（课堂手绘）

```text
                    ┌─────────────────┐
                    │   User / API    │
                    └────────┬────────┘
                             │ query
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     Agent Runtime                         │
│  ┌────────────┐   ┌────────────┐   ┌─────────────────┐  │
│  │ SessionStore│◄─│ Agent Loop │──►│ Tool Dispatch   │  │
│  │  (JSONL)   │   │ while True │   │ name → handler  │  │
│  └────────────┘   └─────┬──────┘   └────────┬────────┘  │
│                         │                    │            │
│  ┌────────────┐   ┌─────▼──────┐   ┌────────▼────────┐  │
│  │ ContextGuard│◄─│ LLM Client │   │ bash/read/...   │  │
│  │ compact    │   └────────────┘   └─────────────────┘  │
│  └────────────┘                                          │
│  ┌────────────┐   ┌────────────┐                        │
│  │ Hook/Guard │   │ Human Queue│                        │
│  └────────────┘   └────────────┘                        │
└──────────────────────────────────────────────────────────┘
```

### 1.1.5 实操：拆解贯穿案例

**贯穿案例（两天统一）**：「**代码生成 + 批量图片处理**」——生成缩略图脚本 +
对目录内图片批量压缩/格式转换。

执行链路（模块 1 只画不跑）：

1. 用户：`为 ./assets 下所有 PNG 生成 800px 宽缩略图，并输出 Python 脚本`
2. **Plan**：Task 工具创建子任务（扫描 / 脚本 / 验证）
3. **Act**：`list_dir` → `write_file` → `bash python script.py`
4. **Observe**：脚本 stdout、生成文件数
5. **Reflect**：缺依赖则 pip install 并重试
6. **Commit**：Checkpoint 写入 Session Log；可选 PR

> 📂 主循环代码：[`s01_agent_loop/agent_loop.py`](../demo/ai-agent/s01_agent_loop/agent_loop.py)\
> 📂 12
> 层递进：[`training-claude-code/agents/`](https://github.com/shareAI-lab/learn-claude-code/tree/main/agents)

---

## 1.2 状态持久化与恢复机制

[返回目录](#课程目录)

### 1.2.1 为什么需要 Append-only Session Log

**问题**：进程崩溃、API 超时、用户关终端 —— 内存里的 `messages[]` 全丢。

**解法**：每轮对话 **追加** 一行 JSON（JSONL），写前不重写整个文件 → 崩溃时最多丢最后一行（可 fsync
加固）。

_参考：OpenClaw / claw0 生产实现同样采用 JSONL；见
[`claw0/sessions/zh/s03_sessions.md`](https://github.com/shareAI-lab/claw0/blob/main/sessions/zh/s03_sessions.md)_

四种记录类型：

```json
{"type": "user", "content": "压缩 assets 目录", "ts": 1718700000}
{"type": "assistant", "content": "[{\"type\":\"tool_use\",...}]", "ts": ...}
{"type": "tool_use", "tool_use_id": "tu_01", "name": "bash", "input": {...}, "ts": ...}
{"type": "tool_result", "tool_use_id": "tu_01", "content": "...", "ts": ...}
```

**重放**：`_rebuild_history()` 将扁平 JSONL 还原为 API 要求的 `messages[]`（tool_use 并入
assistant，tool_result 并入 user）。

### 1.2.2 会话树 / 分支（Branch）与 Checkpoint

**会话树**：同一会话 ID 下，从任意历史点 **fork** 新分支，探索不同方案（类似 git branch）。

```text
main ──●──●──●──●  (批量 PNG 方案)
              ╲
               ╲──●──●  branch/thumb-webp  (改用 WebP)
```

| 概念           | 含义                                         | 实现要点                                               |
| -------------- | -------------------------------------------- | ------------------------------------------------------ |
| **Branch**     | 命名分支，独立 JSONL 文件或 `branch_id` 字段 | `sessions/{id}/main.jsonl`、`sessions/{id}/webp.jsonl` |
| **Checkout**   | 切换活跃分支，加载对应 Log                   | REPL：`/switch webp`                                   |
| **Checkpoint** | 标记可恢复点（任务阶段完成）                 | 记录 `{"type":"checkpoint","label":"script_done",...}` |
| **Replay**     | 从 Log 重放至某 checkpoint                   | 过滤 `ts <= checkpoint_ts` 的行再 rebuild              |

_参考：LangGraph `checkpoint` + `thread_id` 支持 time-travel；概念对齐但存储格式不同 →
[Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)_

### 1.2.3 幂等性与任务重放

**幂等工具设计原则**：

- **读操作**天然幂等
- **写操作**：带 `idempotency_key` 或「先查后写」
- **副作用工具**（删文件、发工单）：Guard 层拦截 + 人工审批

**任务重放**：

1. 从 Session Log 恢复 `messages[]` 至最后 checkpoint
2. 读取 Task 图（`.tasks/task_*.json`）恢复 `pending` / `in_progress`
3. 从 **未完成工具调用** 处继续（勿重复已成功步骤）

_参考：learn-claude-code s07 Task System — 任务图落盘，压缩上下文后目标不丢 →
[`s07_task_system.py`](https://github.com/shareAI-lab/learn-claude-code/blob/main/agents/s07_task_system.py)_

### 1.2.4 图片操作状态记录（课纲扩展）

图片任务在 Log 中额外记录 **轻量元数据**，避免把二进制塞进 context：

```json
{
  "type": "artifact",
  "artifact_kind": "image",
  "path": "assets/out/thumb_001.webp",
  "sha256": "a1b2...",
  "width": 800,
  "height": 600,
  "parent_branch": "main",
  "ts": 1718700100
}
```

续跑时 Agent 用 `list_artifacts` 工具读元数据，而非重新 base64 整图。

### 1.2.5 Demo：最小 Session Log（Branch / Checkout / Replay）

> 📂
> 基础实现：[`s03_context_compact/session_store.py`](../demo/ai-agent/s03_context_compact/session_store.py)

**跟练步骤**：

```bash
cd training-python-public/demo/ai-agent/s03_context_compact
python session_store.py          # 验证 JSONL 追加与 rebuild
pytest test_session.py -v        # 单元测试
```

**课堂扩展练习**（在 `session_store.py` 上增量实现）：

```python
# 扩展 1：Branch — 从当前 session fork
def fork_branch(self, session_id: str, branch: str, up_to_line: int | None = None) -> str:
    """复制 main.jsonl 前 up_to_line 行到 {branch}.jsonl"""
    ...

# 扩展 2：Checkout — 切换活跃分支
def checkout(self, session_id: str, branch: str) -> list:
    return self.load_session(f"{session_id}/{branch}")

# 扩展 3：Replay — 断点续跑
def replay_to_checkpoint(self, session_id: str, label: str) -> list:
    """只保留 ts <= checkpoint(label).ts 的记录后 rebuild"""
    ...
```

**中断续跑模拟**：

```bash
# 终端 1：跑到一半 Ctrl+C
python agent_with_session.py --task "批量压缩 assets/"

# 终端 2：同 session_id 续跑
python agent_with_session.py --session-id abc123 --resume
```

**验收标准**：

- [ ] JSONL 可追加、可 rebuild 为合法 messages[]
- [ ] fork 后两分支互不影响
- [ ] checkpoint 后续跑不重复已完成 tool_use
- [ ] 图片 artifact 元数据可查询

---

## 1.3 上下文压缩与任务记忆保持

[返回目录](#课程目录)

### 1.3.1 上下文窗口：必然溢出

_数据点：读 1 个 1000 行文件 ≈ 4000 token；30 个文件 + 20 次命令 easily > 100k
token（learn-claude-code s06 经验值）。_

**关键信息取舍策略**（优先级从高到低）：

1. **当前 Goal / 未完成任务**（Task 图、`in_progress`）
2. **最近 K 轮 tool_result**（默认 K=3）
3. **分支摘要**（Branch Summary）
4. **Artifact 元数据**（图片路径、hash，非二进制）
5. **早期对话** → 压缩为摘要或占位符

### 1.3.2 三层压缩策略

_来源：learn-claude-code s06 →
[`docs/zh/s06-context-compact.md`](https://github.com/shareAI-lab/learn-claude-code/blob/main/docs/zh/s06-context-compact.md)_

```text
Every turn:
┌──────────────────┐
│ Tool call result │
└────────┬─────────┘
         ▼
[Layer 1: micro_compact]     每轮静默；旧 tool_result → "[Previous: used {tool}]"
         ▼
[Token > threshold?] ──no──► 继续
         │yes
         ▼
[Layer 2: auto_compact]      存 transcript → LLM 摘要 → 替换 messages[]
         ▼
[Layer 3: manual compact]    用户 / 工具主动触发（/compact）
```

| 层     | 触发       | 信息损失             | 恢复手段                |
| ------ | ---------- | -------------------- | ----------------------- |
| micro  | 每轮       | 低（仅旧 tool 输出） | 完整 JSONL / transcript |
| auto   | token 阈值 | 中（摘要化）         | `.transcripts/*.jsonl`  |
| manual | 用户命令   | 中                   | 同上                    |

### 1.3.3 Branch Summary 与长任务记忆

**分支摘要**：切换分支或合并前，对该分支 Log 生成结构化摘要：

```markdown
## Branch Summary: webp-migration

- Goal: 将 assets/ PNG 转为 WebP，宽度 ≤800px
- Done: 脚本 generate_thumbs.py；已处理 120/120
- Pending: 运行 pytest tests/test_thumbs.py
- Artifacts: assets/out/*.webp (120 files)
```

写入 `branches/webp-migration.summary.md`，主分支 Context 只引用摘要路径。

### 1.3.4 3 阶段溢出保护（ContextGuard）

_来源：claw0 s03 / [`compact.py`](../demo/ai-agent/s03_context_compact/compact.py)_

```text
Attempt 0: 正常 API 调用
    │ overflow?
    ▼
Attempt 1: 截断超大 tool_result（如 >2000 字符）
    │ overflow?
    ▼
Attempt 2: LLM compact_history（摘要替换旧消息）
    │ overflow?
    ▼
  raise（需人工介入或换模型）
```

### 1.3.5 Demo：超长文本 + 多轮图片操作压缩

```bash
cd training-python-public/demo/ai-agent/s03_context_compact
python compact.py                # 三层压缩演示
pytest test_session.py -v
```

**课堂实验**：

1. 让 Agent 连续 `read_file` 20+ 个文件 → 观察 micro_compact 占位符
2. 调低 `TOKEN_THRESHOLD=5000` → 触发 auto_compact，检查 `.transcripts/`
3. 图片场景：每处理 10 张写一条 `artifact` 记录；compact 后仍可通过工具列出进度

**跨小时任务验证**：

```bash
# 模拟：第一轮处理 50 张后 compact 并退出
python long_task_demo.py --max-images 50 --compact-and-exit

# 第二轮：同 session 续跑剩余 50 张
python long_task_demo.py --session-id run1 --resume
```

**验收标准**：

- [ ] micro_compact 后最近 3 轮 tool_result 完整
- [ ] auto_compact 后 Task 图 / artifact 列表仍可驱动续跑
- [ ] ContextGuard 在 mock overflow 下 3 阶段可观测

---

## 1.4 运行时干预与扩展治理

[返回目录](#课程目录)

### 1.4.1 Human-in-the-Loop（HITL）

**人工介入队列**：高风险工具调用进入 `PENDING_APPROVAL` 状态，等人确认后再执行。

```text
LLM → tool_use: delete_file("/data/*")
         │
         ▼
    ToolGuard: 匹配规则 DELETE_PATTERN
         │
         ▼
    HumanQueue.enqueue({tool, args, session_id})
         │
    人: approve / reject
         │
         ▼
    执行或返回 "User rejected"
```

适用：**删数据、发外部消息、改生产配置、批量图片覆盖原图**。

### 1.4.2 Hook 扩展机制

_参考：Cursor Hooks — [`create-hook` Skill](https://cursor.com/docs/agent/hooks) ；事件包括
`preToolUse`、`postToolUse`、`beforeShellExecution`、`preCompact` 等。_

| 扩展点     | 时机          | 典型用途                  |
| ---------- | ------------- | ------------------------- |
| **审批点** | tool 执行前   | HITL、权限校验            |
| **拦截点** | tool 执行前   | 阻断危险命令、路径越界    |
| **观察点** | tool 执行后   | Trace、审计日志、指标     |
| **改写点** | API 请求前/后 | Provider Payload Mutation |

**最小 Hook 协议**（stdin/stdout JSON）：

```json
// preToolUse 输入
{"tool_name": "bash", "tool_input": {"command": "rm -rf /"}}

// 输出：deny
{"permission": "deny", "user_message": "禁止递归删除根路径"}
```

### 1.4.3 Tool Call Guard 设计原则

```python
GUARD_RULES = [
    {"match": {"tool": "bash", "pattern": r"rm\s+-rf\s+/"}, "action": "deny"},
    {"match": {"tool": "write_file", "path_prefix": "/etc/"}, "action": "require_approval"},
    {"match": {"tool": "image_edit", "max_pixels": 50_000_000}, "action": "deny"},
]
```

- **fail-closed**： Guard 异常时默认拒绝
- **可解释**：拒绝原因回传模型，便于 Reflect
- **可配置**：按租户 / 项目 YAML 热加载

### 1.4.4 Provider Payload Mutation

不同模型对 **图片格式** 支持不一（URL vs base64 vs 特定 MIME）。在 LLM Client 层统一改写：

```python
def mutate_messages_for_provider(messages, provider: str) -> list:
    if provider == "model-a":
        return convert_images_to_base64(messages)
    if provider == "model-b":
        return convert_images_to_urls(messages, upload_fn=upload_to_obs)
    return messages
```

### 1.4.5 Demo：Hook + Guard + 请求改写

**跟练 A：Cursor 项目 Hook（可选，需 Cursor 2.0+）**

`.cursor/hooks.json`：

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": ".cursor/hooks/block-rm-rf.sh"
      }
    ]
  }
}
```

**跟练 B：Python ToolGuard（与 s02 集成）**

```python
def guarded_dispatch(tool_name, tool_input, guards, human_queue):
    for rule in guards:
        if rule.matches(tool_name, tool_input):
            if rule.action == "deny":
                return f"Guard denied: {rule.reason}"
            if rule.action == "require_approval":
                if not human_queue.approve(tool_name, tool_input):
                    return "User rejected"
    return TOOL_HANDLERS[tool_name](**tool_input)
```

**跟练 C：图片工具 + 审批**

- `batch_resize` 覆盖原图 → `require_approval`
- `batch_resize` 输出到 `out/` → 允许

**第一天小结产出**：可回放 Session + 三层压缩 + Guard/HITL 的最小骨架（见
[附录 A](#附录-a两天产出物验收清单)）。

---

# 第二天：通用方法论 + Harness 平台 + 多智能体 + 生产落地

[返回目录](#课程目录)

| 时段        | 模块                | 形式            |
| ----------- | ------------------- | --------------- |
| 09:00–10:40 | 2.1 架构模式        | 讲授 + 对比实验 |
| 10:40–12:00 | 2.2 评测可观测      | 案例 + Demo     |
| 12:00–12:20 | 2.3 方法论闭环      | 串讲            |
| 14:00–15:10 | 2.4 Harness 定制    | 讲授 + Demo     |
| 15:10–15:40 | 2.5 多租户          | 案例            |
| 15:40–16:30 | 2.6 Multi-Agent     | 实战            |
| 16:30–18:30 | 2.7 综合实战        | 团队协作        |
| 18:30–19:00 | 2.8 上线规范 + 答疑 | 讲授            |

---

## 2.1 Agent 架构模式与任务编排

[返回目录](#课程目录)

### 2.1.1 四种主流模式

| 模式                  | 结构                         | 优点                       | 缺点             | 参考                                            |
| --------------------- | ---------------------------- | -------------------------- | ---------------- | ----------------------------------------------- |
| **ReAct**             | 交错 Reason + Act            | 简单、易调试、token 相对省 | 长计划易漂移     | [ReAct paper](https://arxiv.org/abs/2210.03629) |
| **Plan-and-Execute**  | 先出完整 Plan 再逐步 Execute | 可控、适合长任务           | 计划过时需重规划 | LangChain Plan-and-Execute                      |
| **Reflection**        | Act → Critique → Retry       | 提升成功率                 | 额外 LLM 轮次    | Reflexion                                       |
| **Supervisor-Worker** | 总控分发子 Agent             | 并行、专精分工             | 协调开销         | learn-claude-code s09                           |

### 2.1.2 选型对照表（文本 + 图片场景）

| 场景                | 推荐                   | 理由                  |
| ------------------- | ---------------------- | --------------------- |
| 单次脚本生成        | ReAct                  | 步骤少、反馈快        |
| 批量图片 + 多目录   | Plan-and-Execute       | 先枚举任务再并行 bash |
| 代码审查 + 修复     | Reflection             | 需要自检测试输出      |
| 代码生成 ∥ 图片处理 | Supervisor-Worker      | 两子 Agent 专精       |
| 固定 ETL 流水线     | **工作流（非 Agent）** | 步骤确定时用 DAG 更省 |

### 2.1.3 Coding Agent 常见失败模式

| 失败模式   | 现象                 | Harness 对策                   |
| ---------- | -------------------- | ------------------------------ |
| 计划过长   | Plan 占满 context    | Task 图落盘 + 只加载当前子任务 |
| 工具乱调用 | 重复 read、无效 bash | Tool Guard + micro_compact     |
| 上下文污染 | 旧错误结论影响后续   | 分支 isolate + compact         |
| 重试失控   | 无限 fix loop        | max_iterations + 退避 + HITL   |
| 长尾卡死   | 单步 hang            | 工具 timeout + 后台任务 s08    |

### 2.1.4 图片异步编排要点

- **长耗时**（批量转码）→ 后台 Job + artifact 状态轮询，勿阻塞主循环
- **大文件** → 只传路径 / URL，不传 base64 进 context
- **失败部分成功** → Checkpoint 按文件粒度，支持断点续跑

### 2.1.5 Demo：ReAct vs Plan-and-Execute 对比

> 📂 框架对比：[`s04_framework_comparison/`](../demo/ai-agent/s04_framework_comparison/)\
> 📂 Plan
> 任务图：[`training-claude-code/agents/s07_task_system.py`](https://github.com/shareAI-lab/learn-claude-code/blob/main/agents/s07_task_system.py)

**实验设计**（同一 prompt，记录指标）：

```
Prompt: 为 assets/ 下所有 PNG 生成缩略图，并编写可重复执行的 Python 脚本与 pytest。
```

| 指标                   | ReAct    | Plan-and-Execute |
| ---------------------- | -------- | ---------------- |
| Token 消耗             | 实测填入 | 实测填入         |
| 任务成功率             | 实测填入 | 实测填入         |
| 端到端时延             | 实测填入 | 实测填入         |
| 可控性（人工干预次数） | 实测填入 | 实测填入         |

---

## 2.2 评测、可观测、回放与调试

[返回目录](#课程目录)

### 2.2.1 Trace 链路设计

```text
run_id
 ├── span: llm.call#1
 ├── span: tool.bash
 ├── span: tool.read_file
 ├── span: llm.call#2
 ├── span: guard.blocked (optional)
 └── span: checkpoint.write
```

**最小字段**：`run_id`, `session_id`, `span_id`, `parent_id`, `name`, `start`, `end`, `status`,
`attrs`（tool_name, token_in/out）

_参考：OpenTelemetry GenAI Semantic Conventions（演进中）→
[OTel GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)_

### 2.2.2 Run Replay 与失败归因

1. 从 Session JSONL **完整重放**（不调用 LLM）→ 验证 rebuild 正确
2. **半重放**：从 checkpoint 起用**同一模型**重跑 → 对比 diverge 点
3. **归因标签**：`planning_error` / `tool_error` / `guard_block` / `context_overflow` /
   `model_hallucination`

### 2.2.3 关键指标体系

| 指标               | 定义                              | 目标方向              |
| ------------------ | --------------------------------- | --------------------- |
| **任务成功率**     | 验收通过的任务 / 总任务           | ↑                     |
| **工具调用成功率** | 无异常 tool_result / 总 tool 调用 | ↑                     |
| **平均时延**       | 首次响应、端到端完成              | ↓                     |
| **Token 成本**     | 输入+输出 token × 单价            | ↓                     |
| **人工干预率**     | 需 approve 或人改 prompt 的比例   | ↓（但高风险场景除外） |
| **恢复成功率**     | 中断后续跑成功 / 中断任务         | ↑                     |

### 2.2.4 Demo：评测样例 + Trace

**Benchmark 样例 YAML**（`benchmarks/image_code_gen.yaml`）：

```yaml
cases:
  - id: thumb_001
    prompt: "为 fixtures/3png 生成 400px 宽缩略图到 out/"
    acceptance:
      - glob_exists: "out/*.jpg"
      - min_count: 3
      - pytest: "tests/test_thumbs.py"
  - id: script_idempotent
    prompt: "编写脚本，重复运行不重复处理已存在文件"
    acceptance:
      - file_exists: "resize.py"
      - command_exit_0: "python resize.py && python resize.py"
```

**Trace 注入点**（伪代码）：

```python
with tracer.start_span("tool.bash") as span:
    span.set_attr("command", cmd)
    result = run_bash(cmd)
```

**失败回放**：

```bash
python replay_run.py --run-id failed_042 --from-checkpoint script_done
```

---

## 2.3 上午复盘：方法论闭环

[返回目录](#课程目录)

```text
     ┌─────────────────────────────────────────┐
     │         Coding Agent Engineering         │
     └─────────────────────────────────────────┘
           │              │              │
  State ◄──┤              │              ├──► Governance
持久/分支   │              │              │     Hook/Guard
           │              │              │
           ▼              ▼              ▼
       Context ◄─── Runtime ───► Tools
       压缩/摘要      循环/编排      原子工具
           │              │
           └──────► 架构模式 ◄──────┘
                 ReAct / Plan / Multi-Agent
                           │
                           ▼
                     评测 / Trace
                     驱动迭代优化
```

**专家意见落地**（课纲评审摘要）：

- 少宏观多实战 → 每节绑定 Demo 与验收清单
- 增加 loop engineering → s01–s12
  渐进式循环（[`training-claude-code`](https://github.com/shareAI-lab/learn-claude-code)）
- 增加 Harness / Multi-Agent 生产案例 →
  [2.4](#24-harness-平台深度定制与扩展开发)、[2.6](#26-multi-agent-协同专项实战)
- 业务场景多样化 → 综合实战可选工单 / 知识问答 / 代码生成（[2.7](#27-生产线全链路综合实战)）

---

## 2.4 Harness 平台深度定制与扩展开发

[返回目录](#课程目录)

### 2.4.1 插件体系与 Custom Steps

**Harness 平台**（抽象）：在统一 Runtime 上挂载 **Steps** 流水线。

```text
Request → [PreHook] → [ContextLoad] → [AgentLoop] → [PostHook] → Response
              │              │              │
              │         Custom Steps:       │
              │         - ImageBatchStep    │
              │         - CodeGenStep       │
              │         - RAGInjectStep     │
```

| 扩展点          | 说明                                           |
| --------------- | ---------------------------------------------- |
| **Custom Step** | 同步/异步处理单元，读写 Session State          |
| **Skill**       | 按需知识包（tool_result 注入，非 system 堆叠） |
| **行业模板**    | 预置 Steps + Tools + Guard 规则                |

_参考：learn-claude-code s05 Skill Loading →
[`docs/zh/s05-skill-loading.md`](https://github.com/shareAI-lab/learn-claude-code/blob/main/docs/zh/s05-skill-loading.md)_

### 2.4.2 封装「代码生成 + 图片处理」行业模板

目录结构示例：

```text
harness-templates/media-code/
├── template.yaml          # 步骤编排、默认 Guard
├── tools/
│   ├── image_batch.py     # batch_resize, format_convert
│   └── codegen.py
├── skills/
│   └── pytest-gen/SKILL.md
├── guards/
│   └── default.yaml
└── benchmarks/
    └── smoke.yaml
```

`template.yaml` 片段：

```yaml
name: media-code-pipeline
steps:
  - id: scan_assets
    tool: list_dir
  - id: gen_script
    agent: codegen
    skill: pytest-gen
  - id: batch_images
    custom: ImageBatchStep
    params: {max_width: 800, format: webp}
acceptance:
  - pytest: tests/
```

### 2.4.3 Demo：Custom Step — 批量图片压缩

```python
# custom_steps/image_batch.py
from PIL import Image
from pathlib import Path

def image_batch_step(state, *, src: str, dst: str, max_width: int = 800):
    artifacts = []
    for p in Path(src).glob("*.png"):
        out = Path(dst) / f"{p.stem}.webp"
        img = Image.open(p)
        img.thumbnail((max_width, max_width * 10))
        img.save(out, "WEBP")
        artifacts.append({"path": str(out), "width": img.width, "height": img.height})
    state.append_artifact("image", artifacts)
    return f"Processed {len(artifacts)} images"
```

**运行**：

```bash
pip install Pillow
python run_template.py --template harness-templates/media-code --task "处理 assets/"
```

---

## 2.5 多租户权限与大规模并发

[返回目录](#课程目录)

### 2.5.1 多租户隔离模型

```text
Tenant A                          Tenant B
├── projects/{p1}/sessions/       ├── projects/{p2}/sessions/
├── artifact_store/ (prefix)      ├── artifact_store/
├── RBAC: role → tool allowlist   ├── RBAC
└── quota: token/day, cpu         └── quota
```

| 层级     | 隔离对象                     | 实现                |
| -------- | ---------------------------- | ------------------- |
| **数据** | Session JSONL、图片 artifact | 路径前缀 + 加密桶   |
| **算力** | Worker 池、并发数            | 队列 per-tenant     |
| **权限** | 工具白名单                   | RBAC YAML           |
| **网络** | 出站 API                     | 租户级 proxy / 密钥 |

### 2.5.2 性能优化策略

| 痛点         | 策略                                            |
| ------------ | ----------------------------------------------- |
| 长任务占内存 | Session 落盘；活跃 context 仅保留窗口           |
| 图片算力     | 异步 Worker + 对象存储；Agent 只轮询状态        |
| 多租户争抢   | 优先级队列 + 配额令牌桶                         |
| Token 成本   | 小模型路由（规划用强模型，摘要用弱模型）        |
| 断点唤醒     | 会话 idle 超时 → 持久化；唤醒时 load checkpoint |

### 2.5.3 Demo：瓶颈剖析清单

对「批量图片 + 代码生成」长任务填写：

| 阶段     | 耗时占比 | 优化手段            |
| -------- | -------- | ------------------- |
| LLM Plan | %        | 计划缓存、弱模型    |
| 图片 CPU | %        | 多进程 Pillow / GPU |
| 磁盘 I/O | %        | 本地 SSD / OBS 并行 |
| 等待审批 | %        | 批量 approve UI     |

---

## 2.6 Multi-Agent 协同专项实战

[返回目录](#课程目录)

### 2.6.1 Supervisor-Worker 架构

_参考：learn-claude-code s09 Agent Teams →
[`docs/zh/s09-agent-teams.md`](https://github.com/shareAI-lab/learn-claude-code/blob/main/docs/zh/s09-agent-teams.md)_

```text
             ┌─────────────┐
             │ Lead Agent  │
             │ (Planner)   │
             └──────┬──────┘
    spawn/send     │     send
       ┌───────────┼───────────┐
       ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Coder    │ │ Image    │ │ Verifier │
│ Worker   │ │ Worker   │ │ Worker   │
└──────────┘ └──────────┘ └──────────┘
       │           │           │
       └───────────┴───────────┘
              JSONL Inbox
          .team/inbox/{name}.jsonl
```

**通信**：append-only inbox，`read_inbox` 后 drain；每轮 LLM 前注入 `<inbox>...</inbox>`。

**冲突消解**：Verifier 失败 → Lead 重新 spawn 或降级 HITL。

### 2.6.2 与 Harness 全栈联调

| 能力          | Lead              | Worker                              |
| ------------- | ----------------- | ----------------------------------- |
| Session State | 主 session + 分支 | 子 session 或共享 Task 图           |
| Context       | 摘要 + inbox      | 完整 tool 轨迹（隔离）              |
| Governance    | 全局 Guard        | 工具子集（如 Image Worker 无 bash） |

### 2.6.3 Demo：规划 → 执行 → 校验

```bash
cd training-claude-code   # 或本地 clone learn-claude-code
python agents/s09_agent_teams.py
```

**课堂任务**：

1. Lead：拆 Task「脚本 + 120 张缩略图 + pytest」
2. Coder Worker：写 `resize.py` + 测试
3. Image Worker：批量处理（Custom Step）
4. Verifier：跑 pytest + 检查 artifact 数量
5. 全链路 Trace + 失败 replay

---

## 2.7 生产线全链路综合实战

[返回目录](#课程目录)

### 2.7.1 可选场景（团队抽签）

| 场景         | Harness 要点                        |
| ------------ | ----------------------------------- |
| **智能分析** | 日志工具 + RAG Skill + 摘要 compact |
| **代码生成** | Git 工具 + Guard + CI 验收          |
| **需求拆解** | Plan-and-Execute + Task 图          |
| **规则审核** | Reflection + 结构化输出             |
| **工单处理** | Multi-Agent + HITL + 外部 API 工具  |

### 2.7.2 团队交付清单

- [ ] Harness 工程 repo（template + tools + guards）
- [ ] Session 可恢复 + 至少 1 个 checkpoint
- [ ] 上下文压缩可观测（/transcripts 或日志）
- [ ] 1 条 Tool Guard + 1 个 HITL 场景
- [ ] Benchmark ≥ 3 cases + 任务成功率报告
- [ ] Trace 可回放一次失败 run
- [ ] README：架构图 + 指标 + 已知限制

---

## 2.8 生产上线规范

[返回目录](#课程目录)

| 维度         | 建议                                                         |
| ------------ | ------------------------------------------------------------ |
| **版本管理** | template / guard / skill semver；Session 格式 migration 脚本 |
| **评审管控** | Guard 规则变更需双人 review；HITL 审计日志保留 90 天         |
| **线上监控** | 任务成功率、P95 时延、Token 日账单、Guard 拦截率             |
| **故障回滚** | 模板 pin 上一版本；Session 兼容读；Feature flag 控新 Step    |
| **密钥**     | 租户级 AK/SK；禁止进 Session Log                             |

---

# 第三部分：自学实验跟练手册

[返回目录](#课程目录)

暂无 LLM API Key 时，可按下列顺序 **只跑不调用模型** 的部分：

| 顺序 | 实验              | 命令                                                        | 验证               |
| ---- | ----------------- | ----------------------------------------------------------- | ------------------ |
| 1    | JSONL Session     | `python demo/ai-agent/s03_context_compact/session_store.py` | rebuild 消息数正确 |
| 2    | 三层压缩          | `python demo/ai-agent/s03_context_compact/compact.py`       | 占位符与摘要       |
| 3    | 工具分发          | `pytest demo/ai-agent/s02_tool_dispatch/ -v`                | 全绿               |
| 4    | 主循环（需 Key）  | `python demo/ai-agent/s01_agent_loop/agent_loop.py`         | 单轮问答           |
| 5    | Claude Code 12 层 | `python agents/s01_agent_loop.py` … `s09`                   | 按 README-zh 递进  |

**环境**：

```bash
cd training-python-public/demo/ai-agent
pip install -r requirements.txt
cp .env.example .env   # 填入 MINIMAX_API_KEY 或 Anthropic Key
```

---

## 附录 A：两天产出物验收清单

| 序号 | 产出物              | 对应章节 | 最低验收                      |
| ---- | ------------------- | -------- | ----------------------------- |
| 1    | 可恢复会话状态 Demo | 1.2      | fork/checkout/replay 通过测试 |
| 2    | 上下文压缩方案      | 1.3      | 三层压缩 + 跨轮续跑           |
| 3    | 运行时治理策略      | 1.4      | ≥1 Guard + ≥1 HITL 路径       |
| 4    | 架构选型 + 评测模板 | 2.1–2.2  | 对照表 + benchmark YAML       |
| 5    | Harness 业务模板    | 2.4      | Custom Step 可运行            |
| 6    | 多租户 + 性能方案   | 2.5      | 设计稿 + 瓶颈表               |
| 7    | Multi-Agent 工程    | 2.6–2.7  | 三 Worker 联调 + Trace        |

---

## 附录 B：扩展阅读索引

| 主题                       | 资源                                                                                                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agent 哲学                 | [learn-claude-code agent-philosophy](https://github.com/shareAI-lab/learn-claude-code/blob/main/skills/agent-builder/references/agent-philosophy.md) |
| 12 层 Harness 递进         | [README-zh](https://github.com/shareAI-lab/learn-claude-code/blob/main/README-zh.md)                                                                 |
| OpenClaw 会话              | [claw0 s03_sessions](https://github.com/shareAI-lab/claw0/blob/main/sessions/zh/s03_sessions.md)                                                     |
| ReAct                      | [Yao et al., 2022](https://arxiv.org/abs/2210.03629)                                                                                                 |
| Reflexion                  | [Shinn et al., 2023](https://arxiv.org/abs/2303.11366)                                                                                               |
| LangGraph 持久化           | [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)                                                              |
| Cursor Hooks               | [Cursor Docs — Hooks](https://cursor.com/docs/agent/hooks)                                                                                           |
| MCP 与 Agent 基础          | 姊妹篇 [`we-know-ai-agent.md`](we-know-ai-agent.md)                                                                                                  |
| AI 编程范式                | 姊妹篇 [`we-know-ai-coding.md`](we-know-ai-coding.md)                                                                                                |
| Harness 2 天大纲（联通版） | [`20260527-广州联通-Harness-Engineering.md`](../../training-python/Case/DongFangRuiTong/dagang/20260527-广州联通-Harness-Engineering.md)             |

---

## 附录 C：讲义维护说明（给讲师）

1. **Demo 路径**：优先 `training-python-public/demo/ai-agent`；进阶演示用 `training-claude-code`
   clone。
2. **API**：课堂可统一 MiniMax / 通义 / Anthropic；Guard 与 Session 与厂商无关。
3. **图片案例**：大屏 / 媒资场景可保留；若客户更偏工单 / 知识问答，替换
   [2.7](#27-生产线全链路综合实战) prompt 即可，**骨架不变**。
4. **更新节奏**：LangGraph / Cursor Hooks / OpenClaw 版本变化快，每季度核对附录链接与
   `.env.example`。

---

_本讲义版本：2026-Q2 · 对应课纲 20260618-AI-Coding_
