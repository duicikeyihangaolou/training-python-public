# s14: 传输层实现

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#14-传输层实现)

本节演示 stdio 和 SSE 两种传输方式，以及协议与传输解耦设计。

## 核心概念

**stdio**：每行一个 JSON-RPC，stdin 读 / stdout 写，注意 buffer + flush

**SSE**：HTTP 长连接，Server 按 `data: {...}\n\n` 推送事件

**协议与传输解耦**：同一套「路由 + 执行」，仅替换 IO 层

## 文件说明

| 文件                | 说明         |
| ----------------- | ---------- |
| `stdio_server.py` | stdio 传输实现 |
| `sse_server.py`   | SSE 传输实现   |

## 运行方式

```bash
cd s14_transport
python stdio_server.py      # stdio 模式
python sse_server.py        # SSE 模式（需要 curl 测试）
```
