#!/usr/bin/env python3
"""
s16: 完整实战 — MCP Server（stdio 模式）

这是一个完整的 MCP Server 实现，支持：
- initialize（握手）
- tools/list（列出工具）
- tools/call（调用工具）

工具：get_weather / read_file_summary / get_system_info

运行方式：
    python mcp_server.py

然后可以用以下命令测试：
    echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python mcp_server.py
    echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python mcp_server.py
    echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_weather","arguments":{"city":"北京"}}}' | python mcp_server.py
"""

import json
import sys
import platform
import os
from pathlib import Path


# --------------------------------------------------------------------------- #
# 工具实现
# --------------------------------------------------------------------------- #

def get_weather(city: str) -> str:
    """获取城市天气"""
    db = {
        "北京": "晴，15-25°C",
        "上海": "多云，18-28°C",
        "东京": "小雨，12-20°C",
        "纽约": "阴，8-15°C",
    }
    return db.get(city, f"抱歉，暂不支持查询 {city} 的天气")


def read_file_summary(path: str) -> str:
    """读取文件摘要"""
    # 安全限制：只允许读取 /tmp 或当前目录下的文件
    allowed_dirs = [Path("/tmp"), Path.cwd()]

    try:
        file_path = Path(path).resolve()
        if not any(file_path.is_relative_to(d) for d in allowed_dirs):
            return f"Error: 路径不在允许范围内: {path}"

        if not file_path.exists():
            return f"Error: 文件不存在: {path}"

        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        summary = f"文件: {path}\n行数: {len(lines)}\n前 3 行:\n"
        summary += "\n".join(lines[:3])
        if len(lines) > 3:
            summary += f"\n... (共 {len(lines)} 行)"
        return summary
    except Exception as e:
        return f"Error: {e}"


def get_system_info() -> str:
    """获取系统信息"""
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "cwd": os.getcwd(),
    }
    return json.dumps(info, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# 工具 Schema
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "name": "get_weather",
        "description": "查询指定城市的天气",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称（中文或英文）"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "read_file_summary",
        "description": "读取文件摘要（前几行）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "get_system_info",
        "description": "获取当前系统信息",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


# --------------------------------------------------------------------------- #
# 请求处理
# --------------------------------------------------------------------------- #

def handle_initialize(params: dict) -> dict:
    """处理 initialize"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "demo-mcp-server", "version": "1.0.0"}
    }


def handle_tools_list(params: dict) -> dict:
    """处理 tools/list"""
    return {"tools": TOOLS}


def handle_tools_call(params: dict) -> dict:
    """处理 tools/call"""
    name = params.get("name", "")
    arguments = params.get("arguments", {})

    print(f"[Server] tools/call: {name}({arguments})", file=sys.stderr)

    if name == "get_weather":
        city = arguments.get("city", "")
        result = get_weather(city)
    elif name == "read_file_summary":
        path = arguments.get("path", "")
        result = read_file_summary(path)
    elif name == "get_system_info":
        result = get_system_info()
    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

    return {"content": [{"type": "text", "text": result}]}


def handle_request(request: dict) -> dict:
    """分发请求到对应处理函数"""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    handlers = {
        "initialize": handle_initialize,
        "tools/list": handle_tools_list,
        "tools/call": handle_tools_call,
    }

    handler = handlers.get(method)
    if not handler:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

    try:
        result = handler(params)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(exc)}}


# --------------------------------------------------------------------------- #
# Server 主循环
# --------------------------------------------------------------------------- #

def main():
    print("[Server] MCP Server 启动（stdio 模式）", file=sys.stderr)
    print("[Server] 按 Ctrl+C 退出", file=sys.stderr)

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Server] 无效 JSON: {line[:50]}...", file=sys.stderr)
                continue

            response = handle_request(request)
            resp_line = json.dumps(response, ensure_ascii=False)
            print(resp_line, flush=True)

    except KeyboardInterrupt:
        print("\n[Server] 退出", file=sys.stderr)
    except Exception as e:
        print(f"[Server] 错误: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()