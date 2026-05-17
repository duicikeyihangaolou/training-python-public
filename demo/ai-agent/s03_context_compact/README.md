# s03: 上下文管理与会话持久化

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#3-上下文管理与会话持久化)

本节演示三层压缩策略、JSONL 会话持久化和 3 阶段溢出保护。

## 核心概念

**三层压缩**：

1. **micro_compact**：每轮静默执行，将超过 3 轮的 tool_result 替换为占位符
2. **auto_compact**：token 超阈值时，保存对话到磁盘，LLM 生成摘要，替换历史
3. **manual compact**：用户主动调用 compact 工具

**会话持久化**：

- 每个会话一个 `.jsonl` 文件，追加写入（原子操作）
- 重放时通过 `_rebuild_history()` 重建 API 兼容的 `messages[]`

## 文件说明

| 文件                 | 说明               |
| ------------------ | ---------------- |
| `session_store.py` | JSONL 会话持久化 + 重放 |
| `compact.py`       | 三层压缩 + 3 阶段溢出保护  |
| `test_session.py`  | 会话存储单元测试         |

## 运行方式

```bash
cd s03_context_compact
python session_store.py    # 测试会话持久化
python compact.py           # 测试三层压缩
```

## 测试

```bash
pytest test_session.py -v
```
