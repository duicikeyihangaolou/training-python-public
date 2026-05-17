#!/usr/bin/env python3
"""
s04: LangGraph 最小示例

演示如何使用 LangGraph 构建状态机式的 Agent 工作流。

LangGraph 特点：
- 状态机/图模型，显式控制流程
- 支持 checkpoint（暂停/恢复）
- 适合复杂工作流、生产级应用

运行方式：
    pip install langgraph
    export OPENAI_API_KEY=sk-...
    python langgraph_demo.py
"""

import os

try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict, Annotated
    import operator
except ImportError:
    print("错误：需要安装 langgraph")
    print("  pip install langgraph")
    exit(1)


# --------------------------------------------------------------------------- #
# 定义 State（状态）
# --------------------------------------------------------------------------- #

class AgentState(TypedDict):
    """
    Agent 的状态

    每个节点可以读取和修改状态，状态在节点间传递。
    """
    messages: list
    next_action: str
    tool_result: str


# --------------------------------------------------------------------------- #
# 定义节点（Nodes）
# --------------------------------------------------------------------------- #

def call_llm(state: AgentState) -> AgentState:
    """
    调用 LLM 的节点

    根据状态中的 messages 调用 LLM，决定下一步动作
    """
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MINIMAX_API_KEY")
    if not api_key:
        return {"next_action": "error", "tool_result": "Missing API Key"}

    api_url = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/v1")
    client = OpenAI(api_key=api_key, base_url=api_url)

    messages = state.get("messages", [])
    if not messages:
        messages = [{"role": "user", "content": "你好"}]

    response = client.chat.completions.create(
        model="MiniMax-M2.7",
        messages=messages,
        max_tokens=4096,
    )

    choice = response.choices[0]
    message = choice.message

    messages.append({"role": "assistant", "content": message.content})

    # 简单的路由逻辑（实际应该根据 tool_calls 判断）
    if "天气" in str(messages):
        next_action = "call_tool"
    else:
        next_action = "end"

    return {
        "messages": messages,
        "next_action": next_action,
        "tool_result": ""
    }


def execute_tool(state: AgentState) -> AgentState:
    """
    执行工具的节点

    根据 LLM 的决定，调用对应工具
    """
    messages = state.get("messages", [])
    last_msg = messages[-1] if messages else {}

    # 简单模拟：如果消息中提到"北京"，调用天气工具
    content = str(last_msg.get("content", ""))
    if "北京" in content:
        tool_result = "北京天气：晴，15-25°C"
    else:
        tool_result = "未识别到需要调用的工具"

    messages.append({
        "role": "user",
        "content": f"[tool result] {tool_result}"
    })

    return {
        "messages": messages,
        "next_action": "end",
        "tool_result": tool_result
    }


def should_continue(state: AgentState) -> str:
    """
    路由决策：是否继续

    根据 next_action 决定下一步
    - "call_tool" → 执行工具
    - "end" → 结束
    - "error" → 结束
    """
    return state.get("next_action", "end")


# --------------------------------------------------------------------------- #
# 构建图
# --------------------------------------------------------------------------- #

def build_graph():
    """
    构建 LangGraph 图

    节点：call_llm → execute_tool
    边：根据 next_action 路由
    """
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("call_llm", call_llm)
    graph.add_node("execute_tool", execute_tool)

    # 设置入口节点
    graph.set_entry_point("call_llm")

    # 添加边
    graph.add_edge("call_llm", "execute_tool", condition=lambda s: s.get("next_action") == "call_tool")
    graph.add_edge("call_llm", END, condition=lambda s: s.get("next_action") in ("end", "error"))
    graph.add_edge("execute_tool", END)

    # 编译
    return graph.compile()


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示 LangGraph 状态机"""
    print("=" * 60)
    print("LangGraph 状态机示例")
    print("=" * 60)

    # 检查环境
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("警告：未设置 API Key，LLM 调用可能失败")
        print("  请设置 OPENAI_API_KEY / MINIMAX_API_KEY")

    try:
        app = build_graph()

        print("\n执行查询：'北京天气怎么样？'")
        result = app.invoke({
            "messages": [{"role": "user", "content": "北京天气怎么样？"}],
            "next_action": "",
            "tool_result": ""
        })

        print(f"\n✓ 执行完成")
        print(f"  最终消息数: {len(result['messages'])}")
        print(f"  工具结果: {result.get('tool_result', 'N/A')}")

        # 打印所有消息
        print("\n消息历史：")
        for i, msg in enumerate(result["messages"]):
            role = msg.get("role", "?")
            content = msg.get("content", "")[:80]
            print(f"  [{i}] {role}: {content}...")

    except Exception as e:
        print(f"\n✗ 执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo()