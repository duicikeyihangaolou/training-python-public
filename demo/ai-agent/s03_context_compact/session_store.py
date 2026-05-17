#!/usr/bin/env python3
"""
s03: 会话持久化 — JSONL 存储与重放

核心概念：
- 每个会话一个 .jsonl 文件，追加写入（原子操作）
- 四种记录类型：user / assistant / tool_use / tool_result
- 重放时通过 _rebuild_history() 重建 API 兼容的 messages[]

运行方式：
    python session_store.py
"""

import json
import time
import uuid
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #

@dataclass
class SessionRecord:
    """
    会话记录

    四种 type：
    - user: 用户消息 {"type": "user", "content": "...", "ts": ...}
    - assistant: 助手消息 {"type": "assistant", "content": [...], "ts": ...}
    - tool_use: 工具调用 {"type": "tool_use", "tool_use_id": "...", "name": "...", "input": {...}, "ts": ...}
    - tool_result: 工具结果 {"type": "tool_result", "tool_use_id": "...", "content": "...", "ts": ...}
    """
    type: str
    content: Optional[str] = None
    tool_use_id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[dict] = None
    ts: float = None

    def __post_init__(self):
        if self.ts is None:
            self.ts = time.time()

    def to_json(self) -> str:
        """序列化为一行 JSON"""
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "SessionRecord":
        """从一行 JSON 反序列化"""
        data = json.loads(json_str)
        return cls(**data)


# --------------------------------------------------------------------------- #
# SessionStore：会话持久化核心类
# --------------------------------------------------------------------------- #

class SessionStore:
    """
    会话存储

    核心功能：
    - append_turn()：追加一条记录到会话文件（原子写入）
    - load_session()：从会话文件重建 messages[]
    - _rebuild_history()：将扁平的 JSONL 记录转换为 API 兼容的 messages[]
    """

    def __init__(self, session_dir: str = "/tmp/ai_agent_sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.session_dir / f"{session_id}.jsonl"

    def append_record(self, session_id: str, record: SessionRecord) -> None:
        """
        追加一条记录到会话文件（原子操作）

        使用 'a' 模式追加写入，每条记录一行 JSON
        原子性由操作系统保证（写入单位是单次 write 调用）
        """
        path = self._session_path(session_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(record.to_json() + "\n")

    def append_user(self, session_id: str, content: str) -> None:
        """追加用户消息"""
        self.append_record(session_id, SessionRecord(type="user", content=content))

    def append_assistant(self, session_id: str, content: list) -> None:
        """
        追加助手消息

        Args:
            session_id: 会话 ID
            content: assistant 消息的 content 列表（Anthropic API 格式）
        """
        # content 是 block 列表，如 [{"type": "text", "text": "..."}]
        content_str = json.dumps(content, ensure_ascii=False)
        self.append_record(session_id, SessionRecord(type="assistant", content=content_str))

    def append_tool_use(self, session_id: str, tool_use_id: str, name: str, input: dict) -> None:
        """追加工具调用"""
        self.append_record(session_id, SessionRecord(
            type="tool_use",
            tool_use_id=tool_use_id,
            name=name,
            input=input
        ))

    def append_tool_result(self, session_id: str, tool_use_id: str, content: str) -> None:
        """追加工具结果"""
        self.append_record(session_id, SessionRecord(
            type="tool_result",
            tool_use_id=tool_use_id,
            content=content
        ))

    def _rebuild_history(self, session_id: str) -> list:
        """
        将扁平的 JSONL 记录转换为 API 兼容的 messages[]

        转换规则：
        - user 记录 → {"role": "user", "content": "..."}
        - assistant 记录 → {"role": "assistant", "content": [...]}，content 是 block 列表
        - tool_use → 合并到上一条 assistant 消息的 content 列表中
        - tool_result → 合并到下一条 user 消息的 content 列表中（Anthropic API 要求）

        重要：Anthropic API 格式要求 tool_result 在 user 消息中！
        """
        path = self._session_path(session_id)
        if not path.exists():
            return []

        messages = []
        pending_tool_results = []  # 等待合并到下一条 user 消息的 tool_result

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = SessionRecord.from_json(line)
                rtype = record.type

                if rtype == "user":
                    # 先把待处理的 tool_result 合并到 user 消息中
                    if pending_tool_results:
                        content = [{"type": "tool_result", **tr} for tr in pending_tool_results]
                        # 如果原本有 content，则合并
                        if record.content:
                            content.insert(0, {"type": "text", "text": record.content})
                        messages.append({"role": "user", "content": content})
                        pending_tool_results = []
                    else:
                        messages.append({"role": "user", "content": record.content})

                elif rtype == "assistant":
                    # assistant 消息的 content 是一个 block 列表
                    content = json.loads(record.content) if record.content else []
                    messages.append({"role": "assistant", "content": content})

                elif rtype == "tool_use":
                    # tool_use block 合并到上一条 assistant 消息
                    block = {
                        "type": "tool_use",
                        "id": record.tool_use_id,
                        "name": record.name,
                        "input": record.input
                    }
                    if messages and messages[-1]["role"] == "assistant":
                        messages[-1]["content"].append(block)
                    else:
                        # 没有 assistant 消息，创建一个空的
                        messages.append({"role": "assistant", "content": [block]})

                elif rtype == "tool_result":
                    # tool_result 暂时存着，等待合并到下一条 user 消息
                    pending_tool_results.append({
                        "tool_use_id": record.tool_use_id,
                        "content": record.content
                    })

        return messages

    def load_session(self, session_id: str) -> list:
        """
        加载会话历史，重建为 API 兼容的 messages[]

        这是外部调用的入口，封装了 _rebuild_history()
        """
        return self._rebuild_history(session_id)

    def list_sessions(self) -> list:
        """列出所有会话 ID"""
        sessions = []
        for f in self.session_dir.glob("*.jsonl"):
            sessions.append(f.stem)
        return sorted(sessions)

    def delete_session(self, session_id: str) -> None:
        """删除会话"""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示会话持久化流程"""
    store = SessionStore()

    # 创建测试会话
    session_id = f"test_{int(time.time())}"

    print("=" * 60)
    print("会话持久化演示")
    print("=" * 60)

    # 模拟完整的对话流程
    print("\n1. 模拟用户提问")
    store.append_user(session_id, "北京天气怎么样？")

    print("\n2. 模拟助手回复（包含 tool_use）")
    store.append_assistant(session_id, [
        {"type": "tool_use", "id": "tu_001", "name": "get_weather", "input": {"city": "北京"}}
    ])

    print("\n3. 模拟工具执行结果")
    store.append_tool_result(session_id, "tu_001", "北京天气：晴，温度 15-25°C")

    print("\n4. 模拟助手最终回复")
    store.append_assistant(session_id, [
        {"type": "text", "text": "北京今天天气晴朗，温度 15-25°C，适合外出。"}
    ])

    # 加载并验证
    print("\n5. 加载会话历史")
    messages = store.load_session(session_id)
    print(f"   共 {len(messages)} 条消息：")
    for i, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            print(f"   [{i}] {role}: {content[:50]}...")
        else:
            # content 是 block 列表
            block_types = [b.get("type") for b in content]
            print(f"   [{i}] {role}: {block_types}")

    # 列出所有会话
    print(f"\n6. 所有会话：{store.list_sessions()}")

    # 清理
    store.delete_session(session_id)
    print(f"\n7. 已清理测试会话 {session_id}")


if __name__ == "__main__":
    demo()