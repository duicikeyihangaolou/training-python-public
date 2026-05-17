#!/usr/bin/env python3
"""
s06 为什么需要 MCP — 单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s06_why_mcp.local_vs_mcp import (
    get_weather_local,
    call_local_tool,
    mcp_request,
)


class TestLocalTool:
    """测试本地工具调用"""

    def test_get_weather_local(self):
        """get_weather_local 返回正确格式"""
        result = get_weather_local("北京")
        assert isinstance(result, str)
        assert "北京" in result or "不支持" in result

    def test_call_local_tool(self):
        """call_local_tool 正确分发"""
        handlers = {"get_weather": get_weather_local}
        result = call_local_tool("get_weather", {"city": "北京"}, handlers)
        assert "北京" in result

    def test_unknown_tool(self):
        """未知工具返回错误"""
        handlers = {}
        result = call_local_tool("nonexistent", {}, handlers)
        assert "Error" in result


class TestMCPRequest:
    """测试 MCP 请求/响应"""

    def test_tools_list_response(self):
        """tools/list 返回正确格式"""
        response = mcp_request("tools/list")
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "tools" in response["result"]

    def test_tools_call_response(self):
        """tools/call 返回正确格式"""
        response = mcp_request("tools/call", {
            "name": "get_weather",
            "arguments": {"city": "北京"}
        })
        assert response["jsonrpc"] == "2.0"
        assert "result" in response

    def test_unknown_method(self):
        """未知方法返回错误"""
        response = mcp_request("unknown_method")
        assert "error" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])