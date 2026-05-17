#!/usr/bin/env python3
"""
s10: MCP Server 生命周期

本节演示 MCP Server 的三个阶段：
1. 启动（初始化）
2. 运行（接收请求→分发→处理→响应）
3. 关闭（清理）

这是一个最小骨架，不依赖官方 SDK，用于理解底层原理。

运行方式：
    python server_lifecycle.py
"""

import json
import sys
from typing import Callable, Optional
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# 生命周期状态
# --------------------------------------------------------------------------- #

@dataclass
class ServerState:
    """Server 状态"""
    running: bool = False
    request_count: int = 0

    def start(self):
        self.running = True
        print(f"[Server] 启动完成")

    def stop(self):
        self.running = False
        print(f"[Server] 关闭完成，共处理 {self.request_count} 个请求")


# --------------------------------------------------------------------------- #
# 请求路由表
# --------------------------------------------------------------------------- #

class Router:
    """
    请求路由器

    将 method 映射到处理函数
    """

    def __init__(self):
        self.handlers = {}

    def register(self, method: str, handler: Callable):
        """注册处理函数"""
        self.handlers[method] = handler
        print(f"[Router] 注册 handler: {method}")

    def dispatch(self, method: str, params: dict, state: ServerState) -> dict:
        """
        分发请求到对应处理函数

        Args:
            method: 方法名（如 "tools/list"）
            params: 参数字典
            state: Server 状态

        Returns:
            JSON-RPC 响应字典
        """
        state.request_count += 1

        handler = self.handlers.get(method)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        try:
            result = handler(params)
            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": result
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {exc}"
                }
            }


# --------------------------------------------------------------------------- #
# 处理函数
# --------------------------------------------------------------------------- #

def handle_initialize(params: dict) -> dict:
    """处理 initialize 请求"""
    client_info = params.get("clientInfo", {})
    print(f"[Handler] initialize from {client_info.get('name', 'unknown')}")
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {}
        },
        "serverInfo": {
            "name": "demo-server",
            "version": "1.0.0"
        }
    }


def handle_tools_list(params: dict) -> dict:
    """处理 tools/list 请求"""
    print(f"[Handler] tools/list")
    return {
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


def handle_tools_call(params: dict) -> dict:
    """处理 tools/call 请求"""
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})
    print(f"[Handler] tools/call: {tool_name}({arguments})")

    if tool_name == "get_weather":
        city = arguments.get("city", "未知")
        weather_db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C"}
        content = weather_db.get(city, f"不支持查询 {city}")
        return {"content": [{"type": "text", "text": content}]}
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def handle_resources_list(params: dict) -> dict:
    """处理 resources/list 请求"""
    print(f"[Handler] resources/list")
    return {"resources": []}


# --------------------------------------------------------------------------- #
# Server 主循环
# --------------------------------------------------------------------------- #

def run_server():
    """
    运行 Server（stdio 模式）

    从 stdin 读取 JSON-RPC 请求，从 stdout 写出响应
    """
    state = ServerState()
    router = Router()

    # 注册处理函数
    router.register("initialize", handle_initialize)
    router.register("tools/list", handle_tools_list)
    router.register("tools/call", handle_tools_call)
    router.register("resources/list", handle_resources_list)

    # 启动
    state.start()

    print("[Server] 开始监听 stdin（stdio 模式）")
    print("按 Ctrl+C 退出\n")

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            # 解析请求
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Server] 无效 JSON: {line[:50]}...")
                continue

            method = request.get("method", "")
            params = request.get("params", {})
            req_id = request.get("id")

            # 分发请求
            response = router.dispatch(method, params, state)

            # 设置 id
            if "id" in response and response["id"] is None:
                response["id"] = req_id

            # 发送响应
            resp_json = json.dumps(response, ensure_ascii=False)
            print(f"[Server] → {resp_json[:80]}...")
            print(resp_json, flush=True)

    except KeyboardInterrupt:
        print("\n[Server] 收到退出信号")
    finally:
        state.stop()


# --------------------------------------------------------------------------- #
# 演示（非 stdio 模式）
# --------------------------------------------------------------------------- #

def demo_in_memory():
    """
    内存中演示 Server 生命周期

    不实际监听 stdin，只演示概念
    """
    print("=" * 60)
    print("MCP Server 生命周期演示（内存模式）")
    print("=" * 60)

    state = ServerState()
    router = Router()

    # 注册
    router.register("initialize", handle_initialize)
    router.register("tools/list", handle_tools_list)
    router.register("tools/call", handle_tools_call)

    print("\n--- 阶段 1：启动 ---")
    state.start()
    print("Router 注册了 3 个 handler")

    print("\n--- 阶段 2：运行，处理请求 ---")

    # 请求 1: initialize
    print("\n请求 1: initialize")
    resp = router.dispatch("initialize", {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "test-client", "version": "1.0"}
    }, state)
    print(f"响应: {resp}")

    # 请求 2: tools/list
    print("\n请求 2: tools/list")
    resp = router.dispatch("tools/list", {}, state)
    print(f"响应: 包含 {len(resp['result']['tools'])} 个工具")

    # 请求 3: tools/call
    print("\n请求 3: tools/call")
    resp = router.dispatch("tools/call", {
        "name": "get_weather",
        "arguments": {"city": "北京"}
    }, state)
    print(f"响应: {resp['result']}")

    print("\n--- 阶段 3：关闭 ---")
    state.stop()


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #

def main():
    """主入口"""
    if "--stdio" in sys.argv:
        # stdio 模式：真实监听 stdin
        run_server()
    else:
        # 内存模式：演示概念
        demo_in_memory()


if __name__ == "__main__":
    main()