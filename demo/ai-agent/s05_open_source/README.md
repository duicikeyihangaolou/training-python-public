# s05: 开源 Agent 框架

> 对应讲义：[we-know-ai-agent.md](../../doc/we-know-ai-agent.md#5-开源-agent-框架选讲)

本节介绍三个主流开源 Agent 框架的安装和使用。

## 框架介绍

| 框架               | 开发者           | Stars      | 特点                              |
| ---------------- | ------------- | ---------- | ------------------------------- |
| **Hermes Agent** | Nous Research | 140k+      | GEPA 自优化、6 大消息平台、MIT 许可证        |
| **OpenHuman**    | tinyhumans    | 10k+（快速增长） | Rust+Tauri、Memory Tree、118+ 数据源 |
| **OpenClaw**     | 原 Clawdbot    | 370k+      | 50+ 平台集成，但有安全事件（慎用）             |

## Hermes Agent（推荐）

### 安装

```bash
# 克隆仓库
git clone https://github.com/nousresearch/hermes-agent.git
cd hermes-agent

# 安装依赖
pip install -r requirements.txt

# 配置 API Key
export OPENAI_API_KEY=sk-...
# 或使用其他支持的模型

# 运行
python -m hermes_agent.cli
```

### 特点

- **GEPA 自优化循环**：自动学习和优化技能
- **多级记忆**：session / persistent / skill 三层记忆
- **6 大消息平台**：Telegram / Discord / Slack / WhatsApp / Signal / CLI
- 模型无关，支持 OpenAI / Anthropic / 本地模型

### 快速开始

```bash
# 与 Hermes 对话
hermes chat "北京天气怎么样？"

# 查看可用技能
hermes skills list

# 导入 OpenClaw 工作流
hermes claw migrate /path/to/openclaw/workflows
```

---

## OpenHuman

### 安装

```bash
# 克隆仓库
git clone https://github.com/tinyhumansai/openhuman.git
cd openhuman

# Rust 构建（需要 Rust 1.70+）
cargo build --release

# 或使用预编译二进制
# 下载地址：https://github.com/tinyhumansai/openhuman/releases

# 运行
./target/release/openhuman
```

### 特点

- **Rust + Tauri**：桌面优先，性能高
- **Memory Tree**：本地 SQLite，整合 118+ 数据源
- **TokenJuice**：智能 token 压缩，成本低
- **Ollama 支持**：可选本地 AI，隐私优先
- 内置工具：网页搜索/爬虫、文件系统、Git、浏览器控制

### 快速开始

```bash
# 启动 OpenHuman
openhuman

# 在桌面 UI 中与 Agent 对话
# Agent 会记住上下文（跨 weeks）

# 查看 Memory Tree
openhuman memory tree

# 连接数据源
openhuman connect gmail
openhuman connect slack
```

---

## OpenClaw（谨慎使用）

### 安装

```bash
git clone https://github.com/openclawai/openclaw.git
cd openclaw
pip install -r requirements.txt
```

### 注意

> ⚠️ 2026 年 3 月发生安全事件：4 天内发现 9 个 CVE，341 个恶意技能。建议仅用于学习，**不要在生产环境使用**。

### 替代方案

如果需要类似 OpenClaw 的多平台集成能力，推荐使用 **Hermes Agent**（支持 `hermes claw migrate` 导入 OpenClaw 工作流）。

---

## 对比总结

| 需求         | 推荐框架                             |
| ---------- | -------------------------------- |
| 快速落地、多平台消息 | **Hermes Agent**                 |
| 桌面优先、本地隐私  | **OpenHuman**                    |
| 学习研究（仅限）   | OpenClaw（仅学习，勿生产）                |
| 自托管、多数据源整合 | **Hermes Agent** 或 **OpenHuman** |

---

## 运行测试

本目录不包含这些框架的源代码（外部项目），仅提供安装说明。

如需验证，可以：

```bash
# 测试 Hermes Agent（如果已安装）
hermes chat "你好"

# 测试 OpenHuman（如果已安装）
openhuman chat "你好"
```
