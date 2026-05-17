#!/usr/bin/env python3
"""
s03: 三层压缩与 3 阶段溢出保护

核心概念：
- Layer 1 (micro_compact): 每轮静默执行，将超过 KEEP_RECENT 轮的 tool_result 替换为占位符
- Layer 2 (auto_compact): token 超阈值时，保存对话到磁盘，LLM 生成摘要，替换历史
- Layer 3 (manual compact): 用户主动调用 compact 工具，触发同样的压缩逻辑

3 阶段溢出保护 (guard_api_call):
- Attempt 0: 正常调用
- Attempt 1: 溢出 → 截断过大的 tool_result
- Attempt 2: 还溢出 → LLM 摘要压缩历史

运行方式：
    python compact.py
"""

import json
import time
import re
from pathlib import Path
from typing import Callable, Any


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

KEEP_RECENT = 3          # micro_compact：保留最近几轮 tool_result
TOKEN_THRESHOLD = 50000  # auto_compact 触发阈值
TRANSCRIPT_DIR = Path("/tmp/ai_agent_transcripts")
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Layer 1: micro_compact
# --------------------------------------------------------------------------- #

def micro_compact(messages: list, keep_recent: int = KEEP_RECENT) -> None:
    """
    每轮静默执行的微压缩

    逻辑：
    - 遍历所有 user 消息中的 tool_result block
    - 超过 keep_recent 轮的旧 tool_result → 替换为占位符 "[Previous: used {tool_name}]"

    注意：此函数直接修改 messages 列表（in-place）
    """
    for msg in messages:
        if msg.get("role") != "user":
            continue

        content = msg.get("content", [])
        if not isinstance(content, list):
            continue

        # 统计当前消息之前有多少 tool_result
        tool_result_count = 0
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_result_count += 1

        # 如果当前 block 是 tool_result 且太旧了，替换为占位符
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                # 超过 keep_recent 轮，替换为占位符
                if tool_result_count > keep_recent:
                    tool_name = "unknown"
                    # 尝试从 content 中提取工具名（如果有的话）
                    block["content"] = f"[Previous: used {tool_name}]"
                tool_result_count -= 1


def estimate_tokens(text: str) -> int:
    """
    简单估算 token 数量

    估算方法：中英文都按字符数 / 4 估算（实际 token 数取决于模型）
    精确计算需要 tiktoken 等库，这里用简化算法
    """
    return len(text) // 4


# --------------------------------------------------------------------------- #
# Layer 2: auto_compact
# --------------------------------------------------------------------------- #

def save_transcript(messages: list, transcript_id: str = None) -> Path:
    """
    保存完整对话到 transcripts 目录，便于恢复

    Args:
        messages: 消息列表
        transcript_id: 可选的 transcript ID，默认用时间戳

    Returns:
        保存的文件路径
    """
    if transcript_id is None:
        transcript_id = str(int(time.time()))

    path = TRANSCRIPT_DIR / f"transcript_{transcript_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    return path


def auto_compact(messages: list, summarize_fn: Callable[[list], str]) -> list:
    """
    自动压缩：当 token 超过阈值时，保存历史并生成摘要

    步骤：
    1. 保存完整对话到 .transcripts/ 目录
    2. 调用 summarize_fn 生成摘要（通常是 LLM）
    3. 用摘要替换所有消息，只保留最近 1-2 条

    Args:
        messages: 当前消息列表
        summarize_fn: 摘要生成函数，输入 messages，返回摘要字符串

    Returns:
        压缩后的消息列表
    """
    # 1. 保存 transcript
    path = save_transcript(messages)
    print(f"  [auto_compact] 保存 transcript 到 {path}")

    # 2. 生成摘要
    summary = summarize_fn(messages)
    print(f"  [auto_compact] 生成摘要，共 {len(summary)} 字符")

    # 3. 用摘要替换消息
    compacted = [
        {"role": "user", "content": f"[压缩的历史对话]\n{summary}"},
        {"role": "assistant", "content": "Understood. 我已了解之前的对话内容，继续回答。"}
    ]

    return compacted


def auto_compact_with_mock_llm(messages: list) -> list:
    """
    使用模拟 LLM 生成摘要的 auto_compact（演示用）

    实际项目中这里会调用真实的 LLM API
    """
    def mock_summarize(msgs: list) -> str:
        # 简单模拟：提取每条消息的 role 和前 20 字符
        lines = []
        for msg in msgs[:10]:  # 只看前 10 条
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " | ".join(c.get("text", c.get("name", "")) for c in content if isinstance(c, dict))
            lines.append(f"{role}: {content[:50]}")
        return "\n".join(lines) + f"\n...(共 {len(msgs)} 条消息)"

    return auto_compact(messages, mock_summarize)


# --------------------------------------------------------------------------- #
# Layer 3: manual compact
# --------------------------------------------------------------------------- #

def manual_compact(messages: list, summarize_fn: Callable[[list], str]) -> list:
    """
    手动压缩：用户主动调用 compact 工具

    与 auto_compact 逻辑相同，但可以由用户在任意时刻触发
    """
    return auto_compact(messages, summarize_fn)


# --------------------------------------------------------------------------- #
# 3 阶段溢出保护
# --------------------------------------------------------------------------- #

class ContextGuard:
    """
    上下文溢出保护器

    使用方式：
        guard = ContextGuard(api_call_fn)
        result = guard.call(model="xxx", messages=[...])
        # 如果溢出，自动重试（截断 → 压缩）
    """

    def __init__(self, api_call_fn: Callable):
        """
        Args:
            api_call_fn: 实际执行 API 调用的函数，签名与 client.messages.create 类似
        """
        self.api_call_fn = api_call_fn

    def call(self, *args, **kwargs):
        """
        执行 API 调用，带溢出保护

        3 阶段重试：
        1. 正常调用
        2. 溢出 → 截断过大的 tool_result
        3. 还溢出 → LLM 摘要压缩
        """
        current_messages = kwargs.get("messages", [])

        for attempt in range(3):
            try:
                result = self.api_call_fn(*args, **kwargs)
                # 调用成功，更新 kwargs 中的 messages（以防被截断/压缩修改了）
                if current_messages is not kwargs.get("messages"):
                    kwargs["messages"][:] = current_messages
                return result

            except Exception as exc:
                error_str = str(exc).lower()
                is_overflow = "context" in error_str or "token" in error_str or "maximum" in error_str

                if not is_overflow or attempt >= 2:
                    raise  # 非溢出错误，或已达到最大重试次数

                print(f"  [ContextGuard] Attempt {attempt + 1} 溢出，准备重试...")

                if attempt == 0:
                    # 第一阶段：截断过大的 tool_result
                    current_messages = self._truncate_large_tool_results(current_messages)
                    kwargs["messages"] = current_messages

                elif attempt == 1:
                    # 第二阶段：压缩历史
                    current_messages = auto_compact_with_mock_llm(current_messages)
                    kwargs["messages"] = current_messages

        raise RuntimeError("ContextGuard: 达到最大重试次数仍失败")

    def _truncate_large_tool_results(self, messages: list, max_len: int = 2000) -> list:
        """
        截断过大的 tool_result 内容

        遍历所有 tool_result block，将超长内容截断到 max_len 字符
        """
        import copy
        truncated = copy.deepcopy(messages)

        for msg in truncated:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue

            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    original = block.get("content", "")
                    if len(original) > max_len:
                        block["content"] = original[:max_len] + f"\n... (已截断，原长 {len(original)})"

        return truncated


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示三层压缩和 3 阶段保护"""
    print("=" * 60)
    print("三层压缩与溢出保护演示")
    print("=" * 60)

    # 模拟消息历史（包含多条 tool_result）
    messages = [
        {"role": "user", "content": "北京天气？"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "1", "name": "get_weather", "input": {"city": "北京"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "content": "北京：晴，15-25度"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "北京今天晴朗！"}]},
        {"role": "user", "content": "上海呢？"},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "2", "name": "get_weather", "input": {"city": "上海"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "2", "content": "上海：多云，18-28度"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "上海多云。"}]},
    ]

    print(f"\n1. 原始消息数: {len(messages)}")

    # Layer 1: micro_compact
    print("\n2. Layer 1 (micro_compact):")
    micro_compact(messages, keep_recent=2)
    print(f"   压缩后消息数: {len(messages)}")
    for msg in messages:
        if msg["role"] == "user":
            for block in msg.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    print(f"   tool_result: {block['content'][:50]}...")

    # Layer 2: auto_compact
    print("\n3. Layer 2 (auto_compact):")
    compacted = auto_compact_with_mock_llm(list(messages))
    print(f"   压缩后消息数: {len(compacted)}")
    print(f"   第一条消息前 100 字符: {compacted[0]['content'][:100]}...")

    # Layer 3: manual_compact（同 auto_compact，只是触发方式不同）
    print("\n4. Layer 3 (manual_compact): 与 auto_compact 相同，可由用户主动触发")

    # 3 阶段溢出保护演示
    print("\n5. 3 阶段溢出保护 (ContextGuard):")

    def mock_api_call(messages):
        # 模拟 API 调用
        total_tokens = sum(estimate_tokens(str(m)) for m in messages)
        if total_tokens > 30000:
            raise Exception("Context window exceeded")
        return {"stop_reason": "end_turn", "content": [{"type": "text", "text": "OK"}]}

    guard = ContextGuard(mock_api_call)

    # 测试正常调用
    print("   正常调用: ", end="")
    result = guard.call(messages=[{"role": "user", "content": "hi"}])
    print("成功")

    print("\n演示完成！")


if __name__ == "__main__":
    demo()