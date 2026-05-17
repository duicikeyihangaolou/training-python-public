#!/usr/bin/env python3
"""
s10 MCP Server 生命周期 — 单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s10_mcp_server_lifecycle.server_lifecycle import (
    ServerState,
    Router,
    handle_initialize,
    handle_tools_list,
    handle_tools_call,
)


class TestServerState:
    """测试 Server 状态"""

    def test_start_sets_running(self):
        """启动后 running=True"""
        state = ServerState()
        assert not state.running
        state.start()
        assert state.running

    def test_stop_sets_running_false(self):
        """关闭后 running=False"""
        state = ServerState()
        state.start()
        state.stop()
        assert not state.running

    def test_request_count_increments(self):
        """请求计数增加"""
        state = ServerState()
        state.start()
        state.request_count += 1
        assert state.request_count == 1


class TestRouter:
    """测试请求路由器"""

    def test_register_and_dispatch(self):
        """注册后能正确分发"""
        router = Router()
        router.register("test_method", lambda p: {"result": "ok"})

        resp = router.dispatch("test_method", {}, ServerState())
        assert "result" in resp

    def test_unknown_method_returns_error(self):
        """未知 method 返回错误"""
        router = Router()
        resp = router.dispatch("unknown_method", {}, ServerState())
        assert "error" in resp
        assert resp["error"]["code"] == -32601


class TestHandlers:
    """测试处理函数"""

    def test_initialize_returns_capabilities(self):
        """initialize 返回正确的 capabilities"""
        result = handle_initialize({"clientInfo": {"name": "test"}})
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result

    def test_tools_list_returns_tools(self):
        """tools/list 返回工具列表"""
        result = handle_tools_list({})
        assert "tools" in result
        assert len(result["tools"]) >= 1

    def test_tools_call_get_weather(self):
        """tools/call 能执行 get_weather"""
        result = handle_tools_call({
            "name": "get_weather",
            "arguments": {"city": "北京"}
        })
        assert "content" in result

    def test_tools_call_unknown_tool(self):
        """调用未知工具抛出异常"""
        with pytest.raises(ValueError):
            handle_tools_call({"name": "unknown_tool", "arguments": {}})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])