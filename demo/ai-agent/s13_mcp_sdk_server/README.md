# s13: 用官方 SDK 快速搭建 Server

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#13-用官方-sdk-快速搭建-server选讲)

本节演示使用 MCP Python SDK 快速搭建 Server。

## 核心概念

使用 `@tool` 装饰器或 `Server` constructor 定义工具，传输层由 SDK 处理。

## 文件说明

| 文件            | 说明                |
| --------------- | ------------------- |
| `sdk_server.py` | SDK 快速搭建 Server |

## 运行方式

```bash
cd s13_mcp_sdk_server
pip install mcp
python sdk_server.py
```

## 注意

需要安装 `mcp` SDK：`pip install mcp`
