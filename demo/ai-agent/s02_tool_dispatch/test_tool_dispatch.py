#!/usr/bin/env python3
"""
s02 工具描述与分发 — 单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from s02_tool_dispatch.tool_dispatch import (
    TOOLS,
    TOOL_HANDLERS,
    safe_path,
    process_tool_call,
    WORKDIR,
)


class TestToolsSchema:
    """测试 TOOLS Schema 是否正确定义"""

    def test_tools_is_list(self):
        assert isinstance(TOOLS, list)

    def test_each_tool_has_required_fields(self):
        """每个工具都有 name, description, input_schema"""
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_read_file_schema(self):
        """read_file 的 Schema 正确"""
        read_file = next(t for t in TOOLS if t["name"] == "read_file")
        props = read_file["input_schema"]["properties"]
        assert "path" in props
        assert "limit" in props

    def test_write_file_schema(self):
        """write_file 的 Schema 正确"""
        write_file = next(t for t in TOOLS if t["name"] == "write_file")
        props = write_file["input_schema"]["properties"]
        assert "path" in props
        assert "content" in props
        required = write_file["input_schema"]["required"]
        assert "path" in required
        assert "content" in required


class TestToolHandlers:
    """测试工具处理器注册"""

    def test_all_tools_have_handler(self):
        """每个 Schema 中的工具都有对应的 Handler"""
        for tool in TOOLS:
            assert tool["name"] in TOOL_HANDLERS, f"Missing handler for {tool['name']}"

    def test_handler_is_callable(self):
        """每个 Handler 都是可调用对象"""
        for name, handler in TOOL_HANDLERS.items():
            assert callable(handler), f"{name} handler is not callable"


class TestSafePath:
    """测试路径安全校验"""

    def test_relative_path_within_workdir(self):
        """相对路径解析到工作目录内，是安全的"""
        result = safe_path("subdir/file.txt")
        assert result.is_relative_to(WORKDIR)

    def test_path_with_dotdot_blocked(self):
        """../ 试图逃逸时被拦截"""
        with pytest.raises(ValueError, match="路径逃逸"):
            safe_path("../../etc/passwd")

    def test_absolute_path_blocked(self):
        """/etc/passwd 这种绝对路径被拦截"""
        with pytest.raises(ValueError, match="路径逃逸"):
            safe_path("/etc/passwd")


class TestProcessToolCall:
    """测试工具分发函数"""

    def test_unknown_tool(self):
        """未知工具返回错误"""
        result = process_tool_call("nonexistent", {})
        assert "Error" in result
        assert "Unknown tool" in result

    def test_read_file_missing_arg(self):
        """缺少必需参数时返回错误"""
        result = process_tool_call("read_file", {})
        assert "Error" in result

    def test_calc_basic(self):
        """calc 正常工作"""
        result = process_tool_call("calc", {"expression": "2+2"})
        assert result == "4"


class TestWriteAndRead:
    """测试写文件后读文件的完整流程"""

    def test_write_then_read(self, tmp_path):
        """写入文件后再读取，内容一致"""
        # 创建临时工作目录
        import s02_tool_dispatch.tool_dispatch as td
        original_workdir = td.WORKDIR
        td.WORKDIR = tmp_path

        try:
            # 写文件
            write_result = process_tool_call("write_file", {
                "path": "test.txt",
                "content": "Hello\nWorld\n123"
            })
            assert "成功" in write_result

            # 读文件
            read_result = process_tool_call("read_file", {"path": "test.txt"})
            assert "Hello" in read_result
            assert "World" in read_result
        finally:
            td.WORKDIR = original_workdir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])