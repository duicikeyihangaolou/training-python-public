#!/usr/bin/env python3
"""
s13: 用官方 MCP Python SDK 快速搭建 Server

本节演示如何使用 MCP Python SDK 的 @tool 装饰器快速定义工具，
传输层（stdio/SSE）由 SDK 处理，开发者只需专注业务逻辑。

运行方式：
    pip install mcp
    python sdk_server.py

注意：这个 demo 需要 mcp SDK，如果未安装会显示提示
"""

import sys

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, CallToolResult, TextContent
    from mcp import types
except ImportError:
    print("错误：需要安装 mcp SDK")
    print("  pip install mcp")
    sys.exit(1)

import asyncio
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# 使用 @tool 装饰器定义工具（推荐方式）
# --------------------------------------------------------------------------- #

# 创建 Server 实例
app = Server("demo-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    列出所有可用工具

    这是 Server 的入口点，Client 调用 tools/list 时触发
    """
    return [
        Tool(
            name="get_weather",
            description="查询指定城市的天气",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="calc",
            description="计算数学表达式",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """
    调用工具

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        CallToolResult，包含 content 列表
    """
    print(f"[Server] 调用工具: {name}({arguments})")

    if name == "get_weather":
        city = arguments.get("city", "未知")
        weather_db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C"}
        content = weather_db.get(city, f"不支持查询 {city}")
        return CallToolResult(content=[TextContent(type="text", text=content)])

    elif name == "calc":
        expression = arguments.get("expression", "0")
        try:
            result = eval(expression, {"__builtins__": {}})
            return CallToolResult(content=[TextContent(type="text", text=str(result))])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"错误: {e}")])

    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True
        )


# --------------------------------------------------------------------------- #
# 运行 Server
# --------------------------------------------------------------------------- #

async def main():
    """启动 MCP Server"""
    print("=" * 60)
    print("MCP Server (使用官方 SDK)")
    print("=" * 60)
    print("\nServer 启动，监听 stdio...")
    print("按 Ctrl+C 退出\n")

    # stdio_server 是 MCP SDK 提供的上下文管理器
    # 它处理 stdin/stdout 的 JSON-RPC 协议
    async with stdio_server() as (read, write):
        # 运行 Server，处理请求
        await app.run(read, write)


def demo_concept():
    """
    概念演示（不实际启动 Server）

    展示 SDK 的核心用法
    """
    print("=" * 60)
    print("MCP Python SDK 概念演示")
    print("=" * 60)

    print("""
MCP Python SDK 核心用法：

1. 创建 Server 实例
    app = Server("demo-server")

2. 使用 @tool 装饰器定义工具（两种方式）：

   方式 A：@list_tools + @call_tool（推荐）
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [Tool(name="get_weather", ...)]

    @app.call_tool()
    async def call_tool(name, arguments) -> CallToolResult:
        if name == "get_weather":
            return CallToolResult(content=[TextContent(...)])
        ...

   方式 B：Server constructor + @server.tool()
    server = Server("my-server")

    @server.tool(name="get_weather", description="...")
    async def get_weather(city: str) -> str:
        return f"{city} 天气晴朗"

3. 启动 Server（stdio 模式）
    async with stdio_server() as (read, write):
        await app.run(read, write)

优势：
- 传输层（stdio/SSE）由 SDK 处理
- 开发者专注业务逻辑（工具实现）
- 自动处理 JSON-RPC 协议
- 类型安全（pydantic 模型）
""")


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        # 实际启动 stdio Server
        asyncio.run(main())
    else:
        # 概念演示
        demo_concept()