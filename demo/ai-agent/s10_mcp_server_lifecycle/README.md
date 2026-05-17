# s10: MCP Server 生命周期

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#10-mcp-server-职责与生命周期)

本节演示 MCP Server 的生命周期：启动→运行→关闭。

## 核心概念

**MCP Server 职责**：

- 对外暴露 Tools / Resources
- 接收 JSON-RPC 请求，执行并返回响应

**生命周期**：

1. **启动**：读取配置（传输方式 stdio/SSE），初始化路由表
2. **运行**：循环接收请求（stdio 下读 stdin；SSE 下处理 HTTP），按 method 分发到处理函数
3. **关闭**：清理资源，优雅退出

## 文件说明

| 文件                         | 说明            |
| -------------------------- | ------------- |
| `server_lifecycle.py`      | Server 生命周期骨架 |
| `test_server_lifecycle.py` | 单元测试          |

## 运行方式

```bash
cd s10_mcp_server_lifecycle
python server_lifecycle.py
```

## 测试

```bash
pytest test_server_lifecycle.py -v
```
