#!/usr/bin/env python3
"""
s07: MCP 协议概览 — JSON-RPC 结构与核心方法

本节演示：
1. JSON-RPC 2.0 的请求/响应格式
2. MCP 的核心方法（initialize / tools/list / tools/call）
3. 工具的 JSON Schema

运行方式：
    python protocol_demo.py
"""

import json
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# JSON-RPC 2.0 结构
# --------------------------------------------------------------------------- #

class JSONRPCRequest:
    """JSON-RPC 2.0 请求"""

    def __init__(self, method: str, params: dict = None, id: Any = None):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params or {}
        self.id = id

    def to_dict(self) -> dict:
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
            "id": self.id
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> "JSONRPCRequest":
        return cls(
            method=data["method"],
            params=data.get("params"),
            id=data.get("id")
        )


class JSONRPCResponse:
    """JSON-RPC 2.0 响应"""

    def __init__(self, id: Any, result: dict = None, error: dict = None):
        self.jsonrpc = "2.0"
        self.id = id
        self.result = result
        self.error = error

    def to_dict(self) -> dict:
        base = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            base["error"] = self.error
        else:
            base["result"] = self.result
        return base

    def is_success(self) -> bool:
        return self.error is None


# --------------------------------------------------------------------------- #
# MCP 核心方法
# --------------------------------------------------------------------------- #

def create_initialize_request() -> dict:
    """创建 initialize 请求"""
    return JSONRPCRequest(
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "ai-agent-demo",
                "version": "1.0.0"
            }
        },
        id=1
    ).to_dict()


def create_tools_list_request() -> dict:
    """创建 tools/list 请求"""
    return JSONRPCRequest(
        method="tools/list",
        params={},
        id=2
    ).to_dict()


def create_tools_call_request(tool_name: str, arguments: dict) -> dict:
    """创建 tools/call 请求"""
    return JSONRPCRequest(
        method="tools/call",
        params={
            "name": tool_name,
            "arguments": arguments
        },
        id=3
    ).to_dict()


def create_resources_list_request() -> dict:
    """创建 resources/list 请求"""
    return JSONRPCRequest(
        method="resources/list",
        params={},
        id=4
    ).to_dict()


# --------------------------------------------------------------------------- #
# 工具 Schema 示例
# --------------------------------------------------------------------------- #

def get_weather_schema() -> dict:
    """get_weather 工具的 JSON Schema"""
    return {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如：北京、上海、东京"
                }
            },
            "required": ["city"]
        }
    }


def read_file_schema() -> dict:
    """read_file 工具的 JSON Schema"""
    return {
        "name": "read_file",
        "description": "读取文件内容",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "limit": {
                    "type": "integer",
                    "description": "最多返回行数（可选）"
                }
            },
            "required": ["path"]
        }
    }


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("MCP 协议概览")
    print("=" * 60)

    # 1. JSON-RPC 请求格式
    print("\n1. JSON-RPC 2.0 请求格式")
    print("-" * 40)
    req = create_initialize_request()
    print(f"请求：{json.dumps(req, indent=2, ensure_ascii=False)}")

    # 2. 成功响应
    print("\n2. 成功响应格式")
    print("-" * 40)
    success_resp = JSONRPCResponse(
        id=1,
        result={
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "example-server", "version": "1.0.0"}
        }
    )
    print(f"响应：{json.dumps(success_resp.to_dict(), indent=2, ensure_ascii=False)}")

    # 3. 错误响应
    print("\n3. 错误响应格式")
    print("-" * 40)
    error_resp = JSONRPCResponse(
        id=2,
        error={"code": -32602, "message": "Invalid params", "data": {"param": "city"}}
    )
    print(f"响应：{json.dumps(error_resp.to_dict(), indent=2, ensure_ascii=False)}")

    # 4. MCP 核心方法
    print("\n4. MCP 核心方法")
    print("-" * 40)
    methods = [
        ("initialize", "握手，交换 capabilities"),
        ("tools/list", "列出所有可用工具"),
        ("tools/call", "调用指定工具"),
        ("resources/list", "列出所有可用资源"),
        ("resources/read", "读取指定资源"),
    ]
    print(f"{'方法':<20} {'说明'}")
    print("-" * 40)
    for method, desc in methods:
        print(f"{method:<20} {desc}")

    # 5. 工具 Schema
    print("\n5. 工具 JSON Schema 示例")
    print("-" * 40)
    schema = get_weather_schema()
    print(f"get_weather Schema：")
    print(json.dumps(schema, indent=2, ensure_ascii=False))

    # 6. tools/list 响应
    print("\n6. tools/list 响应示例")
    print("-" * 40)
    tools_response = {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "tools": [get_weather_schema(), read_file_schema()]
        }
    }
    print(json.dumps(tools_response, indent=2, ensure_ascii=False))

    # 7. tools/call 流程
    print("\n7. tools/call 完整流程")
    print("-" * 40)
    print("""
    Agent                    MCP Client                 MCP Server
      |                          |                          |
      |  tools/call              |                          |
      |  {"name": "get_weather", |                          |
      |   "arguments": {"city": "北京"}}                   |
      | ──────────────────────> |                          |
      |                          | stdin写入 JSON-RPC       |
      |                          | ──────────────────────>  |
      |                          |                          | 解析请求
      |                          |                          | 执行 get_weather
      |                          |                          | stdout写出响应
      |                          | <──────────────────────── |
      |                          |  {"result": {"content": ...}} |
      | <────────────────────── |                          |
      | {"content": "北京天气..."}                          |
      |                          |                          |
    """)


if __name__ == "__main__":
    demo()