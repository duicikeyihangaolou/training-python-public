# AI Agent 全栈开发与业务落地

**目标**：学员掌握 Agent 主循环、MCP 协议与 Server 实现，具备独立落地 AI Agent 业务能力。

**时长**：2 天（9：00-12：00，13：30-16：30）

**前置知识**：Python 基础、OOP、并发；AI 智能体开发（工具调用、LLM API 基础概念）

---

## 总览

| 日期    | 上午（3h）          | 下午（3h）    |
| ----- | --------------- | --------- |
| Day 1 | Agent 主循环与工具编排  | MCP 协议与连接 |
| Day 2 | MCP Server 设计实现 | 完整实战与扩展   |

### 环境准备

- Python 3.10+
- Node.js 18+（部分工具需要）
- OpenAI API 密钥 或 Anthropic API 密钥（二选一，Claude SDK 更推荐）
- Git、pip/npm

### 不覆盖内容

- Coze/Dify 等平台用法
- 多 Agent 协同进阶（除 CrewAI 基础）
- Data Agent / ChatBI
- 企业价值与落地路径

---

## 第一天：自建 Agent 与工具编排

### 上午：Agent 主循环（3 小时）

#### 1. Agent 主循环：感知–决策–执行闭环

> _"Agent 就是 `while True` + `stop_reason`"_ — 一个循环 + 一个退出条件 = 一个智能体。

**核心流程图**：

```
+----------+    +-------+    +------------------+
||  User   ||-->|  LLM  ||-->| Tool Dispatch    |
|| prompt  |    |       |    | { name -> func } |
+----------+    +---+---+    +--------+---------+
                   ^                 |
                   |   tool_result   |
                   +-----------------+
                   (loop until stop_reason != "tool_use")
```

**停止条件（stop_reason）**：

| stop_reason    | 含义             | 动作        |
| -------------- | -------------- | --------- |
| `"end_turn"`   | 模型完成回复         | 打印文本，继续循环 |
| `"tool_use"`   | 模型想调用工具        | 执行工具，反馈结果 |
| `"max_tokens"` | 回复被 token 限制截断 | 打印部分文本    |

**从零实现**（理解底层）：

```python
def agent_loop(query):
    messages = [{"role": "user", "content": query}]
    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return  # 打印 response.content 中的文本

        # 执行工具，收集结果
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS[block.name](**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        # 工具结果作为新 user 消息，继续循环
        messages.append({"role": "user", "content": results})
```

**用框架快速搭建**：Claude Agent SDK / OpenAI Agents SDK，最小 Boilerplate（~50 行），内置主循环、解析、重试。

> 📂 代码示例：[s01_agent_loop](../demo/ai-agent/s01_agent_loop/) — 从零实现 ~30 行主循环

#### 2. 工具描述与分发

**工具注册 = Schema（告诉模型）+ Handler（告诉代码）**：

```python
TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command."},
                "timeout": {"type": "integer"},
            },
            "required": ["command"],
        },
    },
]

TOOL_HANDLERS = {
    "bash": tool_bash,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
}
```

**分发函数**（一次字典查找，无 if/elif 链）：

```python
def process_tool_call(tool_name, tool_input):
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"
    try:
        return handler(**tool_input)
    except TypeError as exc:
        return f"Error: Invalid arguments: {exc}"
    except Exception as exc:
        return f"Error: {tool_name} failed: {exc}"
```

**安全沙箱**：路径校验防止目录穿越。

**多工具路由**：registry 映射表，扩展时只加 Schema + Handler，循环本身不变。

> 📂 代码示例：[s02_tool_dispatch](../demo/ai-agent/s02_tool_dispatch/) — TOOLS Schema + TOOL_HANDLERS +
> 分发函数

#### 3. 上下文管理与会话持久化

> _"上下文总会满，要有办法腾地方"_

**三层压缩策略**：

```
Tool call result
      |
      v
[Layer 1: micro_compact]     每轮静默执行
  超过 3 轮的 tool_result → "[Previous: used {tool_name}]"
      |
      v
[Token > 50000?]
   no         yes
   |           |
   v     [Layer 2: auto_compact]
        保存完整对话到 .transcripts/
        LLM 生成摘要，替换所有消息
              |
              v
      [Layer 3: manual compact]
        用户主动调用 compact 工具
```

**会话持久化（JSONL）**：

- 每个会话一个 `.jsonl` 文件，追加写入（原子操作）
- 四种记录类型：`user` / `assistant` / `tool_use` / `tool_result`
- 重放时重建 API 兼容的 `messages[]`

**3 阶段溢出保护**（`guard_api_call`）：

1. 正常调用
2. 溢出 → 截断过大的 tool_result
3. 还溢出 → LLM 摘要压缩历史

> 📂 代码示例：[s03_context_compact](../demo/ai-agent/s03_context_compact/) — 三层压缩 + JSONL 持久化 + 3 阶段溢出保护

#### 4. 主流 Agent 框架对比（选讲）

| 框架                     | 特点                                                  | 适用场景                  | Skill 支持 |
| ---------------------- | --------------------------------------------------- | --------------------- | -------- |
| **Claude Agent SDK**   | 原生 MCP、扩展思维、透明推理                                    | 深度用 Claude / 需 MCP 集成 | MCP      |
| **OpenAI Agents SDK**  | 最小 boilerplate、沙盒执行、结构化输出                           | OpenAI 模型、追求简洁        | MCP      |
| **CrewAI**             | 角色 + 任务 + 班组、多 Agent 协作                             | 业务流程自动化、多角色任务         | Tool     |
| **LangGraph**          | 状态机/图模型、checkpoint、可观测                              | 复杂工作流、生产级控制           | Tool     |
| **Hermes Agent**       | 增长最快开源（140k+ stars）、GEPA 自优化、6 大消息平台                | 快速落地、自托管、多平台集成        | 内置 Skill |
| **OpenHuman**          | Rust + Tauri 桌面端、Memory Tree、118+ 数据源、TokenJuice 压缩 | 桌面优先、本地隐私、多数据整合       | 内置 Skill |
| **OpenClaw**           | 370k+ stars、50+ 平台集成，Skill 市场成熟                     | 快速集成、成熟生态             | Skill 市场 |
| **Claude Code Router** | 多 AI 引擎路由、自动切换、Token 优化                             | 需要灵活切换模型、项目级管理        | MCP      |

选 1～2 个做端到端演示，学员跟做。

> 📂 代码示例：[s04_framework_comparison](../demo/ai-agent/s04_framework_comparison/) — Claude SDK /
> OpenAI SDK / CrewAI / LangGraph / Hermes / OpenHuman / OpenClaw / Claude Code Router

#### 5. Skill 机制与开发

> _"Skill = 工具包 + 编排逻辑 + 元数据"_

**Skill vs Tool**：

| 维度   | Tool（工具）      | Skill（技能）                  |
| ---- | ------------- | -------------------------- |
| 粒度   | 单个原子操作        | 多个工具 + 编排逻辑                |
| 复用性  | 依赖框架工具系统      | 可脱离框架，独立分发                 |
| 生命周期 | 随 Agent 会话    | 可持久化、安装、版本管理               |
| 生态   | MCP Server 市场 | 社区 Skill 市场（HuggingFace 等） |

**Skill 核心结构**：

```json
{
  "name": "web_search",
  "version": "1.0.0",
  "description": "网页搜索与摘要",
  "tools": ["search", "fetch", "extract"],
  "prompt_template": "使用 {{tool}} 搜索 {{query}}，返回摘要",
  "config": {
    "max_results": 5,
    "timeout": 30000
  }
}
```

**Skill 开发流程**（以 Hermes/OpenClaw 为例）：

1. **定义 Skill 元数据**：`name` / `version` / `description` / `tools`
2. **实现工具函数**：每个 tool 对应一个 handler
3. **编写 prompt 模板**：定义 Skill 被调用时的系统提示词
4. **注册到 Skill 注册表**：`skill register ./my_skill.yaml`
5. **测试与发布**：本地调试 → 打包 → 发布到社区市场

**OpenClaw Skill 示例**：

```yaml
name: github-assist
version: 1.0.0
tools:
  - name: create_issue
    handler: github.create_issue
  - name: list_prs
    handler: github.list_prs
prompts:
  - "帮我创建一个 GitHub Issue"
  - "列出最近的 PR"
```

**OpenHuman Skill 示例**（内置 Skill 系统）：

```python
from openhuman import skill

@skill.define(name="file_organizer", version="1.0.0")
def organize_files(directory: str, pattern: str = "*.txt"):
    """按规则整理文件"""
    # 实现逻辑
    pass
```

**Skill 市场与生态**：

- **OpenClaw Marketplace**：成熟社区，1000+ 公开 Skill
- **Hermes Skill Registry**：增长迅速，与 OpenClaw 互通
- **Hugging Face Agents**：新兴生态，支持模型卡片一键加载
- **Claude Code Router**：支持 Skill 路由，自动选择最优工具集

> 📂 代码示例：[s05_skill_dev](../demo/ai-agent/s05_skill_dev/) — Skill 开发模板 + OpenClaw / Hermes 实际开发

#### 6. 开源 Agent 框架（选讲）

- **Hermes Agent**（Nous Research，2026 年 2 月发布）
  - 增长最快的开源 Agent（140k+ GitHub stars）
  - GEPA 自优化循环、多级记忆（session/persistent/skill）
  - 模型无关、MIT 许可证、6 大消息平台（Telegram/Discord/Slack/WhatsApp/Signal/CLI）
  - 支持 `hermes claw migrate` 导入 OpenClaw 工作流
  - **Skill 机制**：内置 Skill 注册表，支持动态加载/卸载，可复用社区 Skill
- **OpenHuman**（tinyhumans，2026 年 2 月发布）
  - Rust + Tauri 构建，桌面优先，GNU GPL-3.0 许可证
  - Memory Tree：本地 SQLite 存储，整合 118+ 数据源（Gmail/Slack/GitHub/Notion/Stripe 等）
  - 内置工具：网页搜索/爬虫、文件系统/Git/lint/test、浏览器控制、定时任务、语音（STT/TTS）
  - TokenJuice 压缩成本，Ollama 本地 AI 支持（隐私优先）
  - Trending #1 on GitHub（2026 年 5 月）
  - **Skill 机制**：内置 Skill 系统，支持自定义扩展工具集
- **OpenClaw**（TopGitHub，370k+ stars）
  - 50+ 平台集成，成熟的 Skill 市场和丰富的预置工具
  - 支持工作流编排、自动化脚本、多平台消息推送（Telegram/Discord/Slack/WhatsApp 等）
  - 2026 年 3 月有安全事件，谨慎选，建议隔离环境使用
  - 提供 `claw migrate` 导入工作流，可与 Hermes 互通
- **Claude Code Router**（可选）
  - 多 AI 引擎路由，自动切换最优模型，降低 Token 成本
  - 支持 Claude / GPT / Gemini 等统一调用
  - 项目级 Agent 管理，适合需要灵活切换模型的场景
- 端到端走通：用 Hermes 或 OpenHuman 跑一条完整任务（读取文件 / 查天气 / 发消息）

> 📂 代码示例：[s05_open_source](../demo/ai-agent/s05_open_source/) — Hermes Agent / OpenHuman / OpenClaw
> 安装说明

### 下午：MCP 协议与连接（3 小时）

#### 7. 为什么需要 MCP

- 本地工具 vs 跨进程/跨语言工具
- MCP 定位：AI 应用的 "USB-C"，统一工具协议
- 生态：5000+ MCP Servers，Cursor / Claude Code / Windsurf / OpenAI 等均已集成

#### 8. MCP 协议概览

- **传输层**：stdio（本地父子进程）/ SSE（HTTP 长连接）
- **消息层**：JSON-RPC 2.0（id / method / params / result / error）
- **核心方法**：
  - `initialize`：握手，交换 capabilities
  - `tools/list`：列出可用工具
  - `tools/call`：调用指定工具
  - `resources/list` / `resources/read`：资源（选讲）
- **官方 SDK**：TypeScript SDK（@modelcontextprotocol/server）+ Python SDK（mcp）

> 📂 代码示例：[s07_mcp_protocol](../demo/ai-agent/s07_mcp_protocol/) — JSON-RPC 结构 + 核心方法解析

#### 9. 最小 MCP Client 实战

- 用 Claude Agent SDK 或 OpenAI Agents SDK 内置 MCP Client
- 连接官方示例 Server（如 filesystem server）
- 发送 `tools/list` → 解析响应 → 发送 `tools/call` → 查看结果
- 理解请求/响应 JSON 结构

> 📂 代码示例：[s08_mcp_client](../demo/ai-agent/s08_mcp_client/) — 用 SDK 连接官方 MCP Server

#### 10. Day 1 小结与练习

- 总结：主循环 + 工具分发 + 三层压缩 + MCP 协议角色
- 练习：用 SDK 内置 MCP Client 调用社区 MCP Server

---

## 第二天：MCP Server 底层设计与实现

### 上午：MCP Server 架构（3 小时）

#### 11. MCP Server 职责与生命周期

- 对外暴露 Tools / Resources；接收 JSON-RPC 请求，执行并返回
- 生命周期：启动（读配置）→ 运行（接收/分发）→ 关闭（清理）
- 与「进程内工具调用」的对比：序列化/反序列化、跨进程

> 📂 代码示例：[s10_mcp_server_lifecycle](../demo/ai-agent/s10_mcp_server_lifecycle/) — 启动→运行→关闭骨架

#### 12. JSON-RPC 路由与分发

- 请求解析：校验 JSON-RPC 2.0 格式（jsonrpc / id / method / params）
- 路由表：`method` → 处理函数（如 `initialize` / `tools/list` / `tools/call`）
- 响应构造：成功 `{"jsonrpc":"2.0","id":...,"result":...}` / 失败 `"error": {"code", "message"}`
- 实战：用 Python 实现最小骨架（仅支持 stdio）

> 📂 代码示例：[s11_jsonrpc_routing](../demo/ai-agent/s11_jsonrpc_routing/) — 路由表 + 响应构造

#### 13. 工具的注册与执行

- 工具元数据：name / description / inputSchema（JSON Schema）
- `tools/list` 实现：返回所有已注册工具
- `tools/call` 实现：根据 name + arguments 执行对应逻辑
- 错误处理：参数缺失/类型错误/执行异常 → JSON-RPC error
- 实战：注册 2～3 个真实工具（如 read_file、get_time、calc）

> 📂 代码示例：[s12_tool_registration](../demo/ai-agent/s12_tool_registration/) — tools/list + tools/call
> 实现

#### 14. 用官方 SDK 快速搭建 Server（选讲）

- Python SDK：`from mcp.server.stdio import stdio_server`
- 定义工具：用 `@tool` 装饰器或 `Server` constructor
- 专注业务逻辑，传输层由 SDK 处理

> 📂 代码示例：[s13_mcp_sdk_server](../demo/ai-agent/s13_mcp_sdk_server/) — Python MCP SDK @tool 装饰器

### 下午：传输层与完整实战（3 小时）

#### 15. 传输层实现

- **stdio**：每行一个 JSON-RPC，stdin 读 / stdout 写，注意 buffer + flush
- **SSE**：HTTP 长连接，Server 按 `data: {...}\n\n` 推送事件
- 协议与传输解耦：同一套「路由 + 执行」，仅替换 IO 层

> 📂 代码示例：[s14_transport](../demo/ai-agent/s14_transport/) — stdio + SSE 两种传输

#### 16. Resources 与 Prompts（选讲）

- Resources：只读数据（文件/配置/API 响应），`resources/list` / `resources/read`
- Prompts：预定义模板，供 Client 获取后填变量

> 📂 代码示例：[s15_resources_prompts](../demo/ai-agent/s15_resources_prompts/) — 资源与提示模板

#### 17. 完整实战：Agent + MCP Server 闭环

**方案一（推荐）**：用 Claude Agent SDK 作为 Client，内置 MCP 支持，连接自建 Server。

**方案二**：用官方 Python MCP SDK 写 Server，暴露 2～3 个工具：

- 示例工具：`get_weather` / `read_file_summary` / `get_system_info`
- 传输：stdio

**端到端步骤**：

1. 启动 MCP Server（stdio 模式）
2. Agent 发送 `initialize` → 握手
3. Agent 发送 `tools/list` → 获取工具列表
4. Agent 将工具列表作为「发给 LLM 的工具描述」
5. LLM 决定调工具 → Agent 发 `tools/call` → Server 执行 → 返回结果
6. 结果再喂给 LLM → 生成最终回复

**调试**：日志（请求/响应 JSON）、超时与重试、Server 崩溃降级

> 📂 代码示例：[s16_full_loop](../demo/ai-agent/s16_full_loop/) — 完整 Agent + MCP Server 端到端闭环

#### 18. Day 2 小结与扩展方向

- **官方/社区 MCP Server 选用**：filesystem / git / database / slack 等
- **生产环境**：认证（API Key / OAuth）、限流（token / rpm）、多实例部署
- **与课程 2 的衔接**：理解 LangChain/CrewAI 内部工具机制
- **持续关注**：Hermes Agent（快速迭代）、OpenHuman（社区热度）、OpenClaw（生态成熟）、MCP 官方 SDK 更新

> 📂 代码示例：[s17_day2_summary](../demo/ai-agent/s17_day2_summary/) — 总结 + 扩展方向

---

## 附录
