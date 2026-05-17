# s16: 完整实战 Agent + MCP Server 闭环

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#16-完整实战-agent-mcp-server-闭环)

本节演示完整的 Agent + MCP Server 端到端闭环。

## 核心流程

1. 启动 MCP Server（stdio 模式）
2. Agent 发送 `initialize` → 握手
3. Agent 发送 `tools/list` → 获取工具列表
4. Agent 将工具列表转为 LLM 可读格式
5. LLM 决定调工具 → Agent 发 `tools/call` → Server 执行
6. 结果返回给 Agent → 再喂给 LLM → 生成最终回复

## 文件说明

| 文件                | 说明                   |
| ----------------- | -------------------- |
| `mcp_server.py`   | 自建 MCP Server（stdio） |
| `agent_client.py` | Agent 作为 MCP Client  |

## 运行方式

```bash
cd s16_full_loop

# 终端 1：启动 MCP Server
python mcp_server.py

# 终端 2：运行 Agent Client（另一进程）
python agent_client.py

# 或者在一个终端里先后运行（用管道连接）
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python mcp_server.py
```
