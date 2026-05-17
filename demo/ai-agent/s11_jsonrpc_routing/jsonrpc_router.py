#!/usr/bin/env python3
"""
s11: JSON-RPC 路由与分发

本节演示完整的 JSON-RPC 2.0 请求解析、路由和响应构造。

运行方式：
    python jsonrpc_router.py
"""

import json
from typing import Callable, Any, Optional


# --------------------------------------------------------------------------- #
# 异常定义
# --------------------------------------------------------------------------- #

class JSONRPCError(Exception):
    """JSON-RPC 错误基类"""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_dict(self) -> dict:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


class ParseError(JSONRPCError):
    """解析错误（-32700）"""

    def __init__(self, message: str):
        super().__init__(-32700, f"Parse error: {message}")


class InvalidRequest(JSONRPCError):
    """无效请求（-32600）"""

    def __init__(self, message: str):
        super().__init__(-32600, f"Invalid Request: {message}")


class MethodNotFound(JSONRPCError):
    """方法未找到（-32601）"""

    def __init__(self, method: str):
        super().__init__(-32601, f"Method not found: {method}")


class InvalidParams(JSONRPCError):
    """参数无效（-32602）"""

    def __init__(self, message: str):
        super().__init__(-32602, f"Invalid params: {message}")


class InternalError(JSONRPCError):
    """内部错误（-32603）"""

    def __init__(self, message: str):
        super().__init__(-32603, f"Internal error: {message}")


# --------------------------------------------------------------------------- #
# 请求解析
# --------------------------------------------------------------------------- #

def parse_request(data: dict) -> tuple[str, dict, Any]:
    """
    解析 JSON-RPC 请求

    Args:
        data: 请求字典（已从 JSON 解析）

    Returns:
        (method, params, request_id) 元组

    Raises:
        ParseError / InvalidRequest / InvalidParams
    """
    # 校验 jsonrpc 版本
    if data.get("jsonrpc") != "2.0":
        raise InvalidRequest(f"Expected jsonrpc '2.0', got '{data.get('jsonrpc')}'")

    # 提取 method
    method = data.get("method")
    if not method or not isinstance(method, str):
        raise InvalidRequest("Missing or invalid 'method'")

    # 提取 params（可选，默认空对象）
    params = data.get("params", {})

    # 提取 id（可选，用于响应匹配）
    req_id = data.get("id")

    return method, params, req_id


# --------------------------------------------------------------------------- #
# 响应构造
# --------------------------------------------------------------------------- #

def success_response(req_id: Any, result: dict) -> dict:
    """构造成功响应"""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result
    }


def error_response(req_id: Any, error: JSONRPCError) -> dict:
    """构造错误响应"""
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": error.to_dict()
    }


# --------------------------------------------------------------------------- #
# 路由
# --------------------------------------------------------------------------- #

class JSONRPCRouter:
    """
    JSON-RPC 路由器

    管理 method → handler 的映射，支持注册/分发/错误处理
    """

    def __init__(self):
        self.handlers = {}

    def register(self, method: str, handler: Callable[[dict], dict]):
        """注册处理函数"""
        self.handlers[method] = handler

    def dispatch(self, request: dict) -> dict:
        """
        分发 JSON-RPC 请求

        Args:
            request: JSON-RPC 请求字典

        Returns:
            JSON-RPC 响应字典
        """
        try:
            # 解析请求
            method, params, req_id = parse_request(request)

            # 查找 handler
            handler = self.handlers.get(method)
            if not handler:
                raise MethodNotFound(method)

            # 调用 handler
            result = handler(params)
            return success_response(req_id, result)

        except JSONRPCError as exc:
            return error_response(request.get("id"), exc)
        except Exception as exc:
            # 未预期的错误，返回 Internal error
            return error_response(request.get("id"), InternalError(str(exc)))


# --------------------------------------------------------------------------- #
# 处理函数示例
# --------------------------------------------------------------------------- #

def demo_handlers():
    """创建演示用处理函数"""
    handlers = {}

    def handle_echo(params):
        """echo: 原样返回参数"""
        return {"echo": params}

    def handle_add(params):
        """add: 加法"""
        a = params.get("a", 0)
        b = params.get("b", 0)
        return {"result": a + b}

    def handle_get_info(params):
        """get_info: 返回服务器信息"""
        return {
            "name": "demo-server",
            "version": "1.0.0",
            "methods": list(handlers.keys())
        }

    handlers["echo"] = handle_echo
    handlers["add"] = handle_add
    handlers["getInfo"] = handle_get_info

    return handlers


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("JSON-RPC 路由与分发演示")
    print("=" * 60)

    router = JSONRPCRouter()
    handlers = demo_handlers()
    for name, handler in handlers.items():
        router.register(name, handler)

    print("\n注册的 handler：", list(handlers.keys()))

    # 测试请求
    test_requests = [
        {"jsonrpc": "2.0", "method": "echo", "params": {"msg": "Hello"}, "id": 1},
        {"jsonrpc": "2.0", "method": "add", "params": {"a": 10, "b": 25}, "id": 2},
        {"jsonrpc": "2.0", "method": "getInfo", "params": {}, "id": 3},
        {"jsonrpc": "2.0", "method": "unknown_method", "params": {}, "id": 4},
        {"jsonrpc": "2.0", "method": "add", "params": "not_an_object", "id": 5},  # 无效 params
        {"jsonrpc": "1.9", "method": "test", "params": {}, "id": 6},  # 无效版本
    ]

    for req in test_requests:
        print(f"\n请求：{json.dumps(req)}")
        resp = router.dispatch(req)
        print(f"响应：{json.dumps(resp, indent=2)}")


if __name__ == "__main__":
    demo()