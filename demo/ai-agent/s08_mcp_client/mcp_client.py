#!/usr/bin/env python3
"""
s08: 最小 MCP Client 实战

本节演示如何使用 MCP Python SDK 创建 Client、连接 Server、调用工具。

MCP Client 工作流程：
1. 创建 ClientSession
2. 发送 initialize 握手
3. 调用 tools/list 获取工具列表
4. 调用 tools/call 执行工具
5. 将工具结果返回给 Agent

运行方式：
    python mcp_client.py

依赖：
    pip install mcp
"""

import sys
import json

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
except ImportError:
    print("错误：需要安装 mcp SDK")
    print("  pip install mcp")
    sys.exit(1)


# --------------------------------------------------------------------------- #
# MCP Client 实现
# --------------------------------------------------------------------------- #

class MCPClient:
    """
    MCP Client 封装

    使用方式：
        async with MCPClient() as client:
            tools = await client.list_tools()
            result = await client.call_tool("get_weather", {"city": "北京"})
    """

    def __init__(self, server_command: list = None, server_cwd: str = None):
        """
        初始化 MCP Client

        Args:
            server_command: 启动 MCP Server 的命令，如 ["python", "server.py"]
            server_cwd: Server 工作目录
        """
        self.server_command = server_command or ["python", "-c", "print('mock server')"]
        self.server_cwd = server_cwd or "."
        self.session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        """连接到 MCP Server"""
        # stdio_client 返回一个异步上下文管理器
        stdio_context = stdio_client()

        # 启动并获取读/写流
        _, self.write = await stdio_context.__aenter__()

        # 创建 ClientSession
        self.session = ClientSession(self.read, self.write)

        # 初始化握手
        await self.session.__aenter__()
        await self.session.initialize()

        print("✓ MCP Client 已连接到 Server")

    async def list_tools(self) -> list:
        """
        获取所有可用工具

        Returns:
            工具列表，每个工具包含 name/description/inputSchema
        """
        if not self.session:
            raise RuntimeError("未连接，请先调用 connect()")

        response = await self.session.list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        调用指定工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果的字符串
        """
        if not self.session:
            raise RuntimeError("未连接，请先调用 connect()")

        result = await self.session.call_tool(tool_name, arguments)

        # result 是 CallToolResult，包含 content 列表
        if result.content:
            # 返回第一个 content block 的文本
            return result.content[0].text
        return ""

    async def disconnect(self):
        """断开与 MCP Server 的连接"""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None


# --------------------------------------------------------------------------- #
# 模拟 MCP Server（用于演示）
# --------------------------------------------------------------------------- #

def create_mock_server():
    """
    创建一个模拟的 MCP Server 脚本

    这个 Server 实现最简单的 tools/list 和 tools/call
    用于在没有真实 Server 时测试 Client
    """
    server_code = '''
import json
import sys

def handle_request(req):
    method = req.get("method", "")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mock-server", "version": "1.0.0"}
            }
        }
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "查询城市天气",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string", "description": "城市名称"}
                            },
                            "required": ["city"]
                        }
                    }
                ]
            }
        }
    elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name", "")
        args = params.get("arguments", {})

        if name == "get_weather":
            city = args.get("city", "未知")
            weather_db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C"}
            content = weather_db.get(city, f"不支持查询 {city} 的天气")
        else:
            content = f"Unknown tool: {name}"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": content}]}
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        resp = handle_request(req)
        print(json.dumps(resp), flush=True)
'''
    return server_code


# --------------------------------------------------------------------------- #
# 演示（使用模拟 Server）
# --------------------------------------------------------------------------- #

async def demo():
    """演示 MCP Client 连接模拟 Server"""
    print("=" * 60)
    print("MCP Client 实战")
    print("=" * 60)

    # 创建模拟 Server 脚本
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(create_mock_server())
        server_script = f.name

    print(f"\n1. 启动模拟 MCP Server: {server_script}")

    # 启动 Server 作为子进程
    proc = subprocess.Popen(
        [sys.executable, server_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("2. 创建 MCP Client")

    # 注意：实际使用中，应该用 asyncio 和 stdio_client
    # 这里为了简化，使用同步模拟

    print("\n3. 发送 initialize 请求")
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    proc.stdin.write(json.dumps(init_req) + "\n")
    proc.stdin.flush()
    init_resp = json.loads(proc.stdout.readline())
    print(f"   响应：{init_resp}")

    print("\n4. 发送 tools/list 请求")
    list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc.stdin.write(json.dumps(list_req) + "\n")
    proc.stdin.flush()
    list_resp = json.loads(proc.stdout.readline())
    print(f"   响应：{list_resp}")
    tools = list_resp.get("result", {}).get("tools", [])
    print(f"   发现 {len(tools)} 个工具：{[t['name'] for t in tools]}")

    print("\n5. 发送 tools/call 请求")
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "get_weather", "arguments": {"city": "北京"}}
    }
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()
    call_resp = json.loads(proc.stdout.readline())
    print(f"   响应：{call_resp}")
    content = call_resp.get("result", {}).get("content", [])
    if content:
        print(f"   工具返回：{content[0].get('text', '')}")

    # 清理
    proc.terminate()
    import os
    os.unlink(server_script)

    print("\n✓ MCP Client 演示完成")


def demo_sync():
    """同步版本的演示（不实际启动 Server）"""
    print("=" * 60)
    print("MCP Client 概念演示（同步模拟）")
    print("=" * 60)

    print("""
MCP Client 工作流程：

1. 启动 MCP Server（子进程，stdio 模式）
   subprocess.Popen([sys.executable, "server.py"], stdin=PIPE, stdout=PIPE)

2. 发送 initialize 握手
   {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}
   ← {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {...}}}

3. 发送 tools/list 获取工具列表
   {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
   ← {"jsonrpc": "2.0", "id": 2, "result": {"tools": [...]}}

4. LLM 决定调用 get_weather(city="北京")
   {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
     "name": "get_weather", "arguments": {"city": "北京"}}}
   ← {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"text": "晴 15-25°C"}]}}

5. 工具结果返回给 LLM，LLM 生成最终回复

实际使用中，推荐用官方 SDK：
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("get_weather", {"city": "北京"})
""")


def main():
    """主入口"""
    import asyncio

    # 检查是否有 mcp SDK
    try:
        from mcp import ClientSession
        print("检测到 mcp SDK，使用真实异步演示")
        asyncio.run(demo())
    except ImportError:
        print("未检测到 mcp SDK，使用同步概念演示")
        demo_sync()


if __name__ == "__main__":
    main()