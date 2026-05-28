# s02: 工具描述与分发

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#2-工具描述与分发)

本节演示工具注册的核心思想：**Schema（告诉模型）+ Handler（告诉代码）**。

## 核心概念

```
LLM 看到 TOOLS（JSON Schema） → 选择工具名 → 代码查 TOOL_HANDLERS → 执行
```

**分发函数**（一次字典查找，无 if/elif 链）：

```python
def process_tool_call(tool_name, tool_input):
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"
    return handler(**tool_input)
```

## 文件说明

| 文件                    | 说明                           |
| ----------------------- | ------------------------------ |
| `tool_dispatch.py`      | 工具分发完整实现，包含安全沙箱 |
| `test_tool_dispatch.py` | 单元测试                       |

## 运行方式

```bash
cd s02_tool_dispatch
python tool_dispatch.py
```

## 测试

```bash
pytest test_tool_dispatch.py -v
```
