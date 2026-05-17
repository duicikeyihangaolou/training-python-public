#!/usr/bin/env python3
"""
s06: 为什么需要 MCP — 本地工具 vs 跨进程工具

本节演示两种工具调用方式的区别：
1. 本地工具：同一进程内直接函数调用
2. MCP 工具：跨进程通过协议调用（stdio/SSE）

核心洞察：
- 本地工具只能在同一个 Python 进程内使用
- MCP 工具可以跨进程、跨语言使用
- MCP 是 AI 应用的"USB-C"，统一了工具调用的协议

运行方式：
    python local_vs_mcp.py
"""

import json
import subprocess
import sys
from typing import Callable, Any


# --------------------------------------------------------------------------- #
# Part 1: 本地工具调用（同一进程）
# --------------------------------------------------------------------------- #

def get_weather_local(city: str) -> str:
    """本地天气查询（直接函数调用）"""
    db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C"}
    return db.get(city, f"不支持 {city}")


def call_local_tool(tool_name: str, tool_input: dict, handlers: dict) -> str:
    """
    调用本地工具（同一进程内）

    特点：
    - 直接函数调用，没有序列化开销
    - 调试简单，直接看调用栈
    - 但只能在同一个进程内使用
    """
    handler = handlers.get(tool_name)
    if not handler:
        return f"Error: unknown tool {tool_name}"
    return handler(**tool_input)


# --------------------------------------------------------------------------- #
# Part 2: MCP 工具调用（跨进程）
# --------------------------------------------------------------------------- #

def mcp_request(method: str, params: dict = None) -> dict:
    """
    发送 MCP 请求（通过 stdio 子进程）

    这是一个简化的 MCP 客户端实现：
    - 启动 MCP Server 作为子进程
    - 通过 stdin/stdout 发送 JSON-RPC 请求
    - 接收 JSON-RPC 响应

    实际项目中，会使用官方 MCP SDK
    """
    # 构建 JSON-RPC 2.0 请求
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }

    # 序列化并发送到子进程（这里用 subprocess 模拟）
    request_json = json.dumps(request)

    # 实际场景中，这里会启动 MCP Server 并通信
    # 这里我们模拟一个响应
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "get_weather", "description": "查询天气", "inputSchema": {"type": "object"}}
                ]
            }
        }
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if tool_name == "get_weather":
            result = get_weather_local(arguments.get("city", "未知"))
        else:
            result = f"Unknown tool: {tool_name}"
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": result}
        }

    return {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}


# --------------------------------------------------------------------------- #
# Part 3: 对比演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("本地工具 vs MCP 工具")
    print("=" * 60)

    # 本地工具注册表
    local_handlers = {
        "get_weather": get_weather_local,
    }

    print("\n1. 本地工具调用（同一进程）")
    print("-" * 40)
    print("代码：call_local_tool('get_weather', {'city': '北京'}, handlers)")
    result = call_local_tool("get_weather", {"city": "北京"}, local_handlers)
    print(f"结果：{result}")
    print("特点：直接函数调用，无序列化开销")

    print("\n2. MCP 工具调用（跨进程）")
    print("-" * 40)
    print("步骤：")
    print("  1. Agent → MCP Client → JSON-RPC → stdio")
    print("  2. MCP Server（子进程）接收请求")
    print("  3. Server 执行工具，返回 JSON-RPC 响应")
    print("  4. MCP Client 解析响应，返回给 Agent")

    # 演示 MCP 请求/响应
    print("\n  发送 MCP 请求：")
    print("  → tools/list")
    response = mcp_request("tools/list")
    print(f"  ← {response}")

    print("\n  发送工具调用：")
    print("  → tools/call (name='get_weather', arguments={'city': '上海'})")
    response = mcp_request("tools/call", {
        "name": "get_weather",
        "arguments": {"city": "上海"}
    })
    print(f"  ← {response}")

    print("\n3. 核心区别")
    print("-" * 40)
    print("""
| 方面 | 本地工具 | MCP 工具 |
|------|---------|---------|
| 进程 | 同一进程 | 跨进程/跨语言 |
| 调用 | 直接函数调用 | JSON-RPC over stdio/SSE |
| 调试 | 简单，直接看调用栈 | 需要看 Server 日志 |
| 扩展 | 只能扩展同语言 | 可以调用任何语言写的工具 |
| 延迟 | 低（无序列化） | 高（有序列化/反序列化） |
""")

    print("\n4. MCP 的价值")
    print("-" * 40)
    print("""
MCP = Model Context Protocol（AI 应用的"USB-C"）

问题：在 MCP 之前，每个 Agent 框架都有自己的工具调用方式
- LangChain 用 Function Calling
- CrewAI 用自定义格式
- 换框架 = 重写所有工具

MCP 的解决方案：
- 统一协议：tools/list, tools/call 等标准方法
- 跨框架：Claude/CrewAI/LangGraph 都可以用同一个 MCP Server
- 生态：5000+ MCP Servers 可用

就像 USB-C：
- 统一接口，一个充电器充所有设备
- 统一协议，一个 Agent 调用所有工具
""")


if __name__ == "__main__":
    demo()