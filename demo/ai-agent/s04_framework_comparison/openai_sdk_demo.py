#!/usr/bin/env python3
"""
s04: OpenAI Agents SDK 最小示例

演示如何使用 OpenAI Agents SDK 快速构建一个 Agent。

OpenAI Agents SDK 特点：
- 最小 boilerplate（~50 行跑通）
- 内置沙盒执行
- 结构化输出

运行方式：
    export OPENAI_API_KEY=sk-...
    pip install openai
    python openai_sdk_demo.py
"""

import os

try:
    from openai import OpenAI
except ImportError:
    print("错误：需要安装 openai SDK")
    print("  pip install openai")
    exit(1)


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

def get_openai_client():
    """创建 OpenAI 客户端"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("请设置 OPENAI_API_KEY 或 MINIMAX_API_KEY 环境变量")

    # MiniMax 使用 OpenAI 兼容接口
    api_url = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/v1")
    return OpenAI(api_key=api_key, base_url=api_url)


# --------------------------------------------------------------------------- #
# 工具定义
# --------------------------------------------------------------------------- #

# OpenAI 使用 function calling 格式，与 Claude略有不同
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calc",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
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
# OpenAI 兼容接口的工具调用
# --------------------------------------------------------------------------- #

def call_openai_with_tools(user_message: str, model: str = "MiniMax-M2.7") -> str:
    """
    使用 OpenAI 兼容接口调用工具

    与 Claude 的主要区别：
    - tools 格式略有不同（function calling 风格）
    - 响应格式：choices[].message.content / tool_calls
    - tool_result 通过 role: tool 的消息传递
    """
    client = get_openai_client()
    messages = [
        {"role": "system", "content": "你是一个有用的助手。"},
        {"role": "user", "content": user_message}
    ]

    max_iterations = 10
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools if tools else None,
            max_tokens=4096,
        )

        choice = response.choices[0]
        message = choice.message

        # 将 assistant 消息追加到历史
        messages.append({"role": "assistant", "content": message.content})

        if choice.finish_reason in ("stop", "length", None):
            # 直接回复
            return message.content or "(无内容)"

        elif choice.finish_reason == "tool_calls":
            # 工具调用
            tool_results = []
            for tc in message.tool_calls:
                tool_name = tc.function.name
                tool_args = eval(tc.function.arguments)  # JSON 字符串 → dict

                result = TOOL_HANDLERS[tool_name](**tool_args)

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })

            # tool_result 通过 role: tool 的消息传递
            messages.append(tool_results[0] if len(tool_results) == 1 else {"role": "user", "content": tool_results})
            continue

    return "达到最大迭代次数"


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示 OpenAI SDK 工具调用"""
    print("=" * 60)
    print("OpenAI Agents SDK 示例（MiniMax 兼容）")
    print("=" * 60)

    try:
        client = get_openai_client()
        print(f"✓ OpenAI 客户端创建成功")
    except Exception as e:
        print(f"✗ 配置错误: {e}")
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
            answer = call_openai_with_tools(query)
            print(f"答: {answer}")
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    demo()