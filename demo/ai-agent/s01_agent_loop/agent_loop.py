#!/usr/bin/env python3
"""
s01: Agent 主循环 — 从零实现感知→决策→执行闭环

本文件演示一个最小的 Agent 主循环，帮助理解底层工作原理。
不依赖 LangChain 等框架，纯 Python 实现 ~60 行核心逻辑。

核心流程：
1. 用户输入 → 加入 messages[]
2. 调用 LLM API，传入 messages + tools
3. 检查 stop_reason：
   - "end_turn" → 模型完成回复，打印输出，结束
   - "tool_use" → 模型想调用工具，执行工具，结果塞回 messages[]，继续循环

运行方式：
    python agent_loop.py                 # 使用真实 API
    python agent_loop.py --mock         # 使用模拟 LLM（无需 API Key）
"""

import sys
import json
from typing import Literal

# --------------------------------------------------------------------------- #
# 模拟 LLM 客户端（当 --mock 时使用，帮助无 API Key 时也能跑通理解流程）
# --------------------------------------------------------------------------- #

class MockLLMClient:
    """
    模拟 LLM 客户端，用于在没有 API Key 时演示 Agent 循环流程。

    模拟逻辑：
    - 如果用户问"天气"相关的问题，返回一个 tool_use 调用 get_weather
    - 如果用户说"直接回答"，返回 end_turn（直接回复）
    - 其他情况返回 text 回复
    """

    def __init__(self, model: str = "mock"):
        self.model = model

    def messages_create(self, *, model: str, system: str, messages: list, tools: list, max_tokens: int):
        """
        模拟 messages.create() 的返回结构

        返回值是一个 dict，具有以下关键字段：
        - stop_reason: "end_turn" | "tool_use"
        - content: list[dict]，每个元素是 text 或 tool_use block
        """
        # 取最后一条用户消息
        last_user_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, str):
                    last_user_msg = content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "tool_result":
                            last_user_msg += part.get("content", "")
                break

        # 简单的模拟逻辑
        if "weather" in last_user_msg.lower() or "天气" in last_user_msg:
            # 模拟模型决定调用工具
            return {
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_001",
                        "name": "get_weather",
                        "input": {"city": last_user_msg.replace("天气", "").replace("weather", "").strip() or "北京"}
                    }
                ]
            }
        else:
            # 模拟模型直接回复
            return {
                "stop_reason": "end_turn",
                "content": [
                    {
                        "type": "text",
                        "text": f"[模拟回复] 我收到了你的消息: {last_user_msg[:50]}..."
                    }
                ]
            }


# --------------------------------------------------------------------------- #
# 工具定义（Schema + Handler）
# --------------------------------------------------------------------------- #

# TOOLS 列表：告诉 LLM 有哪些工具可用，每个工具是一个 JSON Schema
TOOLS = [
    {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如：北京、上海、东京"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calc",
        "description": "计算数学表达式的值",
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

# TOOL_HANDLERS 字典：工具名 → 处理函数，工具注册的中心表
TOOL_HANDLERS = {}


def tool_get_weather(city: str) -> str:
    """
    获取城市天气（模拟实现）

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    # 实际项目中这里会调用天气 API，这里做模拟
    weather_db = {
        "北京": "晴，温度 15-25°C",
        "上海": "多云，温度 18-28°C",
        "东京": "小雨，温度 12-20°C",
    }
    return weather_db.get(city, f"抱歉，暂时不支持查询 {city} 的天气")


def tool_calc(expression: str) -> str:
    """
    计算数学表达式（模拟实现）

    Args:
        expression: 数学表达式字符串

    Returns:
        计算结果的字符串形式
    """
    try:
        # 注意：eval 在生产环境中禁用！这里仅用于演示
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


# 注册工具处理器
TOOL_HANDLERS["get_weather"] = tool_get_weather
TOOL_HANDLERS["calc"] = tool_calc


# --------------------------------------------------------------------------- #
# 分发函数：根据工具名调用对应 Handler
# --------------------------------------------------------------------------- #

def process_tool_call(tool_name: str, tool_input: dict) -> str:
    """
    分发工具调用

    这是整个工具系统的核心：给定工具名和参数，通过字典查找执行对应函数。
    不需要 if/elif 链式判断，扩展时只需在 TOOL_HANDLERS 中添加条目。

    Args:
        tool_name: 工具名称（如 "get_weather"）
        tool_input: 工具参数字典（如 {"city": "北京"}）

    Returns:
        工具执行结果的字符串
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        return handler(**tool_input)
    except TypeError as exc:
        # 参数类型/个数不匹配
        return f"Error: Invalid arguments for {tool_name}: {exc}"
    except Exception as exc:
        # 其他执行错误
        return f"Error: {tool_name} failed: {exc}"


# --------------------------------------------------------------------------- #
# 主循环：Agent 的核心
# --------------------------------------------------------------------------- #

def agent_loop(query: str, client, model: str, system: str = "你是一个有用的AI助手。") -> str:
    """
    Agent 主循环

    核心逻辑（伪代码）：
        messages = [user query]
        while True:
            response = LLM(messages + tools)
            messages += response

            if stop_reason == "end_turn":
                return text response
            else (stop_reason == "tool_use"):
                for each tool_call in response:
                    result = process_tool_call(tool_name, tool_input)
                    messages += tool_result(user message)
                continue (loop again)

    Args:
        query: 用户输入的问题
        client: LLM 客户端对象（有 messages_create 方法）
        model: 模型名称
        system: 系统提示词

    Returns:
        Agent 的最终文本回复
    """
    # 初始化消息历史，用户输入作为第一条消息
    messages = [{"role": "user", "content": query}]

    # 打印分隔线
    print(f"\n{'='*60}")
    print(f"User: {query}")
    print(f"{'='*60}\n")

    # 主循环：持续调用 LLM，直到 stop_reason 不是 "tool_use"
    while True:
        # 调用 LLM API
        # 注意：这是 Anthropic API 的调用格式，如果是 OpenAI 则略有不同
        try:
            response = client.messages_create(
                model=model,
                system=system,
                messages=messages,
                tools=TOOLS,
                max_tokens=8000,
            )
        except Exception as exc:
            print(f"API 调用失败: {exc}")
            return f"错误：无法连接到 LLM API - {exc}"

        # 将 assistant 响应追加到消息历史
        messages.append({"role": "assistant", "content": response["content"]})

        # 打印 assistant 的原始响应（调试用）
        print(f"[Debug] stop_reason = {response['stop_reason']}")
        print(f"[Debug] content = {response['content']}\n")

        # 根据 stop_reason 分支
        if response["stop_reason"] == "end_turn":
            # 模型完成回复，提取文本并返回
            text_parts = []
            for block in response["content"]:
                if block.get("type") == "text":
                    text_parts.append(block["text"])
            final_text = "\n".join(text_parts)

            print(f"{'='*60}")
            print(f"Assistant: {final_text}")
            print(f"{'='*60}\n")

            return final_text

        elif response["stop_reason"] == "tool_use":
            # 模型想调用工具，收集所有工具调用的结果
            tool_results = []

            for block in response["content"]:
                if block.get("type") != "tool_use":
                    continue

                tool_name = block["name"]
                tool_input = block["input"]
                tool_id = block["id"]

                print(f"[Tool Call] {tool_name}({tool_input})")

                # 执行工具
                result = process_tool_call(tool_name, tool_input)
                print(f"[Tool Result] {result}")

                # 构造 tool_result 块，注意格式
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result
                })

            # 将工具结果作为新的一条 user 消息，追加到消息历史
            # 重要：Anthropic API 要求 tool_result 必须在 user 角色的消息中
            messages.append({"role": "user", "content": tool_results})

            # 继续循环，让 LLM 处理工具返回的结果
            print()
            continue

        else:
            # 其他 stop_reason（如 max_tokens），返回部分结果
            text_parts = [b.get("text", "") for b in response["content"] if b.get("type") == "text"]
            return "\n".join(text_parts)


# --------------------------------------------------------------------------- #
# 真实 LLM 客户端（使用 OpenAI 兼容接口）
# --------------------------------------------------------------------------- #

class RealLLMClient:
    """
    真实的 LLM 客户端，支持 OpenAI 兼容接口（MiniMax / OpenAI / Anthropic）

    使用方式：
        client = RealLLMClient(api_url="https://api.minimaxi.com/v1",
                               api_key="sk-xxx",
                               model="MiniMax-M2.7")
        response = client.messages_create(model="MiniMax-M2.7", ...)
    """

    def __init__(self, api_url: str, api_key: str, model: str):
        import openai
        self.client = openai.OpenAI(api_key=api_key, base_url=api_url)
        self.default_model = model

    def messages_create(self, *, model: str, system: str, messages: list, tools: list, max_tokens: int):
        """
        调用 LLM API（OpenAI 兼容格式）

        与 Anthropic 的 messages.create() 略有不同：
        - OpenAI 使用 function calling 风格的 tools
        - 返回格式是 choices[].message
        """
        # 转换 tools 格式（Anthropic style → OpenAI style）
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object"})
                }
            })

        # 构建消息（OpenAI 格式）
        chat_messages = [{"role": "system", "content": system}]
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # tool_result 需要特殊处理
            if role == "user" and isinstance(content, list):
                # content 是 tool_result 列表
                new_content = []
                for item in content:
                    if item.get("type") == "tool_result":
                        new_content.append({
                            "role": "tool",
                            "tool_call_id": item["tool_use_id"],
                            "content": item["content"]
                        })
                chat_messages.append({"role": "user", "content": new_content})
            else:
                chat_messages.append({"role": role, "content": content})

        # 调用 API
        response = self.client.chat.completions.create(
            model=model,
            messages=chat_messages,
            tools=openai_tools if openai_tools else None,
            max_tokens=max_tokens,
        )

        # 转换响应格式（OpenAI → Anthropic 风格，方便统一处理）
        choice = response.choices[0]
        message = choice.message

        stop_reason = "end_turn" if choice.finish_reason in (None, "stop", "length") else "tool_use"

        content = []
        if message.content:
            content.append({"type": "text", "text": message.content})

        if message.tool_calls:
            for tc in message.tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments)
                })

        return {
            "stop_reason": stop_reason,
            "content": content
        }


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #

def main():
    """主入口：根据命令行参数决定使用真实 API 还是模拟 LLM"""
    # 解析命令行参数
    use_mock = "--mock" in sys.argv

    if use_mock:
        # 使用模拟 LLM（不需要 API Key）
        print("使用模拟 LLM（无需 API Key）")
        client = MockLLMClient()
        model = "mock"
    else:
        # 使用真实 API
        import sys
        sys.path.insert(0, str(__file__).rsplit("/", 2)[0])  # 添加项目根目录到 path
        from config import get_api_key, get_api_url, get_model

        try:
            api_key = get_api_key()
            api_url = get_api_url()
            model = get_model()
            print(f"使用真实 API: {api_url}")
            print(f"模型: {model}")
            client = RealLLMClient(api_url=api_url, api_key=api_key, model=model)
        except ValueError as e:
            print(f"配置错误: {e}")
            print("提示: 使用 --mock 参数可以无需 API Key 运行")
            sys.exit(1)

    # 几个测试 query
    test_queries = [
        "北京今天天气怎么样？",
        "计算一下 2+3*5 等于多少",
    ]

    print("\n" + "=" * 60)
    print("欢迎使用 AI Agent 主循环演示")
    print("=" * 60)
    print("\n本演示包含 2 个测试 query：")
    for i, q in enumerate(test_queries, 1):
        print(f"  {i}. {q}")
    print("\n")

    for query in test_queries:
        agent_loop(query, client, model)


if __name__ == "__main__":
    main()