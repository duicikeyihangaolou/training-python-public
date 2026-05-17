#!/usr/bin/env python3
"""
s07 MCP 协议 — 单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s07_mcp_protocol.protocol_demo import (
    JSONRPCRequest,
    JSONRPCResponse,
    create_initialize_request,
    create_tools_list_request,
    create_tools_call_request,
    get_weather_schema,
)


class TestJSONRPCRequest:
    """测试 JSON-RPC 请求"""

    def test_create_request(self):
        """创建请求"""
        req = JSONRPCRequest(method="tools/list", params={}, id=1)
        data = req.to_dict()
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "tools/list"
        assert data["id"] == 1

    def test_serialize_to_json(self):
        """序列化为 JSON"""
        req = JSONRPCRequest(method="test", params={"key": "value"}, id=1)
        json_str = req.to_json()
        assert '"jsonrpc": "2.0"' in json_str
        assert '"method": "test"' in json_str

    def test_parse_from_dict(self):
        """从 dict 解析"""
        data = {"jsonrpc": "2.0", "method": "test", "params": {}, "id": 42}
        req = JSONRPCRequest.from_dict(data)
        assert req.method == "test"
        assert req.id == 42


class TestJSONRPCResponse:
    """测试 JSON-RPC 响应"""

    def test_success_response(self):
        """成功响应"""
        resp = JSONRPCResponse(id=1, result={"tools": []})
        data = resp.to_dict()
        assert "result" in data
        assert data["result"] == {"tools": []}

    def test_error_response(self):
        """错误响应"""
        resp = JSONRPCResponse(id=1, error={"code": -32602, "message": "Invalid params"})
        data = resp.to_dict()
        assert "error" in data
        assert data["error"]["code"] == -32602

    def test_is_success(self):
        """判断是否成功"""
        assert JSONRPCResponse(id=1, result={}).is_success()
        assert not JSONRPCResponse(id=1, error={}).is_success()


class TestMCPMethods:
    """测试 MCP 方法创建"""

    def test_initialize_request(self):
        """initialize 请求格式正确"""
        req = create_initialize_request()
        assert req["method"] == "initialize"
        assert "clientInfo" in req["params"]

    def test_tools_list_request(self):
        """tools/list 请求格式正确"""
        req = create_tools_list_request()
        assert req["method"] == "tools/list"

    def test_tools_call_request(self):
        """tools/call 请求格式正确"""
        req = create_tools_call_request("get_weather", {"city": "北京"})
        assert req["method"] == "tools/call"
        assert req["params"]["name"] == "get_weather"
        assert req["params"]["arguments"]["city"] == "北京"


class TestToolSchema:
    """测试工具 Schema"""

    def test_weather_schema_has_required_fields(self):
        """weather schema 包含必需字段"""
        schema = get_weather_schema()
        assert "name" in schema
        assert "description" in schema
        assert "inputSchema" in schema

    def test_weather_schema_city_required(self):
        """city 参数是必需的"""
        schema = get_weather_schema()
        required = schema["inputSchema"].get("required", [])
        assert "city" in required


if __name__ == "__main__":
    pytest.main([__file__, "-v"])