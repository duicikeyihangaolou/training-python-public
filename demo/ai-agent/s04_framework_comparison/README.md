# s04: 主流 Agent 框架对比

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#4-主流-agent-框架对比选讲)

本节对比四个主流 Agent 框架：**Claude Agent SDK / OpenAI Agents SDK / CrewAI / LangGraph**。

## 框架对比

| 框架                    | 特点                        | 适用场景                  |
| --------------------- | ------------------------- | --------------------- |
| **Claude Agent SDK**  | 原生 MCP、扩展思维、透明推理          | 深度用 Claude / 需 MCP 集成 |
| **OpenAI Agents SDK** | 最小 boilerplate、沙盒执行、结构化输出 | OpenAI 模型、追求简洁        |
| **CrewAI**            | 角色 + 任务 + 班组、多 Agent 协作   | 业务流程自动化、多角色任务         |
| **LangGraph**         | 状态机/图模型、checkpoint、可观测    | 复杂工作流、生产级控制           |

## 文件说明

| 文件                   | 说明                     |
| -------------------- | ---------------------- |
| `claude_sdk_demo.py` | Claude Agent SDK 最小示例  |
| `openai_sdk_demo.py` | OpenAI Agents SDK 最小示例 |
| `crewai_demo.py`     | CrewAI 角色+任务示例         |
| `langgraph_demo.py`  | LangGraph 状态机示例        |

## 运行方式

```bash
cd s04_framework_comparison

# Claude Agent SDK
pip install anthropic
python claude_sdk_demo.py

# OpenAI Agents SDK
pip install openai
python openai_sdk_demo.py

# CrewAI
pip install crewai
python crewai_demo.py

# LangGraph
pip install langgraph
python langgraph_demo.py
```

## 测试

```bash
pytest test_frameworks.py -v
```
