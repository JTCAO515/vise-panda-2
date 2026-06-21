# VisePanda Agent Transfer Index 设计

## 概述

当前仓库已经拥有一整套面向接手者的文档包，包括：

- `HANDOFF.md`
- `docs/2026-06-20-engineering-handoff-notes.md`
- `docs/2026-06-20-first-week-takeover-checklist.md`
- `docs/2026-06-20-high-risk-files-guide.md`
- `docs/2026-06-20-production-regression-manual.md`
- `docs/2026-06-20-next-2-4-weeks-priority-guide.md`
- `docs/2026-06-20-technical-debt-boundaries.md`
- `docs/2026-06-20-module-ownership-guide.md`
- `docs/2026-06-20-commercial-upgrade-plan.md`

同时，仓库里还存在：

- `README.md`
- `CHANGELOG.md`
- 多份 `spec / plan`
- `adr/`
- `agents/`
- 旧的 roadmap 与 iteration 文档

这些文档单独看都各有价值，但对于下一个 coding agent 来说，入口仍然分散。  
因此还需要最后补一层真正的“总目录页”，帮助接手者区分：

1. 哪些文档是当前主用交接包
2. 哪些文档是历史材料或参考材料
3. 不同场景下应该先读哪几份

## 目标

本轮完成后，仓库中需要有一份明确的总入口文档，做到：

1. 下一个 coding agent 一打开就能看懂整套交接文档的层级结构
2. 主用交接包和历史文档清晰分层
3. 不同使用场景下有推荐阅读路径
4. `HANDOFF.md` 和 `README.md` 都能链接到这份总目录页

## 非目标

本轮不做以下事情：

- 不新增新的交接附录类型
- 不修改产品代码
- 不修改测试
- 不重写现有交接包主体内容
- 不重新整理所有旧文档

本轮只做：

- 新增一个总目录页
- 把它接入现有入口文档

## 方案选择

### 方案 A：只做交接包总目录

只收录当前主用文档，例如：

- `HANDOFF.md`
- 工程附录
- 首周清单
- 风险指南
- 回归手册
- 商用升级路线

优点：

- 最干净
- 最适合快速接手

缺点：

- 无法体现仓库里已有的历史文档价值
- 后续接手者可能仍然要自己去找旧材料

### 方案 B：做仓库文档总目录

把 `docs/` 下重要文档都列进来。

优点：

- 最全

缺点：

- 容易让接手者分不清主次
- 第一眼信息噪声过大

### 方案 C：双层目录

本轮采用方案 C。

文档分成两层：

1. 当前主用交接包
2. 历史文档与参考材料

并在每一层中写清楚：

- 文档解决什么问题
- 什么时候该看它
- 它和其他文档的关系是什么

## 设计方案

新增文件：

`docs/2026-06-20-agent-transfer-index.md`

## 文档结构

### 1. 文档目的

解释为什么这份总目录页存在，以及它是写给“下一个 coding agent”用的，而不是简单的链接集合。

### 2. 怎么使用这份目录

说明推荐的使用方式，例如：

- 第一次接手时先看什么
- 准备改代码前看什么
- 准备上线前看什么
- 准备做中期规划时看什么

### 3. 第一层：当前主用交接包

这一层只放当前最应该先看的文档，至少包括：

- `HANDOFF.md`
- `docs/2026-06-20-engineering-handoff-notes.md`
- `docs/2026-06-20-first-week-takeover-checklist.md`
- `docs/2026-06-20-high-risk-files-guide.md`
- `docs/2026-06-20-production-regression-manual.md`
- `docs/2026-06-20-next-2-4-weeks-priority-guide.md`
- `docs/2026-06-20-technical-debt-boundaries.md`
- `docs/2026-06-20-module-ownership-guide.md`
- `docs/2026-06-20-commercial-upgrade-plan.md`

每条至少要说明：

1. 它解决什么问题
2. 什么时候优先看它
3. 它与其他文档的关系

### 4. 第二层：历史文档与参考材料

这一层按类别组织，至少包括：

- `README.md`
- `CHANGELOG.md`
- `docs/superpowers/specs/*`
- `docs/superpowers/plans/*`
- `docs/adr/*`
- `docs/agents/*`
- 旧的 roadmap / iteration / review 文档

重点不是把它们逐一长篇解释，而是让读者知道：

- 这些文档还存在
- 它们适合什么时候查
- 它们不是当前第一优先级入口

### 5. 建议阅读路径

按场景给出阅读顺序，至少覆盖：

1. 第一次接手项目
2. 准备改代码前
3. 准备做线上回归前
4. 准备做 2-4 周规划时

## 与现有入口的联动

本轮需要同步更新：

- `HANDOFF.md`
- `README.md`

### `HANDOFF.md`

在“关键文档索引”中加入总目录页，并在“接手建议”中提示：

- 如果不知道该先看哪份文档，先看总目录页

### `README.md`

在 `Planning Docs` 中加入：

- `Agent Transfer Index`

## 预期改动文件

- Create: `docs/2026-06-20-agent-transfer-index.md`
- Modify: `HANDOFF.md`
- Modify: `README.md`

## 错误控制与边界

为了避免总目录页变成另一份重复的 `HANDOFF.md`，本轮遵循以下约束：

1. 不大段复述每份文档内容
2. 不把总目录页写成新的长篇项目总览
3. 强调“导航”和“分层”，而不是重复原文
4. 当前主用文档与历史参考文档必须清晰分层

## 验收标准

本轮通过的标准是：

1. 仓库中存在 `docs/2026-06-20-agent-transfer-index.md`
2. 文档中明确区分主用交接包与历史参考材料
3. 文档中存在按场景推荐的阅读路径
4. `HANDOFF.md` 中能找到总目录页入口
5. `README.md` 中也能找到总目录页入口

## 交付方式

这轮不涉及产品版本升级。  
只会：

- 新增总目录页
- 更新 `HANDOFF.md`
- 更新 `README.md`
- 提交并推送到 GitHub
