#!/usr/bin/env python3
"""
s15: Resources 与 Prompts

MCP 除了 Tools，还有 Resources 和 Prompts 两种能力。

Resources：只读数据，通过 resources/list / resources/read 暴露
Prompts：预定义提示模板，供 Client 获取后填变量

运行方式：
    python resources_demo.py
"""

import json
from typing import List, Optional


# --------------------------------------------------------------------------- #
# Resource 定义
# --------------------------------------------------------------------------- #

@dataclass
class Resource:
    """资源定义"""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"

    def to_metadata(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }


from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Prompt 模板定义
# --------------------------------------------------------------------------- #

@dataclass
class Prompt:
    """提示模板定义"""
    name: str
    description: str
    arguments: List[dict]  # [{"name": "xxx", "description": "...", "required": True/False}]

    def to_metadata(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "arguments": self.arguments
        }


# --------------------------------------------------------------------------- #
# Resources/Prompts 管理器
# --------------------------------------------------------------------------- #

class ResourceManager:
    """资源管理器"""

    def __init__(self):
        self.resources = []

    def register(self, uri: str, name: str, description: str, mime_type: str = "text/plain"):
        self.resources.append(Resource(uri=uri, name=name, description=description, mime_type=mime_type))

    def list_resources(self) -> List[dict]:
        return [r.to_metadata() for r in self.resources]

    def read_resource(self, uri: str) -> str:
        """读取资源内容（这里返回模拟内容）"""
        # 实际实现中，这里会根据 uri 读取真实数据
        if uri == "file://config":
            return json.dumps({"debug": True, "log_level": "info"}, indent=2)
        elif uri == "file://readme":
            return "# AI Agent Demo\n\n这是一个示例项目。"
        return f"Content of {uri}"


class PromptManager:
    """提示模板管理器"""

    def __init__(self):
        self.prompts = []

    def register(self, name: str, description: str, arguments: List[dict]):
        self.prompts.append(Prompt(name=name, description=description, arguments=arguments))

    def list_prompts(self) -> List[dict]:
        return [p.to_metadata() for p in self.prompts]

    def get_prompt(self, name: str, arguments: dict) -> str:
        """获取提示内容（填充变量）"""
        # 简单的模板替换
        templates = {
            "summarize": "请总结以下内容的要点：\n{content}",
            "translate": "请将以下内容翻译成{to_lang}：\n{content}",
            "review_code": "请审查以下代码，指出潜在问题：\n{code}",
        }
        template = templates.get(name, "请处理：\n{content}")
        return template.format(**arguments)


# --------------------------------------------------------------------------- #
# MCP 方法处理
# --------------------------------------------------------------------------- #

def handle_resources_list(params: dict, rm: ResourceManager) -> dict:
    """处理 resources/list 请求"""
    return {"resources": rm.list_resources()}


def handle_resources_read(params: dict, rm: ResourceManager) -> dict:
    """处理 resources/read 请求"""
    uri = params.get("uri", "")
    content = rm.read_resource(uri)
    return {
        "contents": [{
            "uri": uri,
            "mimeType": "text/plain",
            "text": content
        }]
    }


def handle_prompts_list(params: dict, pm: PromptManager) -> dict:
    """处理 prompts/list 请求"""
    return {"prompts": pm.list_prompts()}


def handle_prompts_get(params: dict, pm: PromptManager) -> dict:
    """处理 prompts/get 请求"""
    name = params.get("name", "")
    arguments = params.get("arguments", {})
    content = pm.get_prompt(name, arguments)
    return {
        "messages": [{
            "role": "user",
            "content": content
        }]
    }


# --------------------------------------------------------------------------- #
# 演示
# --------------------------------------------------------------------------- #

def demo():
    print("=" * 60)
    print("Resources 与 Prompts 演示")
    print("=" * 60)

    # 创建管理器
    rm = ResourceManager()
    pm = PromptManager()

    # 注册资源
    rm.register("file://config", "配置文件", "当前系统配置")
    rm.register("file://readme", "README", "项目说明文档")

    # 注册提示模板
    pm.register("summarize", "总结内容", [
        {"name": "content", "description": "要总结的内容", "required": True}
    ])
    pm.register("translate", "翻译内容", [
        {"name": "content", "description": "要翻译的内容", "required": True},
        {"name": "to_lang", "description": "目标语言", "required": True}
    ])

    print("\n1. Resources")
    print("-" * 40)
    resources = rm.list_resources()
    print(f"注册了 {len(resources)} 个资源：")
    for r in resources:
        print(f"  - {r['uri']}: {r['name']}")

    print("\n2. Prompts")
    print("-" * 40)
    prompts = pm.list_prompts()
    print(f"注册了 {len(prompts)} 个提示模板：")
    for p in prompts:
        print(f"  - {p['name']}: {p['description']}")

    print("\n3. 使用示例")
    print("-" * 40)

    # 读取资源
    print("\n读取 resource://config：")
    content = rm.read_resource("file://config")
    print(f"  内容：{content}")

    # 获取提示
    print("\n获取 summarize 提示（填充 content）：")
    prompt_content = pm.get_prompt("summarize", {"content": "这是一段很长的文本..."})
    print(f"  结果：{prompt_content[:60]}...")


if __name__ == "__main__":
    demo()