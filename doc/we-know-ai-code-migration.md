# AI 驱动大规模代码迁移：Bun 案例与「先事实、后计划」方法论

## 注意 ⚠️

- _斜体表示引用或延伸阅读_
- **未经允许，禁止转载**
- 本讲义为 [`we-know-ai-coding.md`](we-know-ai-coding.md) 姊妹篇，聚焦 **AI
  编排下的语言级/架构级代码迁移**
- 默认读者已了解 Agent、Harness、Spec Coding 等概念；原理见
  [`we-know-ai-harness.md`](we-know-ai-harness.md)

---

## 课程目录

| 章节                                                                   | 主题 |
| ---------------------------------------------------------------------- | ---- |
| [1. 事件概览：Bun 做了什么](#1-事件概览bun-做了什么)                   |      |
| [2. 核心概念：什么是「先事实、后计划」](#2-核心概念什么是先事实后计划) |      |
| [3. Bun 迁移方法论全拆解](#3-bun-迁移方法论全拆解)                     |      |
| [4. 验证体系：测试通过只是地板](#4-验证体系测试通过只是地板)           |      |
| [5. 七条可迁移教训](#5-七条可迁移教训)                                 |      |
| [6. AI 自动开发操作 Playbook](#6-ai-自动开发操作-playbook)             |      |
| [7. 模板与检查清单](#7-模板与检查清单)                                 |      |
| [8. 原始资料索引](#8-原始资料索引)                                     |      |

---

## 1. 事件概览：Bun 做了什么

[返回目录](#课程目录)

2026 年 5 月，JavaScript 运行时 **Bun** 完成了一次在软件工程史上极为罕见的大规模迁移：用 AI 将约
**53.5 万行 Zig** 机械移植到 **Rust**，在 **11
天**内合并进主分支（[PR #30412](https://github.com/oven-sh/bun/pull/30412)），全平台测试套件 **100%
通过**，且 **0 测试跳过或删除**。

| 指标     | 数据                                                |
| -------- | --------------------------------------------------- |
| 时间     | 2026-05-03 → 05-14（11 天）                         |
| 规模     | 1,448 个 `.zig` → `.rs`；+1M LOC；6,778 commits     |
| 并行度   | 峰值 64 个 Claude 同时运行（4 workflow × 16 agent） |
| 验证     | 三平台合计 ~370 万 `expect()` 断言                  |
| API 成本 | 约 $165,000（官方估算）                             |
| 人工等价 | 3 名全职工程师约 1 年                               |
| 代码作者 | 100% 由 AI 生成，Jarred Sumner 编排与验收           |

**动机**：Bun 与 JavaScriptCore 混用 GC 与手动内存管理，use-after-free、泄漏、重入类 bug 频发；Rust
的 borrow checker 与 `Drop` 可在编译期拦截大量此类问题。

**策略选择**：一次性 **Big Bang 机械移植**（行为等价优先，idiomatic Rust
后置），而非长期维护双语言共存。测试套件用 TypeScript 编写，与实现语言无关——这是迁移可行的关键前提。

**合并后**：11 轮安全审计、24/7 coverage-guided fuzzing；已知 19 个回归均已修复；v1.4.0 相对 v1.3.14
修复 128 个 bug，二进制体积约减 20%，HTTP 吞吐提升 2%–5%。

---

## 2. 核心概念：什么是「先事实、后计划」

[返回目录](#课程目录)

### 2.1 一句话定义

**先事实、后计划（Facts before Plans）**：在写迁移方案、架构文档或让 Agent
批量改代码之前，先从源码中提取 **经对抗审查验证的、不可变的事实表**；计划与执行只能 **引用**
这些事实，不能与之矛盾。

### 2.2 与传统做法的对比

| 维度         | 传统做法（Plan first） | Bun 做法（Facts first）                         |
| ------------ | ---------------------- | ----------------------------------------------- |
| 第一步       | 写架构方案 / 迁移计划  | 从源码提取事实表（ownership、layout、API 契约） |
| Agent 争论时 | 重新读源码、各说各话   | 查事实表 tiebreak（`file:line` 已验证）         |
| 计划文档     | 独立撰写，可能脱离现实 | 从事实表 **derive** 出来的派生物                |
| 可审计性     | 计划与代码易漂移       | 事实表 + 计划 + 代码三层可追溯                  |

### 2.3 Bun 的两份「事实文件」

**1. `LIFETIMES.tsv`（2,253 行）**

- 每个 struct field 的指针 **所有权类别** 预分类
- Agent 在 Zig→Rust 翻译时对 lifetime 有分歧 → 查表，不重读 50 万行源码辩论

**2. `PORTING.md`（576 行，Phase-A 迁移规范）**

- Zig 模式 → Rust 模式的 **机械映射规则**
- 禁止项（不用 tokio、不用 `std::fs` 等）、命名规则、例外（`deinit`→`Drop`）
- 每个 Agent 翻译单个文件前 **必须先读全文**

**3. verified-claims corpus（1,355 行，规划阶段）**

- 每条 claim 绑定 `file:line`，经 3-vote 对抗审查
- 用于 [`rust-rewrite-plan.md`](https://github.com/oven-sh/bun/blob/main/docs/rust-rewrite-plan.md)
  架构文档

### 2.4 类比：不同迁移类型的「事实表」

| 迁移类型                | 事实表应包含什么                                      |
| ----------------------- | ----------------------------------------------------- |
| 语言重写（Zig→Rust）    | 指针所有权、FFI 符号表、struct layout、`#[repr]` 约束 |
| 框架升级（Django 3→5）  | 每个 call site 的 API 契约、deprecated 映射、行为差异 |
| 架构重构（单体→微服务） | 依赖图、边界不变量、性能 baseline、数据一致性契约     |
| 新功能（Spec Coding）   | 每个接口的输入/输出/错误码、验收用例、非目标清单      |

### 2.5 为什么对 AI 自动开发尤其重要

LLM **擅长在已有约束下批量生成**，**不擅长在模糊目标下保持一致性**。没有事实表时：

- 并行 Agent 会对同一指针/lifetime/API 做出 **互相矛盾** 的实现
- Reviewer 无法高效 tiebreak，只能重新读源码（上下文窗口不够）
- 「计划文档」与代码快速漂移，合并后 bug 呈 **class 级爆发**

有了事实表后，Agent loop 变成：

```text
Implementer: 按 PORTING.md + LIFETIMES.tsv 翻译 file X
Reviewer A/B: 默认 confirmed=false，cite source:line + target:line 证明等价
Fixer: 仅修 reviewer 指出的、与事实表冲突之处
```

---

## 3. Bun 迁移方法论全拆解

[返回目录](#课程目录)

### 3.1 总体流程

```text
准备（Facts）          试跑（Pilot）           批量（Scale）           验收（Verify）
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ PORTING.md  │      │ 3 文件完整  │      │ Phase A     │      │ 全量测试    │
│ LIFETIMES   │ ──►  │ implement   │ ──►  │ 1448 文件   │ ──►  │ CI 全平台   │
│ 对抗审查    │      │ review loop │      │ Phase B     │      │ 安全审计    │
└─────────────┘      └─────────────┘      │ 修编译错误  │      │ fuzzing     │
                                          └─────────────┘      └─────────────┘
```

### 3.2 Phase A / Phase B 两阶段翻译

Bun 刻意把「逻辑正确」与「能编译」拆开，降低并行冲突：

| 阶段        | 目标                    | 是否要求编译 | 产出                          |
| ----------- | ----------------------- | ------------ | ----------------------------- |
| **Phase A** | 忠实还原 Zig 逻辑与结构 | 否           | 每个 `.zig` 旁生成 `.rs` 草稿 |
| **Phase B** | 按 crate 消除编译错误   | 是           | 可 `cargo check` 的 workspace |

**Phase A 硬规则（摘自 PORTING.md）：**

- `.rs` 与 `.zig` 同目录、同 basename
- 禁止发明 crate layout；跨模块类型用 `bun_<area>::Type`
- 结构对齐：同名函数、同字段顺序、同控制流
- 不确定处打 `// TODO(port):`，**禁止猜测**
- `unsafe` 块必须写 `// SAFETY: <why>`

### 3.3 Dynamic Workflow：可重复的 Agent Loop

Jarred Sumner 用 Claude Code 跑了约 **50 个 dynamic workflow**，每个 workflow 是同一模式的循环：

```javascript
// 伪代码 — 来自官方博客
while (task = todoList.pop()) {
  result = implementer(task)
  feedback = await Promise.all([reviewer1(result), reviewer2(result)])
  await fixer.apply(feedback, result)
}
```

**典型 workflow 清单：**

1. 生成 PORTING.md + LIFETIMES.tsv
2. 机械 port 全部 `.zig` → `.rs`
3. 按 crate 修编译错误（峰值 16,000 错误 ÷ 64 agent）
4. 修循环依赖（另开 workflow 分类 + 重构）
5. 让 `bun --version`、`bun test` 等 subcommand 跑通
6. 测试文件分片修复
7. CI 多平台 burndown（972 → 23 → 0 失败文件）
8. 减 `unsafe`、去重、Windows 清理

### 3.4 对抗性审查（Adversarial Review）

| 角色              | 职责               | 上下文                                |
| ----------------- | ------------------ | ------------------------------------- |
| **1 Implementer** | 写代码             | 独立                                  |
| **2+ Reviewer**   | 找 bug、证伪等价性 | **独立窗口**（不与 implementer 共享） |
| **1 Fixer**       | 应用 reviewer 反馈 | 独立                                  |

**关键 prompt 约束：**

> Default `confirmed=false` unless you verify against source `.zig` with `file:line` citations.

> If you need a paragraph-long comment to justify why the workaround is OK, the code is wrong — fix
> the code.

Implementer 想合并；Reviewer 想找问题——**角色分离** 模拟人类 code review 的独立性。

### 3.5 并行与隔离

| 机制                 | 做法                                 | 防什么              |
| -------------------- | ------------------------------------ | ------------------- |
| Git worktree         | 4 个独立 worktree，各 16 agent       | 互踩、merge 冲突    |
| 禁止 destructive git | 不准 `git stash`、`git reset --hard` | Agent 误删彼此工作  |
| 禁止 loop 内慢命令   | `cargo check` 仅轮首/轮末            | 磁盘 I/O 打满、互等 |
| Round cap            | 12 / 80 / 100 轮上限                 | 无限 loop           |
| IOU 机制             | 超时写 `todo!("blocked_on: X::Y")`   | 死任务阻塞队列      |
| 测试隔离             | `systemd-run` + cgroups              | 内存/进程耗尽       |

峰值吞吐：**~1,300 LOC/min**（每行经 2 reviewer + 1 fixer）。

### 3.6 编译错误即 Work Queue

Phase B 不把编译错误当「失败」，而当 **可并行消费的任务队列**：

```text
for each crate:
  1. cargo check → 按文件分组错误 → 写入 errors/<crate>.json
  2. N 个 agent 并行修各文件错误
  3. 2 reviewer 审查该 crate 变更
  4. 1 fixer 应用反馈
  5. 轮末统一 cargo check
```

**踩坑**：Agent 曾把「修编译错误」理解成 **stub 空函数**——加一条 reviewer 规则 + prompt 修改后消失。

---

## 4. 验证体系：测试通过只是地板

[返回目录](#课程目录)

Bun 的分层验证（第三方复盘强调：合并后仍有 36 个安全发现，说明 **L3 测试全绿 ≠ 可放心**）：

| 层级 | 手段                                | 捕获什么                  |
| ---- | ----------------------------------- | ------------------------- |
| L1   | `cargo check`                       | 类型 / 生命周期           |
| L2   | `cargo clippy`（45 条 deny lint）   | 非惯用法                  |
| L3   | 全量 TS 测试套件                    | 行为回归                  |
| L4   | LeakSanitizer                       | 内存泄漏                  |
| L5   | Miri                                | `unsafe` soundness        |
| L6   | `cargo geiger`                      | unsafe 分布审计           |
| L7   | 24/7 coverage-guided fuzzing        | parser 类 bug             |
| L8   | 148 个 `const _: () = assert!(...)` | 跨语言 struct layout 漂移 |
| L9   | Post-merge 11 轮安全审计            | 逃逸实例                  |

### 4.1 语义陷阱：语法相同、语义不同

合并后 19 个已知回归，多数是 **机械翻译时看不出的语义差**：

| 问题            | Zig                     | Rust                         | 后果               |
| --------------- | ----------------------- | ---------------------------- | ------------------ |
| assert 副作用   | `assert()` 始终执行参数 | `debug_assert!` Release 擦除 | HMR 热更新失效     |
| 奇数长度 slice  | 忽略尾部字节            | `bytemuck::cast_slice` panic | `Blob.text()` 崩溃 |
| bounds check    | ReleaseFast 无检查      | Release 保留                 | 模块解析上限骤降   |
| comptime 格式串 | 编译期处理 marker       | 运行时处理                   | 终端超链接乱码     |

**启示**：机械 port 必须有一份 **「语义差异对照表」** 作为事实表的一部分。

---

## 5. 七条可迁移教训

[返回目录](#课程目录)

_摘自
[Michael Lady 对 PR #30412 的逆向调查](https://gist.github.com/michaellady/7e63223d5d72d9ad18a03efa1f376aae)（经五轮对抗审查）_

### 5.1 Facts before plans

写计划前先写事实表。Agent mid-port 争论时，tiebreak 引用不可变事实，而非重读源码。

### 5.2 Default-deny on AI verification

Verifier prompt 默认 **「有问题」**，Agent 必须 cite `file:line` 证明正确。漏报成本 >> 误报成本。

### 5.3 Class fix + instance re-audit

发现 bug **class** 后：先修 codegen / lint rule / CI gate（系统性），再逐 site 重审。Bun 修了 23 个
`&mut self` 重入问题，22 处到位，**1 处逃逸**。

### 5.4 Agents find well, repair poorly

Agent 擅长 **发现** bug、 decent 于 **提议** fix；不擅长验证 fix 未引入相邻 class 的新 bug。**Fix
必须过独立 gate**（另一 Agent 或人）。

### 5.5 Bounded loops with explicit IOUs

每个 phase 有 round cap；超时写结构化 IOU；下游 phase 消费 IOU。禁止无限 Agent loop。

### 5.6 Cheap continuous gates compound

148 个 compile-time layout assert，每个 ~5 行，运行时零成本，阻止整类跨语言漂移。**能用一个 regex +
一行 CI 挡住的 bug class，值得铺 100 份。**

### 5.7 Preserve the orchestration

Bun squash merge 后，5,512 commits、32 分支、audit doc 全部消失——**方法论不可 peer review**。应保留
workflow JSON、audit log、事实表 archive。

### 5.8 Meta-lesson

> 方法论在 **class 级别** 有效，在 **instance 级别** 泄漏。

Fix 不是「少用人、多 AI」，而是 **class 级 rigor（AI 擅长）+ instance 级 re-audit gate（AI
不擅长）**。

---

## 6. AI 自动开发操作 Playbook

[返回目录](#课程目录)

以下六阶段可直接用于团队内部的 AI 驱动迁移项目。

### Phase 0：可行性评估（1–2 天）

```text
□ 是否有语言无关、高覆盖的测试套件？
□ 源/目标边界是否清晰（FFI seam、module 边界）？
□ 能否定义可观测的「行为等价」指标（非仅编译通过）？
□ 能否机械提取事实表（ownership、API contract、layout）？
```

**不可迁移信号**：测试与实现语言强耦合；无 integration test；边界模糊；需架构 redesign（Bun
明确不做）。

### Phase 1：Facts File（2–5 天）

1. 只读 Agent workflow 分析源码 → 输出 TSV/YAML 事实表
2. **2+ 对抗 Agent + 1 人类** 审查事实表
3. 从事实表 derive `MIGRATION.md` / `PORTING.md`
4. 人类负责人 sign-off 事实表（版本化进仓库）

### Phase 2：Pilot + Workflow 调优（2–3 天）

1. 选 3 个文件（简单 / 中等 / 复杂）
2. 跑完整 loop：implement → 2×review → fix → compile/test
3. 记录 false start，写入 `AGENTS.md` / `.cursor/rules`
4. 确认 round cap、IOU、git 约束、禁止 stub 等规则有效

### Phase 3：批量执行

```text
Phase A: 逻辑翻译（不要求编译）→ 铺开覆盖面
Phase B: 编译/测试修复 → 消费 error queue
```

- 按 **crate/module 分片**，非随机按文件
- 每 shard 独立 worktree/branch
- Orchestrator 分配任务、收集 IOU、合并

**人类角色**：监控 workflow、改 prompt、处理 blocked IOU——**不是手写代码**。

### Phase 4：分层验证 Pipeline

建议 hook 到 **每次 Agent 写文件之后**（Bun 主要事后 audit，可改进）：

```yaml
on_file_write:
  - compile_check          # 编译
  - lint -- -D warnings    # lint
  - test -p $module        # 单元测试
  - layout_assert.sh       # 跨语言 layout（若适用）
  - unsafe_audit           # unsafe 计数（若适用）
```

### Phase 5：Class fix + Instance re-audit

```text
1. 从 audit 抽象 bug CLASS
2. 修 CODEGEN / LINT RULE / CI GATE
3. 对同类所有 instance 重跑 grep + 对抗审查
4. Agent 提出的 fix → 独立 gate（implementer 不得自证）
```

### Phase 6：方法论 Preservation

- 保留 orchestration 分支 / `docs/migration/` archive
- 不 squash AI 编排 PR，或至少保留 audit trail
- 关闭项 strike-through，不删除

### 6.1 工具映射（Cursor / Claude Code / Codex CLI）

| Bun 做法            | 通用映射                                |
| ------------------- | --------------------------------------- |
| Dynamic Workflow    | Cursor Automations / 自定义 loop script |
| 64 并行 agent       | git worktree + Task / subagent 分片     |
| PORTING.md          | 项目根 `AGENTS.md` / `.cursor/rules`    |
| LIFETIMES.tsv       | 结构化 facts（TSV/YAML in repo）        |
| 对抗审查            | 独立 context 的 reviewer subagent       |
| 编译错误 work queue | 解析 compiler 输出 → 任务 JSON → 分配   |
| Round cap + IOU     | `max_iterations=N`；超时写 `BLOCKED.md` |
| PostToolUse 验证    | Cursor hooks / CI on push               |

### 6.2 成本与适用边界

| 场景                                | 是否适合 AI 大规模迁移                  |
| ----------------------------------- | --------------------------------------- |
| 语言 port、API rename、框架版本升级 | ✅ 机械性高                             |
| 有语言无关测试 + 清晰 mapping guide | ✅                                      |
| 架构 redesign、新算法               | ❌ Bun 明确不做                         |
| GC + 手动内存、crypto、并发语义     | ⚠️ 需额外语义差异表 + 更强验证           |
| 无测试或测试即 spec                 | ❌ 省下的写代码时间会在 post-merge 吐回 |

**粗算（参考 Bun）**：~50 万 LOC 语言迁移 ≈ $100K–200K API + 1 人 × 2–4 周 orchestration；人工等价
2–3 人 × 6–12 月。

---

## 7. 模板与检查清单

[返回目录](#课程目录)

### 7.1 事实表 Schema 示例（`facts/ownership.tsv`）

```tsv
file	line	struct	field	ownership_class	lifetime_notes	verified_by
src/http/client.zig	142	ClientConnection	socket_owned	UniqueOwned	closed in deinit or on error path	human+agent-v3
src/http/client.zig	143	ClientConnection	callback_ref	SharedRef	counted via refcnt; may outlive connect()	agent-v2
```

### 7.2 MIGRATION.md 最小骨架

```markdown
# <Project> 迁移规范

## 非目标

- （明确不做什么）

## 事实表引用

- facts/ownership.tsv
- facts/api-contracts.yaml
- facts/semantic-traps.md

## 映射规则

- （源模式 → 目标模式，带示例）

## 禁止项

- （Agent 不得使用的库 / 模式）

## Phase 定义

- Phase A: …（是否要求编译）
- Phase B: …

## Agent 约束

- 禁止 git stash / reset --hard
- 禁止 stub 空实现糊弄编译
- 默认 reviewer confirmed=false
- Round cap: N
```

### 7.3 迁移前检查清单

- [ ] 事实表已版本化，经对抗审查
- [ ] MIGRATION.md 从事实表 derive，非凭空撰写
- [ ] 3 文件 pilot 通过完整 implement→review→fix loop
- [ ] 测试套件与实现语言解耦，覆盖率可接受
- [ ] 并行分片策略与 worktree 方案确定
- [ ] Round cap + IOU + blocked 消费 phase 已定义
- [ ] 分层验证 hook 已接入（至少 L1–L3）
- [ ] Fix 与 Find 分离 gate 已定义
- [ ] Orchestration 保留策略（不 squash audit trail）

### 7.4 合并前检查清单

- [ ] 全量测试通过（含多平台 CI）
- [ ] 无测试 skip/delete（或每项有 documented 理由）
- [ ] Class 级 audit 已完成 + instance re-audit 已完成
- [ ] Agent 自动 fix 均经独立 gate
- [ ] 已知回归清单 + 修复状态
- [ ] `docs/migration/` audit archive 已保留

---

## 8. 原始资料索引

[返回目录](#课程目录)

| 类型            | 链接                                                                                                    | 说明                           |
| --------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------ |
| 官方博客        | [Rewriting Bun in Rust](https://bun.com/blog/bun-in-rust)                                               | Jarred Sumner 第一人称全流程   |
| 架构规划        | [rust-rewrite-plan.md](https://github.com/oven-sh/bun/blob/main/docs/rust-rewrite-plan.md)              | Strangler-fig、FFI、GC 模型    |
| 迁移规范        | [PORTING.md commit](https://github.com/oven-sh/bun/commit/46d3bc29f270fa881dd5730ef1549e88407701a5)     | Phase A/B 规则                 |
| PR              | [#30412](https://github.com/oven-sh/bun/pull/30412)                                                     | 合并本体                       |
| 七条教训        | [Broadly Applicable Lessons Gist](https://gist.github.com/michaellady/7e63223d5d72d9ad18a03efa1f376aae) | 第三方逆向调查                 |
| 深度调查        | [Investigation Gist](https://gist.github.com/michaellady/7d552137fb1e37ab9bf637e450016c25)              | 完整方法论审计                 |
| 技术评审        | [Fawad HS Blog](https://fawadhs.dev/blog/bun-rust-rewrite-technical-review)                             | 构建链与 post-merge            |
| Google 内部迁移 | [arXiv:2501.06972](https://arxiv.org/html/2501.06972v1)                                                 | seed location 扩展 + diff 生成 |
| 姊妹讲义        | [we-know-ai-coding.md](we-know-ai-coding.md)                                                            | AI 赋能软件开发总纲            |
| 姊妹讲义        | [we-know-ai-harness.md](we-know-ai-harness.md)                                                          | Harness 与 Agent 循环          |

---

## 一句话带走

**先事实、后计划** = 让 AI 在 **不可变、可 cite 的约束** 下批量干活；**计划**
是事实的派生物，**验证** 分多层且 test 全绿只是地板；**class 级 systemic fix** 之后必须 **instance
级 re-audit**——这是 Bun 百万行迁移最值得复制的工程纪律，而非「多开几个 Agent」本身。
