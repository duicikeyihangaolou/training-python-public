#!/usr/bin/env python3
"""
s11 JSON-RPC 路由 — 单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s11_jsonrpc_routing.jsonrpc_router import (
    JSONRPCRouter,
    parse_request,
    success_response,
    InvalidRequest,
    MethodNotFound,
)


class TestParseRequest:
    """测试请求解析"""

    def test_valid_request(self):
        """有效请求正确解析"""
        req = {"jsonrpc": "2.0", "method": "test", "params": {}, "id": 1}
        method, params, req_id = parse_request(req)
        assert method == "test"
        assert params == {}
        assert req_id == 1

    def test_invalid_jsonrpc_version(self):
        """无效 jsonrpc 版本"""
        req = {"jsonrpc": "1.9", "method": "test", "params": {}, "id": 1}
        with pytest.raises(InvalidRequest):
            parse_request(req)

    def test_missing_method(self):
        """缺少 method"""
        req = {"jsonrpc": "2.0", "params": {}, "id": 1}
        with pytest.raises(InvalidRequest):
            parse_request(req)


class TestRouter:
    """测试路由器"""

    def test_register_and_dispatch(self):
        """注册后能正确分发"""
        router = JSONRPCRouter()
        router.register("test", lambda p: {"ok": True})
        resp = router.dispatch({"jsonrpc": "2.0", "method": "test", "params": {}, "id": 1})
        assert "result" in resp
        assert resp["result"]["ok"] is True

    def test_method_not_found(self):
        """未知方法返回错误"""
        router = JSONRPCRouter()
        resp = router.dispatch({"jsonrpc": "2.0", "method": "unknown", "params": {}, "id": 1})
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_success_response_format(self):
        """成功响应格式正确"""
        resp = success_response(42, {"data": "value"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 42
        assert "result" in resp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])