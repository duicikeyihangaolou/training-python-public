#!/usr/bin/env python3
"""
s12: 工具注册与执行

本节演示 MCP Server 中的工具注册与执行：
- tools/list: 返回所有已注册工具的元数据
- tools/call: 根据 name + arguments 执行工具

运行方式：
    python tool_registry.py
"""

import json
from typing import Callable, Any, Optional


# --------------------------------------------------------------------------- #
# 工具元数据
# --------------------------------------------------------------------------- #

@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    input_schema: dict
    handler: Callable

    def to_metadata(self) -> dict:
        """转为 JSON-RPC 可传输的元数据（不含 handler）"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# 工具注册表
# --------------------------------------------------------------------------- #

class ToolRegistry:
    """
    工具注册表

    管理工具的元数据和执行函数
    """

    def __init__(self):
        self.tools = {}  # name -> Tool

    def register(self, name: str, description: str, input_schema: dict, handler: Callable):
        """注册工具"""
        tool = Tool(name=name, description=description, input_schema=input_schema, handler=handler)
        self.tools[name] = tool
        print(f"[Registry] 注册工具: {name}")

    def list_tools(self) -> list:
        """返回所有工具的元数据（用于 tools/list）"""
        return [tool.to_metadata() for tool in self.tools.values()]

    def call_tool(self, name: str, arguments: dict) -> Any:
        """
        调用工具

        Args:
            name: 工具名称
            arguments: 参数字典

        Returns:
            工具执行结果

        Raises:
            ValueError: 工具不存在或参数错误
        """
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        try:
            return tool.handler(**arguments)
        except TypeError as exc:
            raise ValueError(f"Invalid arguments for {name}: {exc}")
        except Exception as exc:
            raise ValueError(f"{name} failed: {exc}")


# --------------------------------------------------------------------------- #
# 工具实现
# --------------------------------------------------------------------------- #

def get_weather(city: str) -> str:
    """获取城市天气"""
    db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C", "东京": "小雨 12-20°C"}
    return db.get(city, f"不支持查询 {city} 的天气")


def calc(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        raise ValueError(f"计算错误: {e}")


def read_file(path: str, limit: Optional[int] = None) -> str:
    """读取文件内容"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if limit:
                lines = content.splitlines()[:limit]
                return "\n".join(lines) + f"\n...(共 {len(content.splitlines())} 行)"
            return content
    except FileNotFoundError:
        raise ValueError(f"文件不存在: {path}")
    except Exception as e:
        raise ValueError(f"读取失败: {e}")


# --------------------------------------------------------------------------- #
# MCP Server 处理函数
# --------------------------------------------------------------------------- #

def create_tool_registry() -> ToolRegistry:
    """创建并注册工具的注册表"""
    registry = ToolRegistry()

    registry.register(
        name="get_weather",
        description="查询指定城市的天气",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        },
        handler=get_weather
    )

    registry.register(
        name="calc",
        description="计算数学表达式的值",
        input_schema={
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        },
        handler=calc
    )

    registry.register(
        name="read_file",
        description="读取文件内容（可选限制行数）",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "limit": {"type": "integer", "description": "最多返回行数（可选）"}
            },
            "required": ["path"]
        },
        handler=read_file
    )

    return registry


# --------------------------------------------------------------------------- #
# MCP 方法处理函数
# --------------------------------------------------------------------------- #

def handle_tools_list(params: dict, registry: ToolRegistry) -> dict:
    """处理 tools/list 请求"""
    tools = registry.list_tools()
    return {"tools": tools}


def handle_tools_call(params: dict, registry: ToolRegistry) -> dict:
    """处理 tools/call 请求"""
    name = params.get("name", "")
    arguments = params.get("arguments", {})

    print(f"[Handler] tools/call: {name}({arguments})")

    try:
        result = registry.call_tool(name, arguments)
        return {"content": [{"type": "text", "text": str(result)}]}
    except ValueError as exc:
        # 参数错误或工具不存在
        raise exc


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("工具注册与执行演示")
    print("=" * 60)

    # 创建注册表并注册工具
    registry = create_tool_registry()

    print(f"\n已注册 {len(registry.tools)} 个工具")

    # 演示 tools/list
    print("\n1. tools/list")
    print("-" * 40)
    tools = registry.list_tools()
    print(f"返回 {len(tools)} 个工具：")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")

    # 演示 tools/call
    print("\n2. tools/call")
    print("-" * 40)

    test_calls = [
        ("get_weather", {"city": "北京"}),
        ("calc", {"expression": "2**10"}),
        ("read_file", {"path": "/etc/passwd"}),  # 会失败（安全沙箱）
    ]

    for name, args in test_calls:
        print(f"\n调用: {name}({args})")
        try:
            result = registry.call_tool(name, args)
            print(f"  结果: {result}")
        except ValueError as exc:
            print(f"  错误: {exc}")


if __name__ == "__main__":
    demo()