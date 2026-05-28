# s06: 为什么需要 MCP

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#6-为什么需要-mcp)

本节演示**本地工具**和**跨进程工具**的区别，引出 MCP 的价值。

## 核心概念

**本地工具 vs MCP 工具**：

```
本地工具（同一进程）：
  Agent → TOOL_HANDLERS["get_weather"]()  ← 函数直接调用

MCP 工具（跨进程）：
  Agent → MCP Client → stdio/SSE → MCP Server → get_weather()
```

**为什么需要 MCP**：

- 本地工具：只能在同一个 Python 进程内调用
- 跨进程工具：Python 可以调用 Node.js/Go/Rust 写的工具
- 跨语言工具：C 可以调用 Python 的功能
- 标准化协议：不同 Agent（Claude/CrewAI/LangGraph）可以用同一套工具

## 文件说明

| 文件                   | 说明                             |
| ---------------------- | -------------------------------- |
| `local_vs_mcp.py`      | 演示本地工具调用 vs MCP 工具调用 |
| `test_local_vs_mcp.py` | 单元测试                         |

## 运行方式

```bash
cd s06_why_mcp
python local_vs_mcp.py
```

## 测试

```bash
pytest test_local_vs_mcp.py -v
```
