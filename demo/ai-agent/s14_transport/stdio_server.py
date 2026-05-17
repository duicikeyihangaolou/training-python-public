#!/usr/bin/env python3
"""
s14: 传输层实现 — stdio 模式

本节演示 stdio 传输的实现细节：
- 每行一个 JSON-RPC 消息
- stdin 读入，stdout 写出
- 注意 buffer + flush 避免卡住

运行方式：
    python stdio_server.py

测试：
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python stdio_server.py
"""

import json
import sys
from typing import Callable


# --------------------------------------------------------------------------- #
# stdio 读写
# --------------------------------------------------------------------------- #

def read_request() -> dict:
    """
    从 stdin 读取一行 JSON-RPC 请求

    注意：
    - 使用 sys.stdin.readline() 读取一行
    - strip() 去除换行符
    - 如果返回 None，说明 stdin 关闭
    """
    line = sys.stdin.readline()
    if line is None:
        return None
    line = line.strip()
    if not line:
        return None
    return json.loads(line)


def write_response(response: dict) -> None:
    """
    向 stdout 写入 JSON-RPC 响应

    注意：
    - flush() 是必须的，否则可能被缓冲
    - 确保每条响应一行，便于对方读取
    """
    line = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
# stdio Server 模板
# --------------------------------------------------------------------------- #

def create_stdio_server(handlers: dict) -> Callable:
    """
    创建 stdio Server

    Args:
        handlers: method -> handler function 的字典

    Returns:
        可调用的 server 函数
    """
    def server():
        """stdio Server 主循环"""
        print("[Server] stdio Server 启动", file=sys.stderr)

        while True:
            # 读取请求
            request = read_request()
            if request is None:
                print("[Server] stdin 关闭，退出", file=sys.stderr)
                break

            # 解析请求
            method = request.get("method", "")
            params = request.get("params", {})
            req_id = request.get("id")

            # 分发请求
            handler = handlers.get(method)
            if handler:
                try:
                    result = handler(params)
                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                except Exception as exc:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}}
            else:
                response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

            # 发送响应
            write_response(response)

    return server


# --------------------------------------------------------------------------- #
# 演示用 handlers
# --------------------------------------------------------------------------- #

def handle_initialize(params):
    return {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "stdio-demo", "version": "1.0"}}


def handle_tools_list(params):
    return {"tools": [{"name": "get_weather", "description": "查询天气", "inputSchema": {"type": "object"}}]}


def handle_tools_call(params):
    name = params.get("name", "")
    args = params.get("arguments", {})
    if name == "get_weather":
        return {"content": [{"type": "text", "text": f"{args.get('city', '未知')} 天气晴朗"}]}
    return {"content": [{"type": "text", "text": f"Unknown: {name}"}]}


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("stdio 传输层演示")
    print("=" * 60)

    print("\nstdio 关键点：")
    print("""
1. 每行一个 JSON-RPC 消息
   - 请求：{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
   - 响应：{"jsonrpc":"2.0","id":1,"result":{...}}

2. stdin 读入，stdout 写出
   - read_request(): 从 stdin.readline() 读取一行
   - write_response(): json.dumps() 后 write() + flush()

3. 注意 flush()
   - Python 输出默认是缓冲的
   - 如果不 flush，输出可能不会立即写出
   - 使用 sys.stdout.flush() 确保立即写出

4. 父子进程通信
   - Agent 作为父进程，启动 MCP Server 作为子进程
   - 通过 pipe（stdin/stdout）通信
   - 适合本地、同一机器的场景
""")

    # 创建一个简单的 server 并用模拟请求测试
    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
    }

    print("\n模拟 stdio Server 处理：")

    # 模拟请求
    test_requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "北京"}}},
    ]

    for req in test_requests:
        print(f"\n→ {req}")
        method = req.get("method", "")
        params = req.get("params", {})
        req_id = req.get("id")

        handler = handlers.get(method)
        if handler:
            try:
                result = handler(params)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as exc:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}}
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown: {method}"}}

        print(f"← {resp}")


if __name__ == "__main__":
    if "--server" in sys.argv:
        # 实际运行 stdio Server
        handlers = {
            "initialize": handle_initialize,
            "tools/list": handle_tools_list,
            "tools/call": handle_tools_call,
        }
        server = create_stdio_server(handlers)
        server()
    else:
        demo()