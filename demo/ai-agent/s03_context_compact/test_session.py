#!/usr/bin/env python3
"""
s03 会话持久化 — 单元测试
"""

import pytest
import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s03_context_compact.session_store import SessionStore, SessionRecord
from s03_context_compact.compact import (
    micro_compact,
    auto_compact,
    ContextGuard,
    estimate_tokens,
)


class TestSessionRecord:
    """测试会话记录序列化"""

    def test_to_json_and_back(self):
        """Record 可以序列化和反序列化"""
        record = SessionRecord(type="user", content="Hello")
        json_str = record.to_json()
        restored = SessionRecord.from_json(json_str)
        assert restored.type == "user"
        assert restored.content == "Hello"


class TestSessionStore:
    """测试会话存储"""

    def test_append_and_load(self, tmp_path):
        """追加记录后能正确加载"""
        store = SessionStore(session_dir=str(tmp_path))
        session_id = f"test_{int(time.time())}"

        # 模拟对话
        store.append_user(session_id, "Hello")
        store.append_assistant(session_id, '[{"type": "text", "text": "Hi!"}]')

        # 加载
        messages = store.load_session(session_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_tool_use_and_result(self, tmp_path):
        """tool_use 和 tool_result 正确合并到消息"""
        store = SessionStore(session_dir=str(tmp_path))
        session_id = f"test_{int(time.time())}"

        store.append_user(session_id, "天气？")
        store.append_assistant(session_id, '[{"type": "tool_use", "id": "tu1", "name": "get_weather", "input": {"city": "北京"}}]')
        store.append_tool_result(session_id, "tu1", "晴天")
        store.append_assistant(session_id, '[{"type": "text", "text": "晴天"}]')

        messages = store.load_session(session_id)

        # 应该合并为 3 条消息：user / assistant(tool_use) / user(tool_result) / assistant(text)
        # 实际：user, assistant, user, assistant = 4 条
        assert len(messages) == 4

    def test_list_sessions(self, tmp_path):
        """list_sessions 返回所有会话"""
        store = SessionStore(session_dir=str(tmp_path))
        store.append_user("session_a", "hello")
        store.append_user("session_b", "world")

        sessions = store.list_sessions()
        assert "session_a" in sessions
        assert "session_b" in sessions


class TestMicroCompact:
    """测试 micro_compact"""

    def test_old_tool_results_replaced(self):
        """超过 keep_recent 轮的 tool_result 被替换"""
        messages = [
            {"role": "user", "content": [{"type": "tool_result", "content": "old1"}]},
            {"role": "user", "content": [{"type": "tool_result", "content": "old2"}]},
            {"role": "user", "content": [{"type": "tool_result", "content": "old3"}]},
            {"role": "user", "content": [{"type": "tool_result", "content": "recent"}]},
        ]

        micro_compact(messages, keep_recent=2)

        # 最近 2 个应该保留，第 1 个应该被替换
        assert "[Previous:" in messages[0]["content"][0]["content"]
        assert "recent" in messages[-1]["content"][0]["content"]


class TestContextGuard:
    """测试 3 阶段溢出保护"""

    def test_normal_call_succeeds(self):
        """正常调用直接返回"""
        def api_call():
            return {"result": "ok"}

        guard = ContextGuard(api_call)
        result = guard.call()
        assert result["result"] == "ok"

    def test_overflow_truncated(self):
        """第一次溢出时截断 tool_result"""
        call_count = [0]

        def api_call(messages):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Token limit exceeded")
            return {"result": "ok after truncate"}

        guard = ContextGuard(api_call)
        messages = [{"role": "user", "content": [{"type": "tool_result", "content": "x" * 5000}]}]

        result = guard.call(messages=messages)
        assert result["result"] == "ok after truncate"

    def test_estimate_tokens(self):
        """token 估算"""
        assert estimate_tokens("hello") == 1  # 5/4 = 1
        assert estimate_tokens("你好") == 1   # 2/4 = 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])