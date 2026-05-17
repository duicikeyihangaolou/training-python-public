#!/usr/bin/env python3
"""
s14: 传输层实现 — SSE 模式

本节演示 SSE（Server-Sent Events）传输的实现：
- HTTP 长连接
- Server 按 `data: {...}\n\n` 推送事件
- 适合 Web/远程场景

运行方式：
    python sse_server.py  # 启动 Server
    # 然后用 curl 测试：
    # curl http://localhost:8765/mcp -X POST -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

注意：这个 demo 会启动 HTTP Server，请注意端口占用
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable
import threading


# --------------------------------------------------------------------------- #
# SSE 事件格式
# --------------------------------------------------------------------------- #

def sse_event(data: dict) -> bytes:
    """
    将 JSON 包装为 SSE 事件格式

    SSE 格式：
    - 每个事件以 "data: " 开头
    - 多行数据用 "\ndata: " 开头
    - 事件以两个换行符结束 "\n\n"
    """
    json_str = json.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n".encode("utf-8")


# --------------------------------------------------------------------------- #
# SSE Handler
# --------------------------------------------------------------------------- #

class SSEHandler(BaseHTTPRequestHandler):
    """SSE HTTP 请求处理"""

    protocol_version = "HTTP/1.1"

    def do_GET(self):
        """处理 GET 请求（可用于健康检查）"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        """处理 POST 请求（JSON-RPC）"""
        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # 处理请求
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        # 分发（使用共享的 handlers）
        handler = self.server.handlers.get(method)
        if handler:
            try:
                result = handler(params)
                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as exc:
                response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}}
        else:
            response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown: {method}"}}

        # 发送 SSE 响应
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        self.wfile.write(sse_event(response))
        self.wfile.flush()

    def log_message(self, format, *args):
        """抑制日志输出"""
        pass


class SSEServer(HTTPServer):
    """SSE HTTP Server"""

    def __init__(self, port: int, handlers: dict):
        super().__init__(("localhost", port), SSEHandler)
        self.handlers = handlers
        print(f"[Server] SSE Server 启动在 http://localhost:{port}/mcp")


# --------------------------------------------------------------------------- #
# 演示用 handlers
# --------------------------------------------------------------------------- #

def handle_initialize(params):
    return {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "sse-demo", "version": "1.0"}}


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
    print("SSE 传输层演示")
    print("=" * 60)

    print("\nSSE 关键点：")
    print("""
1. HTTP 长连接
   - Client 发起 POST 请求
   - Server 保持连接，推送事件
   - 适合 Web 前端、远程 Server

2. SSE 格式
   - 每个事件：data: {json}\n\n
   - 事件流：data: {...}\ndata: {...}\n\n

3. 与 stdio 的区别
   | 方面     | stdio           | SSE                |
   |----------|-----------------|-------------------|
   | 传输     | 管道（pipe）    | HTTP              |
   | 场景     | 本地父子进程    | Web/远程          |
   | 复杂度   | 简单            | 需要 HTTP Server  |
   | 调试     | 直接看 stdin/out | 需要 curl/wireshark |

4. 协议与传输解耦
   - 路由 + 执行逻辑完全相同
   - 区别只在 IO 层：stdio vs HTTP
""")

    print("\nSSE 事件格式示例：")
    example = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}
    print(f"data: {json.dumps(example)}\n\n")

    print("\n启动 SSE Server（测试用）...")
    print("提示：实际运行需要 Ctrl+C 停止\n")

    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
    }

    try:
        server = SSEServer(8765, handlers)
        print("Server 运行中，可以用以下命令测试：")
        print('  curl http://localhost:8765/mcp -X POST -d \'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\'')
        print("\n按 Ctrl+C 停止\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer 停止")
    except Exception as e:
        print(f"\nServer 错误: {e}")
        print("（这可能是端口已被占用）")


if __name__ == "__main__":
    demo()