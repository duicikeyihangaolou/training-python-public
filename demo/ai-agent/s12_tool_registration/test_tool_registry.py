#!/usr/bin/env python3
"""
s12 工具注册与执行 — 单元测试
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s12_tool_registration.tool_registry import (
    ToolRegistry,
    create_tool_registry,
)


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_and_list(self):
        """注册后能列出工具"""
        registry = ToolRegistry()
        registry.register("test_tool", "测试工具", {"type": "object"}, lambda: "ok")
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_call_existing_tool(self):
        """调用已注册工具成功"""
        registry = create_tool_registry()
        result = registry.call_tool("get_weather", {"city": "北京"})
        assert "北京" in result

    def test_call_unknown_tool(self):
        """调用未知工具抛出异常"""
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Unknown tool"):
            registry.call_tool("nonexistent", {})

    def test_call_with_invalid_args(self):
        """调用时参数错误"""
        registry = create_tool_registry()
        with pytest.raises(ValueError, match="Invalid arguments"):
            registry.call_tool("get_weather", {})  # 缺少必需的 city


class TestCalcTool:
    """测试 calc 工具"""

    def test_calc_basic(self):
        """基本计算"""
        registry = create_tool_registry()
        result = registry.call_tool("calc", {"expression": "2+2"})
        assert result == "4"

    def test_calc_expression(self):
        """复杂表达式"""
        registry = create_tool_registry()
        result = registry.call_tool("calc", {"expression": "2**10"})
        assert result == "1024"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])