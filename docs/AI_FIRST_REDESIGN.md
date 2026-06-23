# VP-Codex-Web — AI-First 用户流程重构方案

> 版本：v1.0 | 日期：2026-06-22 | 状态：待实现

---

## 一、核心思路

**从"工具型旅游网站" → "AI Agent 优先的旅行规划助手"**

传统旅游网站的结构：首页 → 搜索/浏览 → 详情 → 规划

VisePanda 的结构应该是：**AI Agent 对话 → 按需使用工具**

用户打开网站第一眼看到的不应该是 Dashboard/英雄图/功能入口，而是一个 **准备好了的 AI 旅行顾问聊天框**。

---

## 二、具体改动

### 2.1 默认视图改为 Chat（P0）

| 当前 | 改为 |
|------|------|
| `boot()` 设置 `data-view = "dashboard"` | `boot()` 设置 `data-view = "chat"` |
| 导航栏高亮 Plan tab | 导航栏高亮 Ask tab（聊天图标） |
| 用户需要点 Ask 才能聊天 | **打开即聊，零点击进入对话** |

### 2.2 Chat 作为首页主体（P0）

当前 Chat 面板是一个 `section.workspace`，和 Cities/Tools/Trips 平级。改为：

- **Chat 面板不再是普通的 tab panel**
- 应该作为 `<main>` 的默认/唯一内容，全屏展示
- 背景：保持深色中国风（对接 DESIGN.md），聊天框居中占主要区域
- Hero 区域（great-wall 背景图 + "Plan with context"）可以保留，但移到 Chat 之后作为**次要内容**或整合进 Chat 面板的背景装饰

### 2.3 聊天配置选项「渐进式」展示（P1）

当前 Chat 面板布局（按顺序）：
1. Chat toolbar（mode/provider/depth 三个下拉框）
2. Chat prompts（预设问题 8 个按钮）
3. Chat status
4. Chat log（对话区域）
5. Chat input

改为 **AI-First 渐进式：**

**阶段 1：初次加载（空对话）**
```
┌──────────────────────────────────┐
│   🐼 VisePanda                   │
│   AI China Travel Agent          │
│                                  │
│   [Welcome message - already has]│
│   "Tell me your nationality..."  │
│                                  │
│   [Quick prompt chips]           │
│   First trip | Food route | ...  │
│                                  │
│   ┌──────────────────────────┐   │
│   │ Ask anything...          │   │
│   └──────────────────────────┘   │
│   [Send]                         │
└──────────────────────────────────┘
```
- 只有：欢迎语 + 快速提示按钮 + 输入框
- 不展示 toolbar、不展示 preset groups

**阶段 2：用户发送第一条消息后**
```
┌──────────────────────────────────┐
│   🐼 VisePanda                   │
│                                  │
│   Mode: [Itinerary ▼]           │ ← 出现
│   Route: [Auto ▼]     Depth: [▼]│ ← 出现
│                                  │
│   [Chat history...]              │
│   [Messages streaming...]        │
│                                  │
│   ┌──────────────────────────┐   │
│   │ Ask a follow-up...       │   │
│   └──────────────────────────┘   │
│   [Send]                         │
└──────────────────────────────────┘
```
- Chat toolbar 渐入显示
- 预设问题 buttons 移到 toolbar 下方或保持隐藏（由 toolbar 的 mode 切换控制）

### 2.4 首页/Dashboard 重新设计（P1）

当前 Dashboard 有两个 panel：
- `hero` — 英雄区（标题 + 描述 + 快速规划 + home-snapshot + 大图）
- `dashboard` — "Start here" + 城市/工具/路线入口

改为：

**方案 A：Chat 就是首页（推荐）**
- 移除 hero section 作为独立 panel
- 将 hero 的 branding 元素融入 Chat panel 头部：
  - "China travel planning for international visitors" 作为 subtitle
  - AI Agent 头像/熊猫标志作为聊天伙伴头像
  - Great-wall 图片作为聊天背景水印或对话区域背景
- "Start here" 区域的三个入口（Route/Entry/Local）改为聊天预设按钮
- Quick planner 表单（destination + length）合并到聊天输入框旁边的快捷选项

**方案 B：Hero 简化为 Chat 的附属**
- Hero 区域压缩为窄条，位于 Chat 上方
- 只保留标题 + 一句 tagline
- 其余全部砍掉

### 2.5 导航栏调整

当前 5 个 tab：Plan | Ask | Cities | Tools | Trips

改为（方案）：
- `Ask` — 默认选中，代表 AI Agent（可改成 `AI Guide` 或保持 `Ask` 带熊猫图标）
- `Cities` — 城市探索
- `Tools` — 旅行工具
- `Trips` — 已存行程

说明：Plan（Index/Dashboard）不再需要独立 tab，因为 Chat 已经是首页。

---

## 三、UI/UX 细节

### 3.1 空状态设计
- **未登录 + 空对话：** 展示欢迎语 + 品牌标识 + AI 头像 + 4 个快速触发按钮
- **已登录 + 有空对话：** 恢复上次对话（存 localStorage），滚动到最后一条
- **已登录 + 无对话：** 同上初次加载状态

### 3.2 Chat 配置的渐进式展示逻辑
```javascript
// 伪代码
let hasStarted = false;

function sendFirstMessage() {
  hasStarted = true;
  // 显示 toolbar（带动画 fadeIn）
  document.querySelector('.chat-toolbar').classList.remove('is-hidden');
  document.querySelector('.chat-toolbar').classList.add('fade-in');
  // 隐藏初始引导区域
  document.querySelector('.chat-welcome').classList.add('is-hidden');
}
```

### 3.3 快速触发按钮
当前 hero 区域的 3 个 prompt-rail 按钮 + 8 个 chat-prompts 按钮 + 3 个 home-snapshot 卡片。

合并为统一的 4-6 个高价值快速触发按钮，放在 Chat 输入框上方：
1. 🇨🇳 First trip planner（首次来访路线规划）
2. 🍜 Food & culture（美食文化推荐）
3. 🛂 Entry ready（入境准备清单）
4. 💰 Budget model（预算模型）
5. 🚄 Rail vs flight（交通对比）
6. 🎯 Compare cities（城市对比）

### 3.4 加载状态
- 首次打开 Chat 时，不要等所有 API 加载完再显示
- 立即渲染 Chat 界面骨架（输入框 + 欢迎语）
- `loadChatOptions()`、`loadCities()`、`restoreSession()` 在后台并行加载

---

## 四、涉及的文件

| 文件 | 改动 |
|------|------|
| `web/app.js` | `boot()` 默认 view → chat；渐进式 toolbar 逻辑；导航 tab 更新 |
| `web/index.html` | Chat panel 提升为主内容；Hero 区域整合/简化；Chat 配置结构改为折叠 |
| `web/app.css` | Chat 全屏布局；渐入动画；聊天作为首页的新样式 |

---

## 五、不动的内容

- Cities / Tools / Trips 三个 tab 的功能逻辑完全不变
- API 端点和数据流不变
- Auth 系统不变
- PWA / Service Worker 不变

---

## 六、效果预期

| 指标 | 当前 | 改后 |
|------|------|------|
| 用户首次接触的功能 | Dashboard 信息流 | **AI Agent 对话** |
| 从打开到提问的步骤 | 2 步（点 Ask + 打字） | **1 步（直接打字）** |
| 与传统旅游网站差异度 | 中等（有 AI 但藏在 tab 里） | **极高（AI 就是首页）** |
| 配置选项复杂度感知 | 高（8 个按钮 + 3 个下拉框） | **低（起始干净，逐步展开）** |
| 品牌识别度 | 浅色 Generic 风格 | 熊猫中国风 + AI Agent 角色感 |
