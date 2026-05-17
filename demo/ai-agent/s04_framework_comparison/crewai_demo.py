#!/usr/bin/env python3
"""
s04: CrewAI 最小示例

演示如何使用 CrewAI 构建多角色 Agent 协作。

CrewAI 特点：
- 角色 + 任务 + 班组（Crew）
- 适合业务流程自动化、多角色协作
- 代码可读性好

运行方式：
    pip install crewai
    export OPENAI_API_KEY=sk-...  # 或其他 LLM API Key
    python crewai_demo.py

注意：CrewAI 需要 Serper 等工具的 API Key 才能运行搜索工具
"""

import os

try:
    from crewai import Agent, Task, Crew
except ImportError:
    print("错误：需要安装 crewai")
    print("  pip install crewai")
    exit(1)


# --------------------------------------------------------------------------- #
# 定义工具（简单版本，不依赖 Serper 等外部服务）
# --------------------------------------------------------------------------- #

def search_web(query: str) -> str:
    """模拟网页搜索（实际项目中替换为真实搜索 API）"""
    return f"搜索结果：关于 '{query}' 的信息...\n1. 相关文章 A\n2. 相关文章 B\n3. 相关文章 C"


def write_file(path: str, content: str) -> str:
    """模拟写文件"""
    return f"已写入文件 {path}，共 {len(content)} 字符"


# --------------------------------------------------------------------------- #
# 定义 Agent（角色）
# --------------------------------------------------------------------------- #

def create_agents():
    """
    创建两个 Agent：
    - 研究员（Researcher）：负责搜索信息
    - 写手（Writer）：负责总结并写文件
    """

    researcher = Agent(
        role="研究员",
        goal="搜索并整理关于用户问题的相关信息",
        backstory="你是一名专业研究员，擅长从互联网搜索并整理信息。",
        verbose=True,
        tools=[search_web],
    )

    writer = Agent(
        role="写手",
        goal="将研究结果整理成清晰的文档",
        backstory="你是一名专业写手，擅长将复杂信息整理成易于理解的文档。",
        verbose=True,
        tools=[write_file],
    )

    return researcher, writer


# --------------------------------------------------------------------------- #
# 定义 Task（任务）
# --------------------------------------------------------------------------- #

def create_tasks(researcher: Agent, writer: Agent):
    """
    创建任务流程：
    1. 研究员搜索信息
    2. 写手根据研究结果写报告
    """

    research_task = Task(
        description="搜索有关 AI Agent 最新发展的信息，并整理成摘要",
        agent=researcher,
        expected_output="关于 AI Agent 最新发展的摘要报告",
    )

    write_task = Task(
        description="根据研究员的摘要，写一份简短的报告并保存到 report.txt",
        agent=writer,
        expected_output="一份保存在 report.txt 的报告",
    )

    return research_task, write_task


# --------------------------------------------------------------------------- #
# 运行 Crew（班组）
# --------------------------------------------------------------------------- #

def run_crew(query: str):
    """
    运行 CrewAI 的班组流程

    流程：研究员搜索 → 写手写报告
    """
    researcher, writer = create_agents()
    research_task, write_task = create_tasks(researcher, writer)

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, write_task],
        verbose=True,
    )

    print(f"\n开始执行：{query}")
    result = crew.kickoff()

    print(f"\n最终结果：{result}")
    return result


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    """演示 CrewAI 多角色协作"""
    print("=" * 60)
    print("CrewAI 多角色 Agent 协作示例")
    print("=" * 60)

    # 检查环境
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("MINIMAX_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("警告：未设置 API Key，CrewAI 可能无法正常运行")
        print("  请设置 OPENAI_API_KEY / MINIMAX_API_KEY / ANTHROPIC_API_KEY")

    try:
        # 简单的同步执行演示
        result = run_crew("AI Agent 的最新发展趋势")
        print(f"\n✓ Crew 执行完成")
    except Exception as e:
        print(f"\n✗ Crew 执行出错: {e}")
        print("  （这可能是因为缺少 API Key 或依赖未安装）")


if __name__ == "__main__":
    demo()