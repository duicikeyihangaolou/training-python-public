# s11: JSON-RPC 路由与分发

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#11-json-rpc-路由与分发)

本节演示 JSON-RPC 请求解析、路由表和响应构造。

## 核心概念

**JSON-RPC 请求解析**：

- 校验 `jsonrpc` 字段是否为 "2.0"
- 提取 `method` / `params` / `id`

**路由表**：

- `method` 字符串 → 处理函数
- 如 `initialize` → `handle_initialize`

**响应构造**：

- 成功：`{"jsonrpc": "2.0", "id": ..., "result": ...}`
- 失败：`{"jsonrpc": "2.0", "id": ..., "error": {"code": ..., "message": ...}}`

## 文件说明

| 文件                       | 说明     |
| ------------------------ | ------ |
| `jsonrpc_router.py`      | 完整路由实现 |
| `test_jsonrpc_router.py` | 单元测试   |

## 运行方式

```bash
cd s11_jsonrpc_routing
python jsonrpc_router.py
```
