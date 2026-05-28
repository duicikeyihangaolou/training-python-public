# AI Agent 端到端代码示例库

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md)

本目录包含 AI Agent 全栈开发课程的全部代码示例，每个 demo 独立可运行，配有 README 说明和单元测试。

---

## 目录结构

| 序号                               | 名称                    | 对应章节 | 说明                                         |
| ---------------------------------- | ----------------------- | -------- | -------------------------------------------- |
| [s01](./s01_agent_loop/)           | Agent 主循环            | 第 1 节  | 从零实现 ~30 行主循环，感知→决策→执行闭环    |
| [s02](./s02_tool_dispatch/)        | 工具描述与分发          | 第 2 节  | TOOLS Schema + TOOL_HANDLERS + 分发函数      |
| [s03](./s03_context_compact/)      | 上下文与会话持久化      | 第 3 节  | 三层压缩 + JSONL 持久化 + 3 阶段溢出保护     |
| [s04](./s04_framework_comparison/) | 主流框架对比            | 第 4 节  | Claude SDK / OpenAI SDK / CrewAI / LangGraph |
| [s05](./s05_open_source/)          | 开源 Agent 框架         | 第 5 节  | Hermes Agent / OpenHuman / OpenClaw 安装说明 |
| [s06](./s06_why_mcp/)              | 为什么需要 MCP          | 第 6 节  | 本地工具 vs MCP 工具对比                     |
| [s07](./s07_mcp_protocol/)         | MCP 协议概览            | 第 7 节  | JSON-RPC 结构 + 核心方法解析                 |
| [s08](./s08_mcp_client/)           | 最小 MCP Client         | 第 8 节  | 用 SDK 连接官方 MCP Server                   |
| [s10](./s10_mcp_server_lifecycle/) | MCP Server 生命周期     | 第 10 节 | 启动→运行→关闭骨架                           |
| [s11](./s11_jsonrpc_routing/)      | JSON-RPC 路由与分发     | 第 11 节 | 路由表 + 响应构造                            |
| [s12](./s12_tool_registration/)    | 工具注册与执行          | 第 12 节 | tools/list + tools/call 实现                 |
| [s13](./s13_mcp_sdk_server/)       | SDK 快速搭建 Server     | 第 13 节 | Python MCP SDK @tool 装饰器                  |
| [s14](./s14_transport/)            | 传输层实现              | 第 14 节 | stdio + SSE 两种传输                         |
| [s15](./s15_resources_prompts/)    | Resources 与 Prompts    | 第 15 节 | 资源与提示模板                               |
| [s16](./s16_full_loop/)            | Agent + MCP Server 闭环 | 第 16 节 | 完整端到端实战                               |
| [s17](./s17_day2_summary/)         | Day 2 小结              | 第 17 节 | 总结 + 扩展方向                              |

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库后，在 demo/ai-agent 目录下：
cd /Users/wuwenxiang/local/github-mine/training-python-public/demo/ai-agent

# 安装全局依赖
pip install -r requirements.txt

# 配置 API Key（两种方式二选一）
# 方式一：环境变量
export MINIMAX_API_KEY=sk-cp-你的key
export MINIMAX_API_URL=https://api.minimaxi.com/v1
export MINIMAX_MODEL=MiniMax-M2.7

# 方式二：创建 .env 文件（不要提交到 git）
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 2. 运行任意 demo

```bash
# 例如运行 s01 Agent 主循环
cd s01_agent_loop
python agent_loop.py
```

### 3. 运行单元测试

```bash
# 运行所有测试
pytest . -v

# 运行单个 demo 的测试
pytest s01_agent_loop/ -v
```

---

## API 配置说明

所有 demo 默认使用以下配置（调试用）：

| 配置项       | 值                            |
| ------------ | ----------------------------- |
| API URL      | `https://api.minimaxi.com/v1` |
| 模型         | `MiniMax-M2.7`                |
| Key 获取方式 | 环境变量 `MINIMAX_API_KEY`    |

如需使用其他 API（如 OpenAI / Anthropic），请在各 demo 的 `.env.example` 中查看说明。

---

## 目录约定

- 每个 demo 目录下有 `README.md` 说明本节内容和运行方式
- 每个 `.py` 文件对应一个独立功能，配有单元测试（`test_*.py`）
- 全局依赖在根目录 `requirements.txt`，各 demo 独立依赖在 `requirements.txt`（可选）
