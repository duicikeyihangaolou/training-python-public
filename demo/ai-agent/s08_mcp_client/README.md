# s08: 最小 MCP Client 实战

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#8-最小-mcp-client-实战)

本节演示如何使用 MCP SDK 连接 MCP Server 并调用工具。

## 核心概念

**MCP Client 职责**：

1. 启动 MCP Server（stdio 模式）
2. 发送 `initialize` 握手
3. 发送 `tools/list` 获取工具列表
4. 将工具列表转为 LLM 可读的格式
5. LLM 决定调工具 → 发送 `tools/call` → 解析结果

## 文件说明

| 文件                 | 说明                |
| -------------------- | ------------------- |
| `mcp_client.py`      | MCP Client 完整实现 |
| `test_mcp_client.py` | 单元测试            |

## 运行方式

```bash
cd s08_mcp_client
python mcp_client.py
```

## 测试

```bash
pytest test_mcp_client.py -v
```

## 依赖

```bash
pip install mcp
```
