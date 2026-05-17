#!/usr/bin/env python3
"""
s02: 工具描述与分发

本节演示工具注册的核心思想：
  Schema（告诉模型） + Handler（告诉代码） = 工具注册

核心原则：
- 加工具 = 加 Schema + 加 Handler，循环本身不变
- 分发函数一次字典查找，无 if/elif 链
- 安全沙箱防止目录穿越

运行方式：
    python tool_dispatch.py
"""

import os
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# 工具 Schema：告诉 LLM 有哪些工具、参数是什么
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "name": "read_file",
        "description": "读取文件内容（支持限制行数）",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径，相对于工作目录"
                },
                "limit": {
                    "type": "integer",
                    "description": "最多返回多少行，默认 None（返回全部）"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "创建或覆盖文件内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径，相对于工作目录"
                },
                "content": {
                    "type": "string",
                    "description": "文件内容"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "bash",
        "description": "执行 shell 命令（仅用于演示，生产环境禁用）",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell 命令"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时秒数，默认 30"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "calc",
        "description": "计算数学表达式",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如：2+3*5"
                }
            },
            "required": ["expression"]
        }
    }
]

# --------------------------------------------------------------------------- #
# 安全沙箱：防止目录穿越攻击
# --------------------------------------------------------------------------- #

# 工作目录，所有文件操作限制在此目录内
WORKDIR = Path("/tmp/ai_agent_workdir")

def setup_workdir():
    """初始化工作目录"""
    global WORKDIR
    WORKDIR.mkdir(parents=True, exist_ok=True)

def safe_path(path: str) -> Path:
    """
    将相对路径转换为安全的工作目录内绝对路径。
    如果路径逃逸到工作目录之外，抛出 ValueError。

    这是防止目录穿越攻击的关键：
    用户可能传入 ../../etc/passwd 或 /etc/passwd，
    我们需要确保最终路径在 WORKDIR 之内。
    """
    # 拼接工作目录
    abs_path = (WORKDIR / path).resolve()

    # 检查是否在工作目录内
    if not abs_path.is_relative_to(WORKDIR):
        raise ValueError(f"路径逃逸: {path} -> {abs_path} 超出工作目录 {WORKDIR}")

    return abs_path

# --------------------------------------------------------------------------- #
# 工具 Handler：具体实现每个工具的逻辑
# --------------------------------------------------------------------------- #

def tool_read_file(path: str, limit: int = None) -> str:
    """
    读取文件内容

    Args:
        path: 文件路径
        limit: 最多返回多少行

    Returns:
        文件内容字符串，超长部分会被截断
    """
    abs_path = safe_path(path)

    if not abs_path.exists():
        return f"Error: 文件不存在 {path}"

    try:
        text = abs_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit]
            return "\n".join(lines) + f"\n... (共 {len(lines)} 行，已限制显示)"
        return "\n".join(lines)
    except Exception as exc:
        return f"Error: 读取失败 {exc}"


def tool_write_file(path: str, content: str) -> str:
    """
    创建或覆盖文件

    Args:
        path: 文件路径
        content: 文件内容

    Returns:
        成功/失败消息
    """
    abs_path = safe_path(path)

    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        return f"成功写入文件 {path}，共 {len(content)} 字符"
    except Exception as exc:
        return f"Error: 写入失败 {exc}"


def tool_bash(command: str, timeout: int = 30) -> str:
    """
    执行 shell 命令（演示用，生产环境禁用！）

    Args:
        command: Shell 命令
        timeout: 超时秒数

    Returns:
        命令输出或错误信息
    """
    import subprocess

    try:
        # 注意：eval 在生产环境中禁用！这里仅用于演示
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKDIR),
        )
        if result.returncode == 0:
            output = result.stdout.strip() or "(命令执行成功，无输出)"
            return output
        else:
            return f"Error: 命令执行失败 (exit {result.returncode})\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Error: 命令超时（{timeout}秒）"
    except Exception as exc:
        return f"Error: {exc}"


def tool_calc(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 数学表达式

    Returns:
        计算结果或错误
    """
    try:
        # 注意：eval 在生产环境中禁用！这里仅用于演示
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


# --------------------------------------------------------------------------- #
# 工具注册表：Schema（TOOLS）和 Handler（TOOL_HANDLERS）成对出现
# --------------------------------------------------------------------------- #

# TOOL_HANDLERS 字典：工具名 → 处理函数
TOOL_HANDLERS = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "bash": tool_bash,
    "calc": tool_calc,
}


# --------------------------------------------------------------------------- #
# 分发函数
# --------------------------------------------------------------------------- #

def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    分发工具调用 — 整个系统的核心调度员

    工作原理：
    1. 根据 tool_name 在 TOOL_HANDLERS 中查找对应的处理函数
    2. 用 **tool_input 解包参数，调用处理函数
    3. 捕获异常，返回错误信息（而不是抛出）

    核心优势：O(1) 查找，不使用 if/elif 链，扩展时只需添加注册表条目

    Args:
        tool_name: 工具名称（如 "read_file"）
        tool_input: 参数字典（如 {"path": "a.txt", "limit": 10}）

    Returns:
        工具执行结果的字符串
    """
    handler = TOOL_HANDLERS.get(tool_name)

    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        return handler(**tool_input)
    except TypeError as exc:
        # 参数缺失或类型错误（handler 签名与传入参数不匹配）
        return f"Error: Invalid arguments for {tool_name}: {exc}"
    except ValueError as exc:
        # 安全沙箱违规（如目录穿越）
        return f"Error: {exc}"
    except Exception as exc:
        # 其他执行错误
        return f"Error: {tool_name} failed: {exc}"


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示工具分发流程"""
    setup_workdir()

    print("=" * 60)
    print("工具分发演示")
    print("=" * 60)

    # 测试用例
    test_cases = [
        # (tool_name, tool_input, 说明)
        ("read_file", {"path": "hello.txt"}, "读取不存在的文件"),
        ("write_file", {"path": "hello.txt", "content": "Hello, AI Agent!\n第二行"}, "创建文件"),
        ("read_file", {"path": "hello.txt"}, "读取刚创建的文件"),
        ("read_file", {"path": "hello.txt", "limit": 1}, "限制行数读取"),
        ("calc", {"expression": "2**10"}, "计算 2 的 10 次方"),
        ("bash", {"command": "echo 'Hello from bash'"}, "执行 shell 命令"),
        ("nonexistent_tool", {}, "调用不存在的工具"),
    ]

    for tool_name, tool_input, description in test_cases:
        print(f"\n[测试] {description}")
        print(f"  调用: {tool_name}({tool_input})")
        result = process_tool_call(tool_name, tool_input)
        print(f"  结果: {result[:100]}{'...' if len(result) > 100 else ''}")

    # 演示目录穿越攻击被拦截
    print("\n[测试] 目录穿越攻击拦截")
    print("  调用: read_file(path='../../etc/passwd')")
    result = process_tool_call("read_file", {"path": "../../etc/passwd"})
    print(f"  结果: {result}")


if __name__ == "__main__":
    demo()