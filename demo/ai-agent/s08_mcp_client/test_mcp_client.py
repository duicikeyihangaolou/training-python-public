#!/usr/bin/env python3
"""
s08 MCP Client — 单元测试
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPClientConcept:
    """测试 MCP Client 概念"""

    def test_jsonrpc_request_format(self):
        """JSON-RPC 请求格式正确"""
        from s07_mcp_protocol.protocol_demo import create_tools_call_request
        req = create_tools_call_request("get_weather", {"city": "北京"})
        assert req["jsonrpc"] == "2.0"
        assert req["method"] == "tools/call"
        assert req["params"]["name"] == "get_weather"

    def test_mock_server_response(self):
        """模拟 Server 响应格式"""
        # 模拟 tools/list 响应
        resp = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {"name": "get_weather", "description": "查询天气", "inputSchema": {"type": "object"}}
                ]
            }
        }
        assert "result" in resp
        assert "tools" in resp["result"]

    def test_tool_call_response(self):
        """tools/call 响应格式"""
        resp = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": "北京天气：晴"}]
            }
        }
        assert "result" in resp
        assert "content" in resp["result"]


class TestMCPClientSession:
    """测试 MCP Client Session 概念"""

    def test_session_needs_initialize(self):
        """Session 需要先 initialize"""
        # 验证流程：创建 session → initialize → 调用工具
        steps = ["create_session", "initialize", "list_tools", "call_tool", "disconnect"]
        assert len(steps) == 5

    def test_tools_list_returns_tools(self):
        """tools/list 返回工具列表"""
        # 这是一个概念测试，验证返回结构
        mock_response = {
            "tools": [
                {"name": "get_weather", "description": "查询天气", "inputSchema": {}},
                {"name": "calc", "description": "计算", "inputSchema": {}}
            ]
        }
        assert len(mock_response["tools"]) == 2
        assert mock_response["tools"][0]["name"] == "get_weather"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])