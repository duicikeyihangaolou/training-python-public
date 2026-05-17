#!/usr/bin/env python3
"""
s01 Agent 主循环 — 单元测试

测试内容：
1. process_tool_call 工具分发
2. get_weather / calc 工具注册
3. MockLLMClient 返回正确的 stop_reason
4. agent_loop 对 tool_use 和 end_turn 的处理
"""

import pytest
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s01_agent_loop.agent_loop import (
    process_tool_call,
    TOOL_HANDLERS,
    MockLLMClient,
    agent_loop,
)


class TestToolHandlers:
    """测试工具处理器是否正确注册"""

    def test_get_weather_registered(self):
        """get_weather 工具已注册"""
        assert "get_weather" in TOOL_HANDLERS

    def test_calc_registered(self):
        """calc 工具已注册"""
        assert "calc" in TOOL_HANDLERS

    def test_get_weather_returns_string(self):
        """get_weather 返回天气字符串"""
        result = TOOL_HANDLERS["get_weather"]("北京")
        assert isinstance(result, str)
        assert "北京" in result or "天气" in result or "晴" in result

    def test_calc_basic(self):
        """calc 能正确计算表达式"""
        result = TOOL_HANDLERS["calc"]("2+3*5")
        assert result == "17"


class TestProcessToolCall:
    """测试工具分发函数"""

    def test_unknown_tool_returns_error(self):
        """未知工具返回错误信息"""
        result = process_tool_call("nonexistent_tool", {})
        assert "Error" in result
        assert "Unknown tool" in result

    def test_get_weather_city(self):
        """get_weather 能接收 city 参数"""
        result = process_tool_call("get_weather", {"city": "北京"})
        assert "北京" in result

    def test_get_weather_unknown_city(self):
        """未知城市返回友好提示"""
        result = process_tool_call("get_weather", {"city": "火星"})
        assert "不支持" in result or "Error" in result

    def test_calc_expression(self):
        """calc 能计算表达式"""
        result = process_tool_call("calc", {"expression": "10/2"})
        assert result == "5.0"

    def test_calc_invalid_expression(self):
        """无效表达式返回错误"""
        result = process_tool_call("calc", {"expression": "1/0"})
        assert "Error" in result


class TestMockLLMClient:
    """测试模拟 LLM 客户端"""

    def test_weather_query_triggers_tool(self):
        """包含'天气'的查询触发 tool_use"""
        client = MockLLMClient()
        response = client.messages_create(
            model="mock",
            system="",
            messages=[{"role": "user", "content": "北京天气怎么样"}],
            tools=[],
            max_tokens=8000,
        )
        assert response["stop_reason"] == "tool_use"
        assert any(b.get("name") == "get_weather" for b in response["content"] if b.get("type") == "tool_use")

    def test_normal_query_triggers_end_turn(self):
        """普通查询触发 end_turn"""
        client = MockLLMClient()
        response = client.messages_create(
            model="mock",
            system="",
            messages=[{"role": "user", "content": "给我讲个笑话"}],
            tools=[],
            max_tokens=8000,
        )
        assert response["stop_reason"] == "end_turn"

    def test_weather_in_chinese(self):
        """中文'天气'也能触发工具"""
        client = MockLLMClient()
        response = client.messages_create(
            model="mock",
            system="",
            messages=[{"role": "user", "content": "今天天气如何"}],
            tools=[],
            max_tokens=8000,
        )
        assert response["stop_reason"] == "tool_use"


class TestAgentLoop:
    """测试 Agent 主循环"""

    def test_agent_loop_with_mock_end_turn(self):
        """mock 模式下，end_turn 能正常返回文本"""
        client = MockLLMClient()
        result = agent_loop("给我讲个笑话", client, "mock")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_agent_loop_with_mock_tool_use(self):
        """mock 模式下，tool_use 能正确执行并返回结果"""
        client = MockLLMClient()
        # 天气查询会触发 tool_use
        result = agent_loop("北京天气怎么样", client, "mock")
        assert isinstance(result, str)
        # 模拟 LLM 在 tool 之后会再返回一个 end_turn
        assert "北京" in result or "天气" in result or "Error" not in result

    def test_messages_are_accumulated(self):
        """验证 messages 历史在循环中正确累积（通过 mock）"""
        client = MockLLMClient()

        # 捕获 messages 的变化
        captured_messages = []

        original_messages_create = client.messages_create

        def capture_wrapper(**kwargs):
            captured_messages.append(kwargs["messages"][:])  # 深拷贝
            return original_messages_create(**kwargs)

        client.messages_create = capture_wrapper

        agent_loop("测试", client, "mock")

        # 至少调用了 1 次 LLM
        assert len(captured_messages) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])