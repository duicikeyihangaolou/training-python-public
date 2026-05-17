#!/usr/bin/env python3
"""
s16: 完整实战 — Agent 作为 MCP Client

本节演示 Agent 如何作为 MCP Client：
1. 启动 MCP Server（子进程）
2. 发送 initialize 握手
3. 发送 tools/list 获取工具列表
4. 将工具列表转为 LLM 可读格式
5. LLM 决定调工具 → 发送 tools/call
6. 结果返回给 LLM → 生成最终回复

运行方式：
    python agent_client.py

注意：这个 demo 需要先启动 mcp_server.py（在同一台机器上）
"""

import json
import subprocess
import sys
from typing import Optional


# --------------------------------------------------------------------------- #
# MCP Client
# --------------------------------------------------------------------------- #

class MCPClient:
    """
    MCP Client 实现

    通过 stdio 与 MCP Server 通信
    """

    def __init__(self, server_command: list):
        self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    def start(self):
        """启动 MCP Server 作为子进程"""
        self.process = subprocess.Popen(
            self.server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"[Client] 启动 Server: {' '.join(self.server_command)}")

    def stop(self):
        """停止 MCP Server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("[Client] Server 已停止")

    def send_request(self, method: str, params: dict = None) -> dict:
        """
        发送 JSON-RPC 请求

        Args:
            method: 方法名
            params: 参数字典

        Returns:
            响应字典
        """
        if not self.process:
            raise RuntimeError("Server 未启动")

        self.request_id += 1
        req_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        # 发送请求
        req_line = json.dumps(request, ensure_ascii=False)
        print(f"[Client] → {method} (id={req_id})", file=sys.stderr)
        self.process.stdin.write(req_line + "\n")
        self.process.stdin.flush()

        # 读取响应
        resp_line = self.process.stdout.readline()
        if not resp_line:
            raise RuntimeError("Server 已关闭连接")

        response = json.loads(resp_line.strip())
        print(f"[Client] ← {response.get('result', response.get('error'))}", file=sys.stderr)

        return response

    def initialize(self) -> dict:
        """发送 initialize 握手"""
        return self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agent-client", "version": "1.0.0"}
        })

    def list_tools(self) -> list:
        """发送 tools/list"""
        response = self.send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> str:
        """发送 tools/call"""
        response = self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        result = response.get("result", {})
        content = result.get("content", [])
        if content:
            return content[0].get("text", "")
        return ""


# --------------------------------------------------------------------------- #
# Agent 实现
# --------------------------------------------------------------------------- #

class Agent:
    """
    简单的 Agent实现

    使用 MCP Client 获取工具，将工具列表发给 LLM，
    LLM 决定调工具后，通过 MCP 调用返回结果
    """

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools = []

    def setup(self):
        """初始化 Agent：启动 Server，获取工具列表"""
        print("[Agent] 初始化...")

        # 启动 MCP Server
        self.mcp_client.start()

        # 初始化握手
        init_result = self.mcp_client.initialize()
        print(f"[Agent] 握手成功: {init_result.get('result', {}).get('serverInfo', {})}")

        # 获取工具列表
        self.tools = self.mcp_client.list_tools()
        print(f"[Agent] 发现 {len(self.tools)} 个工具")

    def tools_to_llm_format(self) -> list:
        """将 MCP tools 转为 LLM 可读的格式"""
        # 简化：直接返回 MCP 的 tool 列表
        # 实际应该根据使用的 LLM API 转换格式
        return self.tools

    def ask_llm(self, question: str) -> dict:
        """
        模拟 LLM 决策

        实际项目中，这里会调用真实的 LLM API
        这里用简单规则模拟：
        - 如果问题包含"天气"→调用 get_weather
        - 如果问题包含"系统"→调用 get_system_info
        - 其他→返回"我不知道"
        """
        print(f"[Agent] LLM 决策: {question}")

        if "天气" in question or "weather" in question.lower():
            # 提取城市名
            city = "北京"
            for word in question:
                if word in ["北京", "上海", "东京", "纽约"]:
                    city = word
                    break
            return {"tool": "get_weather", "arguments": {"city": city}}

        elif "系统" in question or "system" in question.lower():
            return {"tool": "get_system_info", "arguments": {}}

        return {"tool": None, "arguments": {}}

    def run(self, question: str) -> str:
        """
        运行 Agent 处理问题

        Args:
            question: 用户问题

        Returns:
            Agent 的回复
        """
        # 1. LLM 决策
        decision = self.ask_llm(question)

        if not decision["tool"]:
            return "抱歉，我不知道如何回答这个问题。"

        # 2. 通过 MCP 调用工具
        tool_name = decision["tool"]
        arguments = decision["arguments"]

        try:
            result = self.mcp_client.call_tool(tool_name, arguments)
            return f"工具 {tool_name} 返回：\n{result}"
        except Exception as e:
            return f"调用工具失败: {e}"

    def cleanup(self):
        """清理资源"""
        self.mcp_client.stop()


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("Agent + MCP Server 完整闭环演示")
    print("=" * 60)

    # 创建 MCP Client
    # 假设 mcp_server.py 在同目录下
    server_script = Path(__file__).parent / "mcp_server.py"
    mcp_client = MCPClient([sys.executable, str(server_script)])

    # 创建 Agent
    agent = Agent(mcp_client)

    try:
        # 初始化
        agent.setup()

        print("\n" + "=" * 60)
        print("开始对话（输入 quit 退出）")
        print("=" * 60)

        while True:
            question = input("\n你: ").strip()
            if question.lower() in ("quit", "exit"):
                break
            if not question:
                continue

            answer = agent.run(question)
            print(f"\nAgent: {answer}")

    finally:
        agent.cleanup()


def demo_scripted():
    """脚本化演示（不需交互）"""
    print("=" * 60)
    print("Agent + MCP Server 脚本化演示")
    print("=" * 60)

    # 创建 MCP Client
    server_script = Path(__file__).parent / "mcp_server.py"
    mcp_client = MCPClient([sys.executable, str(server_script)])

    # 创建 Agent
    agent = Agent(mcp_client)

    try:
        agent.setup()

        # 测试问题
        questions = [
            "北京天气怎么样？",
            "你的系统信息是什么？",
        ]

        for question in questions:
            print(f"\n问题: {question}")
            answer = agent.run(question)
            print(f"回答: {answer}")

    finally:
        agent.cleanup()


if __name__ == "__main__":
    if "--interactive" in sys.argv:
        demo()
    else:
        demo_scripted()