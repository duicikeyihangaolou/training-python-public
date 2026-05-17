# s12: 工具注册与执行

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#12-工具的注册与执行)

本节演示 tools/list 和 tools/call 的实现。

## 核心概念

**tools/list**：

- 返回所有已注册工具的元数据（name / description / inputSchema）

**tools/call**：

- 根据 name + arguments 执行对应逻辑
- 错误处理：参数缺失 / 类型错误 / 执行异常 → JSON-RPC error

## 文件说明

| 文件                      | 说明      |
| ----------------------- | ------- |
| `tool_registry.py`      | 工具注册与执行 |
| `test_tool_registry.py` | 单元测试    |

## 运行方式

```bash
cd s12_tool_registration
python tool_registry.py
```
