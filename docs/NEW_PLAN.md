# VP-Codex-Web AI-First Redesign — 实施计划

> 基于：AI_FIRST_REDESIGN.md | 目标版本：v6.1.0
> 优先级：P0=阻塞级 → P1=核心功能 → P2=体验优化

---

## 总览

### 目标
把 VisePanda 从"工具型旅游网站"改为"AI Agent 优先的旅行规划助手"——首页即 Chat，零点击开始对话，配置渐进式展开。

### 涉及文件
| 文件 | 改动类型 |
|------|----------|
| `web/app.js` | 核心逻辑改动 |
| `web/index.html` | 结构调整 |
| `web/app.css` | 布局/动画/风格 |
| `web/sw.js` | 缓存策略（可能不） |
| `CONTEXT.md` | 文档更新 |

### 分支策略
在 `main` 上直接迭代（当前项目无其他活跃分支），每次提交对应一个 Phase。

---

## Phase 1 — Chat 设为默认视图（P0）

**目标：** 用户打开网站第一眼看到的是 Chat 对话框。

### 1.1 修改 boot 默认视图
**文件：** `web/app.js` 第 608 行
```diff
- document.body.dataset.view = "dashboard";
+ document.body.dataset.view = "chat";
```

### 1.2 更新导航栏激活状态
**文件：** `web/app.js` — `setView()` 函数
- 确保 `nav__item[data-view="chat"]` 默认 `is-active`
- 移除 `tab-dashboard` 的默认激活

### 1.3 更新 `index.html` 初始标记
**文件：** `web/index.html` 第 22 行
```diff
- <button class="nav__item is-active" id="tab-dashboard" data-view="dashboard" ...>
+ <button class="nav__item" id="tab-dashboard" data-view="dashboard" ...>
- <button class="nav__item" id="tab-chat" data-view="chat" ...>
+ <button class="nav__item is-active" id="tab-chat" data-view="chat" ...>
```

### 验证门禁
- [ ] 打开站点，默认看到 Chat 面板，而非 Dashboard
- [ ] 导航栏 Ask tab 默认高亮
- [ ] Plan tab 可点击切换到 Dashboard（保持可用性）
- [ ] 所有其他 tab 功能正常

---

## Phase 2 — Chat 面板升级为首页主体（P0）

**目标：** Chat 不再是一个普通 tab panel，而是占据页面主体的全屏体验。

### 2.1 HTML 结构调整
**文件：** `web/index.html`

当前的 main 结构：
```
<main>
  <section.hero data-view-panel="dashboard">
  <section.dashboard data-view-panel="dashboard">
  <section.workspace.is-hidden#panel-chat data-view-panel="chat">
  <section.workspace.is-hidden#panel-cities data-view-panel="cities">
  <section.workspace.is-hidden#panel-tools data-view-panel="tools">
  <section.workspace.is-hidden#panel-trips data-view-panel="trips">
</main>
```

改为：
```
<main>
  <section#panel-chat data-view-panel="chat" class="chat-hero">
    <!-- AI Agent 全屏体验 -->
  </section>
  <section.workspace.is-hidden#panel-dashboard data-view-panel="dashboard">
    <!-- Dashboard 精简版，作为次要入口 -->
  </section>
  <section.workspace.is-hidden#panel-cities data-view-panel="cities">
  <section.workspace.is-hidden#panel-tools data-view-panel="tools">
  <section.workspace.is-hidden#panel-trips data-view-panel="trips">
</main>
```

具体改动：
1. `#panel-chat` 移除 `is-hidden`，添加 `chat-hero` CSS 类
2. Hero section 精简后合并到 `#panel-dashboard` 内（作为 Plan tab 的内容）
3. Dashboard section（`class="dashboard section"`）也收入 `#panel-dashboard` 内

### 2.2 Chat Hero CSS
**文件：** `web/app.css`（新增）

```css
.chat-hero {
  min-height: calc(100vh - 126px); /* 扣除 topbar + nav */
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 720px;
  margin: 0 auto;
  padding: clamp(24px, 5vw, 48px);
}

.chat-hero .chat-shell {
  /* 移除原来的 grid 5-row，改为 flex column */
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: unset;
}

.chat-hero .chat-log {
  max-height: 60vh;
  flex: 1;
}
```

### 2.3 品牌标识融入 Chat
- Chat 面板顶部添加：
  - AI Agent 头像（熊猫 logo，40x40px，圆形）
  - 问候语 "VisePanda · AI China Travel Agent"
  - 副标题 "Plan like you asked a local friend"

### 验证门禁
- [ ] Chat 面板全屏显示，居中布局
- [ ] 品牌标识清晰可见
- [ ] Dashboard 作为次要面板，点击 Plan tab 可访问
- [ ] 手机端布局正常

---

## Phase 3 — Chat 配置渐进式展示（P1）

**目标：** 空对话时只显示欢迎语+输入框+快速按钮；用户发消息后 toolbar 渐入。

### 3.1 HTML 结构调整
**文件：** `web/index.html`

当前 Chat 面板内结构：
```
.chat-shell
  .chat-toolbar — mode/provider/depth（始终显示）
  .chat-prompts — 8 个预设按钮（始终显示）
  .view-status#chatStatus
  .chat-log#chatLog
  .chat-form#chatForm
```

改为：
```
.chat-shell
  .chat-welcome（初始可见）
    — AI 品牌标识
    — 欢迎语消息
    — 4-6 个快速触发按钮 pill
  .chat-toolbar.is-hidden（初始隐藏，发消息后出现）
    — mode/provider/depth 下拉
  .chat-prompts.is-hidden（发消息后出现，或由 mode 切换触发）
    — 预设问题（可选）
  .view-status#chatStatus
  .chat-log#chatLog
  .chat-form#chatForm
```

### 3.2 JS 逻辑
**文件：** `web/app.js`

新增状态变量：
```javascript
const chatState = {
  hasStarted: false,  // 是否已经发送过至少一条消息
};
```

修改 `sendChat()` 函数（在第 311 行附近）：
```javascript
async function sendChat(message, overrides = {}) {
  // 首次发送：显示 toolbar 和 prompts
  if (!chatState.hasStarted && message.trim()) {
    chatState.hasStarted = true;
    document.querySelector('.chat-toolbar')?.classList.remove('is-hidden');
    document.querySelector('.chat-toolbar')?.classList.add('fade-in');
    document.querySelector('.chat-prompts')?.classList.remove('is-hidden');
    document.querySelector('.chat-prompts')?.classList.add('fade-in');
    document.querySelector('.chat-welcome')?.classList.add('is-hidden');
  }
  // ... 原有的 sendChat 逻辑
}
```

### 3.3 CSS 渐入动画
**文件：** `web/app.css`（新增）

```css
.fade-in {
  animation: fadeSlideIn 0.32s ease-out both;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-6) 0;
  text-align: center;
}
```

### 3.4 快速触发按钮（合并统一）
将 hero 的 prompt-rail 3 个按钮 + chat-prompts 8 个按钮 + home-snapshot 3 个卡片 → 合并为 6 个高价值快速触发 pill 按钮：

| 按钮 | 对应 prompt | 触发效果 |
|------|------------|----------|
| 🇨🇳 First trip | 首次 7 天路线 | 切到 itinerary mode，发送 prompt |
| 🍜 Food route | 美食城市对比 | 切到 food mode，发送 prompt |
| 🛂 Entry ready | 入境 checklist | 切到 entry mode，发送 prompt |
| 💰 Budget | 预算模型 | 切到 budget mode，发送 prompt |
| 🚄 Rail vs flight | 交通对比 | 切到 transit mode，发送 prompt |
| 🎯 Compare cities | 城市对比 | 切到 city-fit mode，发送 prompt |

### 验证门禁
- [ ] 空对话只看到欢迎语 + 快速按钮 + 输入框
- [ ] 首次发送消息后，toolbar 和 prompts 渐入出现
- [ ] 欢迎区域在 toolbar 出现后隐藏
- [ ] 快速按钮点击后自动发送预设消息
- [ ] 动画流畅，无闪烁/跳动

---

## Phase 4 — Dashboard 简化为次要面板（P1）

**目标：** Dashboard/Hero 不再是首页，而是 Plan tab 下的次要内容。

### 4.1 Hero 精简
**文件：** `web/index.html` 第 45-97 行

保留：
- 标题 "VisePanda"
- 一段话描述（压缩为一句 tagline）
- 3 个 home-snapshot 卡片（Entry/Route/Local）

移除：
- 大图（great-wall.jpg）
- prompt-rail 按钮（已移到 Chat）
- quickPlanner 表单（已移到 Chat）
- hero__media-note

### 4.2 Dashboard section 精简
**文件：** `web/index.html` 第 99-116 行

现有内容：
- "Start here" eyebrow
- 3 个卡片（Cities/Tools/Trips 入口）

保持不动，只是不再是首页。

### 4.3 导航栏文案可选调整
考虑将 "Plan" tab 改为 "Home" 或 "Overview"，避免与 Chat 的规划功能混淆。

### 验证门禁
- [ ] Plan tab 内容简洁，加载快速
- [ ] Chat 作为首页无干扰
- [ ] 从 Chat 切换到 Plan 再切回来，状态保持

---

## Phase 5 — 空状态与对话恢复（P2）

**目标：** 无对话时展示友好引导；有历史对话时恢复上下文。

### 5.1 空状态引导
欢迎语保留现有的：
```
"Tell me your nationality, travel month, total days, budget band, and what you care about most."
```
但在 UI 上展示为更美观的对话气泡样式（不是纯文本），配合 AI 头像。

### 5.2 对话存储与恢复（优化）
当前已在 `boot()` 中调用 `addMessage()` 添加欢迎语。

考虑添加 localStorage 存储：
- 存最后 1 条对话（非完整历史，避免存储膨胀）
- 刷新页面时恢复最后对话片段作为参考上下文

### 验证门禁
- [ ] 初次访问看到友好空状态
- [ ] 刷新后欢迎语仍在
- [ ] 不影响首次加载速度

---

## Phase 6 — 质量门禁（P2）

### 6.1 回归测试
- Cities 加载/搜索/过滤
- Tools 加载/详情/打开
- Trips 登录/未登录状态
- Auth 登录/注册/验证/登出
- Chat 流式对话/配置切换
- 所有 tab 切换

### 6.2 响应式检查
- 手机 ≤480px：Chat 输入框占满宽度，toolbar 折叠
- 平板 768px：同上优化
- 桌面 ≥1024px：Chat 居中 720px

### 6.3 性能检查
- 首次加载时间（注意 Google Fonts 阻塞问题）
- Chat 初始化不阻塞其他 API 加载
- 无控制台错误

---

## 执行路线图

| Phase | 内容 | 预估工时 | 依赖 |
|-------|------|----------|------|
| P1 | Chat 设为默认视图 | 0.5h | 无 |
| P2 | Chat 面板升级为首页主体 | 1.5h | P1 |
| P3 | 渐进式配置展示 | 2h | P2 |
| P4 | Dashboard 精简 | 1h | P2 |
| P5 | 空状态与对话恢复 | 0.5h | P3 |
| P6 | 质量门禁 | 1h | 全部 |

**总计预估：** 6.5 小时

---

## 风险与注意事项

| 风险 | 影响 | 缓解方案 |
|------|------|----------|
| 现有用户习惯 Dashboard 布局 | 适应成本 | 保留 Plan tab，不删除功能 |
| Chat 全屏后在手机上键盘弹出导致布局错乱 | 交互体验 | 使用 `dvh` 单位 + `inputmode` 优化 |
| 渐进式展示引入新状态，增加 debug 复杂度 | 维护成本 | chatState 集中管理，便于追踪 |
| 已有对话历史无法迁移 | 数据丢失 | 仅视觉改动，对话不持久化 |

---

*本计划基于 AI_FIRST_REDESIGN.md v1.0 制定*
*如有 Phase 优先级或实现细节需要调整，随时修改*
