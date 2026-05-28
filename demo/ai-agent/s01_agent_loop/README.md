# s01: Agent 主循环

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#1-agent-主循环感知决策执行闭环)

本节演示从零实现 Agent 主循环，理解"感知→决策→执行"闭环。

## 核心概念

**Agent 就是 `while True` + `stop_reason`**：

```
User Input → messages[] → LLM API → stop_reason?
                                        ├── "end_turn" → 打印文本，结束
                                        └── "tool_use" → 执行工具，结果塞回 messages[]，继续循环
```

## 文件说明

| 文件                 | 说明                                       |
| -------------------- | ------------------------------------------ |
| `agent_loop.py`      | 主程序，从零实现 ~60 行主循环              |
| `mock_client.py`     | 模拟 LLM 客户端（当真实 API 不可用时使用） |
| `test_agent_loop.py` | 单元测试                                   |

## 运行方式

```bash
cd s01_agent_loop

# 确保在项目根目录安装了依赖
pip install -r requirements.txt

# 运行（使用真实 API）
python agent_loop.py

# 运行（使用模拟 LLM，无需 API Key）
python agent_loop.py --mock
```

## 测试

```bash
pytest test_agent_loop.py -v
```
