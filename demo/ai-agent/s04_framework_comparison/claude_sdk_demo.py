#!/usr/bin/env python3
"""
s04: Claude Agent SDK 最小示例

演示如何使用 Claude Agent SDK 快速构建一个带工具调用的 Agent。

Claude Agent SDK 特点：
- 原生 MCP 支持
- 扩展思维（Extended Thinking）
- API 设计最清晰

运行方式：
    export ANTHROPIC_API_KEY=sk-ant-...
    python claude_sdk_demo.py

注意：本 demo 需要安装 anthropic SDK: pip install anthropic
"""

import os

# --------------------------------------------------------------------------- #
# 检查依赖
# --------------------------------------------------------------------------- #

try:
    from anthropic import Anthropic
except ImportError:
    print("错误：需要安装 anthropic SDK")
    print("  pip install anthropic")
    exit(1)


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

def get_anthropic_client():
    """创建 Anthropic 客户端"""
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("请设置 ANTHROPIC_API_KEY 或 MINIMAX_API_KEY 环境变量")

    return Anthropic(api_key=api_key)


# --------------------------------------------------------------------------- #
# 工具定义（与之前一样的格式）
# --------------------------------------------------------------------------- #

tools = [
    {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "calc",
        "description": "计算数学表达式",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        }
    }
]


def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    weather_db = {"北京": "晴 15-25°C", "上海": "多云 18-28°C", "东京": "小雨 12-20°C"}
    return weather_db.get(city, f"不支持查询 {city} 的天气")


def calc(expression: str) -> str:
    """计算表达式"""
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"计算错误: {e}"


TOOL_HANDLERS = {
    "get_weather": get_weather,
    "calc": calc,
}


# --------------------------------------------------------------------------- #
# 使用 Claude Messages API（新版，不依赖 Agent SDK）
# --------------------------------------------------------------------------- #
# 注意：Claude 官方推荐使用 Messages API 而不是 Agent SDK，
# 因为 Messages API 更灵活，与手写主循环的概念一致。
# --------------------------------------------------------------------------- #

def call_claude_with_tools(user_message: str, system_prompt: str = "你是一个有用的助手。") -> str:
    """
    使用 Claude Messages API 调用工具

    这是 Claude SDK 的核心用法：
    1. messages.create() 传入 tools 列表
    2. 根据 stop_reason 判断是 end_turn 还是 tool_use
    3. 执行工具，结果合并到 messages，继续调用

    与手写 agent_loop 完全一致的概念！
    """
    client = get_anthropic_client()
    messages = [{"role": "user", "content": user_message}]

    max_iterations = 10
    for _ in range(max_iterations):
        # 调用 Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=4096,
        )

        # 将 assistant 响应追加到消息历史
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # 检查 stop_reason
        if response.stop_reason == "end_turn":
            # 提取文本回复
            text_parts = [block.text for block in response.content if hasattr(block, 'text')]
            return "\n".join(text_parts)

        elif response.stop_reason == "tool_use":
            # 执行工具，结果合并到 user 消息继续循环
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = TOOL_HANDLERS[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

    return "达到最大迭代次数"


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示 Claude SDK 工具调用"""
    print("=" * 60)
    print("Claude Agent SDK 示例")
    print("=" * 60)

    try:
        client = get_anthropic_client()
        print(f"✓ Anthropic 客户端创建成功")
        print(f"  API Key: ...{client.api_key[-4:]}")
    except Exception as e:
        print(f"✗ 配置错误: {e}")
        print("  提示: 使用 --mock 参数可以跳过 API 测试")
        return

    test_queries = [
        "北京天气怎么样？",
        "计算一下 2+3*5",
    ]

    print("\n开始测试...")
    for query in test_queries:
        print(f"\n问: {query}")
        print("-" * 40)
        try:
            answer = call_claude_with_tools(query)
            print(f"答: {answer}")
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    import sys
    if "--mock" in sys.argv:
        print("Claude SDK 需要真实 API Key，无法使用 mock")
        print("请设置 ANTHROPIC_API_KEY 环境变量")
    else:
        demo()