#!/usr/bin/env python3
"""
s04 框架对比 — 单元测试

测试各框架的导入和基本结构（不实际调用 API）
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestClaudeSDKImport:
    """测试 Claude SDK 导入"""

    def test_can_import_claude_sdk(self):
        """Claude SDK 可以导入"""
        try:
            from anthropic import Anthropic
            assert Anthropic is not None
        except ImportError:
            pytest.skip("anthropic SDK 未安装")


class TestOpenAIImport:
    """测试 OpenAI SDK 导入"""

    def test_can_import_openai(self):
        """OpenAI SDK 可以导入"""
        try:
            from openai import OpenAI
            assert OpenAI is not None
        except ImportError:
            pytest.skip("openai SDK 未安装")


class TestToolHandlers:
    """测试各框架的 tool handlers 格式"""

    def test_claude_tools_format(self):
        """Claude 工具格式正确"""
        from s04_framework_comparison.claude_sdk_demo import tools, TOOL_HANDLERS
        assert len(tools) >= 2
        assert "get_weather" in TOOL_HANDLERS

    def test_openai_tools_format(self):
        """OpenAI 工具格式正确（function calling）"""
        from s04_framework_comparison.openai_sdk_demo import tools, TOOL_HANDLERS
        assert len(tools) >= 2
        assert tools[0]["type"] == "function"
        assert "get_weather" in TOOL_HANDLERS


class TestLangGraphStructure:
    """测试 LangGraph 结构"""

    def test_langgraph_imports(self):
        """LangGraph 可以导入"""
        try:
            from langgraph.graph import StateGraph, END
            assert StateGraph is not None
            assert END is not None
        except ImportError:
            pytest.skip("langgraph 未安装")

    def test_agent_state_defined(self):
        """AgentState 已定义"""
        from s04_framework_comparison.langgraph_demo import AgentState
        assert "messages" in AgentState.__annotations__
        assert "next_action" in AgentState.__annotations__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])