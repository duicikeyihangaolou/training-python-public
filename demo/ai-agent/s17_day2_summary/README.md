# s17: Day 2 小结与扩展方向

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#17-day-2-小结与扩展方向)

本节总结 Day 2 的学习内容，并提供扩展方向。

## Day 2 总结

### MCP Server 架构

```
Server 生命周期：
  启动 → 运行（接收/分发）→ 关闭

JSON-RPC 路由：
  请求解析 → 路由表 → 处理函数 → 响应构造

工具注册：
  Schema（name/description/inputSchema）+ Handler（执行逻辑）
```

### 传输层

| 传输方式  | 适用场景     | 特点                  |
| --------- | ------------ | --------------------- |
| **stdio** | 本地父子进程 | 简单、低延迟          |
| **SSE**   | Web/远程     | HTTP 长连接、事件推送 |

### 完整闭环

```
Agent → MCP Client → stdio → MCP Server
                              ↓
                         tools/call
                              ↓
                         返回结果
                              ↓
Agent ← MCP Client ← JSON-RPC ←
```

## 扩展方向

### 1. 官方/社区 MCP Server

| Server       | 用途         |
| ------------ | ------------ |
| `filesystem` | 本地文件操作 |
| `git`        | Git 操作     |
| `database`   | 数据库查询   |
| `slack`      | Slack 集成   |
| `github`     | GitHub API   |

### 2. 生产环境考虑

- **认证**：API Key / OAuth
- **限流**：token / rpm 限制
- **多实例**：负载均衡部署
- **监控**：日志、指标、追踪

### 3. 与课程衔接

理解 LangChain/CrewAI 内部工具机制：

- LangChain 的 Tool = MCP 工具的 Schema
- CrewAI 的 Agent = MCP Client
- 理解底层后，使用框架更得心应手

### 4. 持续关注

- **Hermes Agent**：快速迭代，GEPA 自优化
- **OpenHuman**：Memory Tree，118+ 数据源
- **MCP 官方 SDK**：持续更新

## 下一步

1. 跑通 `s16_full_loop` 的完整闭环
2. 尝试用自己的工具替换示例工具
3. 研究官方 MCP Servers（filesystem / git）
4. 探索生产环境部署（认证、限流）

---

## 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [OpenHuman](https://github.com/tinyhumansai/openhuman)
