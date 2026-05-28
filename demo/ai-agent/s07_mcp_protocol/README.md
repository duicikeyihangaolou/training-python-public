# s07: MCP 协议概览

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#7-mcp-协议概览)

本节深入讲解 MCP 协议的结构：传输层、消息层和核心方法。

## 核心概念

**MCP = Model Context Protocol**

- **传输层**：stdio（本地父子进程）/ SSE（HTTP 长连接）
- **消息层**：JSON-RPC 2.0
- **核心方法**：initialize / tools/list / tools/call / resources/list / resources/read

## JSON-RPC 2.0 消息格式

**请求**：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {"city": "北京"}
  }
}
```

**成功响应**：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": "北京天气：晴，15-25°C"
  }
}
```

**错误响应**：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

## 文件说明

| 文件               | 说明                              |
| ------------------ | --------------------------------- |
| `protocol_demo.py` | 解析 JSON-RPC 结构 + MCP 核心方法 |
| `test_protocol.py` | 单元测试                          |

## 运行方式

```bash
cd s07_mcp_protocol
python protocol_demo.py
```

## 测试

```bash
pytest test_protocol.py -v
```
