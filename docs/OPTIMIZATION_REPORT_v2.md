# VP-Codex-Web 优化报告 v2.0 — AI-First 版响应式审查

> 审查对象：v6.1.0 AI-First 改版
> 审查重点：手机竖屏 / 电脑横屏适配、新增功能 Bug
> 日期：2026-06-23

---

## 一、AI-First 迁移带来的新 Bug

### 🔴 1. Trips 空状态仍引用了 Dashboard（已移除）
**文件：** `web/app.js` 第 360 行
```javascript
emptyState("No trips yet", "...", "Use planner", () => setView("dashboard"))
```
❌ 如果 v6.1.0 移除了 Dashboard tab，点击这个按钮会跳转到不存在的 view
**修复：** 改为 `setView("chat")` 或移除该 emptyState

### 🟡 2. Dashboard view 残留引用
**文件：** 搜索 `data-view="dashboard"` 确认是否全部清理
- Trips 空状态（如上）
- Navigation 中如果 Dashboard tab 已移除，所有引用需清理

### 🟡 3. Quick Planner 表单——是否已合并到 Chat？
v6.1.0 将 quickPlanner 合并进 Chat。需确认：
- Hero 区域的 `#quickPlanner` 表单是否已正确迁移到 Chat 面板
- 如果 Hero 区域被精简，表单的提交事件绑定 `$("#quickPlanner").addEventListener(...)` 不会报错（因为 `$` 会返回 null 但不报错）

---

## 二、手机竖屏适配问题（<560px /  portrait）

### 📱 M1. Chat 输入框在键盘弹出后被遮挡
**文件：** `web/app.css` 第 1173-1194 行（560px 断点）
```css
.chat-shell {
  min-height: calc(100dvh - 156px);
}
.chat-form {
  position: sticky;
  bottom: calc(90px + env(safe-area-inset-bottom));
}
```
**问题：** 竖屏手机上键盘弹出时 `100dvh` 会变化（现代浏览器已支持 `dvh`），但 sticky bottom 的偏移量（90px）是硬编码的，没有考虑键盘高度。用户打字时输入框可能被键盘遮住。
**修复：** 
- 使用 `100dvh` ✓（已用）
- 使用 `VisualViewport API` 监听键盘弹出，JS 动态调整 `.chat-form` 的 bottom 值
- 或使用 `inputMode` 优化，避免全屏键盘

### 📱 M2. Chat 首屏——6 个快捷按钮在窄屏上超宽
**文件：** `web/app.css` 第 1037-1059 行
**问题：** 6 个 pill 按钮在 320px 宽的屏幕上横向滚动，每个按钮文本可能被截断。当前代码 `white-space: nowrap` + `overflow-x: auto` 可以滚动但用户体验差。
**优化方案：**
- 3×2 网格布局（两行三列）替代单行横向滚动
- 或使用更短的按钮文案（如 `🇨🇳 First trip` → `First trip`）

### 📱 M3. Chat toolbar 在手机上堆叠占满屏幕
**文件：** `web/app.css` 第 1061-1065 行
```css
@media (max-width: 560px) {
  .chat-toolbar {
    grid-template-columns: 1fr;  /* 三个下拉框竖排 */
    gap: 10px;
    padding: 12px;
  }
}
```
**问题：** mode/provider/depth 三个下拉框在手机上竖排，加上 padding 占约 160px 高度。对于首次弹出的渐进式展示，会挤占对话空间。
**优化方案：**
- 折叠式：默认只显示 Mode 下拉，Provider 和 Depth 通过 "⚙️ More" 按钮展开
- 或改为横向滚动标签样式 `<Mode> <Provider> <Depth>` 排成一行

### 📱 M4. 底部导航——4 tab vs 5 tab 布局
**文件：** `web/app.css` 第 952-953 行
```css
grid-template-columns: repeat(5, minmax(0, 1fr));  /* 5 列 */
```
**问题：** AI-first 改为 4 个 tab（Ask/Cities/Tools/Trips），需改为 `repeat(4, minmax(0, 1fr))`。否则多出一列空白。
**注意：** 4 个 tab 每个占 25%，比 5 个 tab 每个 20% 更宽，按钮文案可略长。

### 📱 M5. 竖屏键盘弹出后底部导航被顶起
**问题：** 底部 nav 使用 `bottom: calc(8px + env(safe-area-inset-bottom))` 固定。键盘弹出时 nav 会被顶到键盘上方（iOS Safari 行为），遮挡 Chat 输入框。
**优化方案：** 
- Chat view 时隐藏底部 nav（键盘弹出时更简洁）
- 或 Chat view 时 nav 改为透明/极简模式

### 📱 M6. Scroll 到顶部时 Tab 视觉不同步
**文件：** `web/app.js` 第 95-115 行 `setView()`
**问题：** 目前 `setView()` 只切换 `is-hidden` 类。在手机上，不同 tab 的内容高度差异大，切换后 scroll 位置可能保留在之前 tab 的滚动位置。
**优化方案：** `setView()` 时添加 `window.scrollTo({ top: 0, behavior: 'smooth' })`

---

## 三、电脑横屏适配问题（>1024px / landscape）

### 🖥️ D1. Chat 在宽屏上内容太窄
**文件：** `web/app.css` 第 730 行
```css
max-width: min(760px, 92%);
```
**问题：** 27 寸显示器（2560px）上 Chat 只占中间 760px，两侧大量空白。浪费横屏优势。
**优化方案：**
- 宽屏（>1400px）时 Chat max-width 提升到 960px
- 或聊天消息采用两栏布局（城市信息在侧边展示）
- 或左侧加城市选择侧栏（类似 Slack 频道列表）

### 🖥️ D2. 横屏下 Chat 高度不足
**文件：** `web/app.css` 第 671 行
```css
.chat-shell {
  min-height: 560px;
}
.chat-log {
  max-height: 58vh;
}
```
**问题：** 横屏时 58vh 约等于 580px（1080p 显示器），但底部还有 toolbar + form 等固定元素，对话可见区域反而更少。
**优化方案：**
- 横屏时 `max-height: calc(100vh - 320px)` 让对话区域充分利用垂直空间
- 或聊天消息区域使用 `flex: 1` 自适应填充

### 🖥️ D3. 城市卡片网格——宽屏只显示 4 列
**文件：** 搜索 `city-grid`
**问题：** 城市卡片网格当前最大 4 列。27 寸显示器上每张卡片被拉得很宽，信息密度低。
**优化方案：**
- 宽屏（>1400px）改为 5-6 列
- 或使用 `auto-fill, minmax(220px, 1fr)` 自适应

### 🖥️ D4. Topbar + Nav 在横屏上占用过多垂直空间
**现状：** Topbar 68px + Nav 58px = 126px 固定顶部。横屏（1080p）上占 12% 的垂直空间。
**问题：** 不是大问题，但 Chat 视图可以考虑在滚动时自动隐藏 topbar（`position: sticky` + 滚动检测）

### 🖥️ D5. 横屏 Hero 图片高度过大
**文件：** `web/app.css` 第 206 行
```css
min-height: 430px;
```
**问题：** Hero section 在横屏上高度 680px（含图片 430px），用户需要滚动才能看到下方内容。横屏本应信息密度更高。
**优化方案：** 横屏+Chat 作为首页后，Hero 已不是重点，大幅压缩或移除。

### 🖥️ D6. Auth dialog 弹出位置
**文件：** `web/app.css` 第 1244-1253 行
```css
.auth-dialog {
  position: fixed;
  inset: auto 8px calc(8px + env(safe-area-inset-bottom)) 8px;  /* 底部弹出 */
}
```
**问题：** 手机端底部弹出合理，但**桌面横屏**上 auth dialog 也从底部弹出，看起来很奇怪。
**优化方案：** 桌面端（>768px）使用 `position: relative` + 居中 modal（`top: 50%; left: 50%; transform: translate(-50%, -50%)`）

---

## 四、通用优化

### 🌐 G1. 桌面 Nav 改为 Sticky 无滚动
**问题：** 当前 Nav 在 920px 断点以下加了 `overflow-x: auto`。但在某些宽屏浏览器窗口宽度介于 920-1024px 时，Nav 不需要滚动却依然可以滚动，造成误触。
**修复：** Nav 滚动仅在小屏（<768px）启用

### 🌐 G2. 流式对话时禁止输入框编辑
**问题：** 上一轮已报。`withButtonBusy` 只禁用了发送按钮，`#chatInput` 仍可编辑。大屏用户会用快捷键粘贴新内容造成混乱。

### 🌐 G3. 统一使用 dvh 而非 vh
**检查：** `app.css` 第 60 行 `body { min-height: 100vh }`
**修复：** 改为 `100dvh`，避免手机浏览器地址栏伸缩导致的布局跳动

### 🌐 G4. 跨设备 Tab 状态保持
**问题：** 从手机 Ask tab 切换到 Cities，再旋转到横屏，view 状态保持正确。但手动 resize 窗口时，底部 nav 和顶部 nav 的切换不同步（底部 nav 在小屏显示，大屏隐藏）。
**优化方案：** 添加 `matchMedia` 监听，窗口尺寸跨断点时自动切换 nav 模式

---

## 五、修复 Bug 回归验证

确认 v6.1.0 中已修复的 Bug：

| 原问题 | 状态 | 验证方式 |
|--------|------|----------|
| SSE JSON 解析无 try/catch | 需验证 | 检查 `app.js` 是否有 `try{JSON.parse}` |
| Quick Planner `values.length` | 需验证 | 如果 quickPlanner 已合并到 Chat，此路由已不存在 |
| `api()` 无超时 | 需验证 | 检查是否有 `AbortController` |
| `sendChat()` raw fetch | 需验证 | 检查是否统一使用 `api()` |
| 空 catch 静默吞错误 | 需验证 | `loadAuthConfig()`, `restoreSession()` 是否加了反馈 |
| 城市图片 fallback | 需验证 | 检查 `image.onerror` 回调 |

---

## 六、优化优先级

| 优先级 | 编号 | 内容 | 预估工时 |
|--------|------|------|----------|
| 🔴 P0 | M1 | Chat 输入框键盘遮挡 | 1h |
| 🔴 P0 | Bug1 | Trips 空状态引用已删除的 Dashboard | 0.2h |
| 🔴 P0 | G3 | 统一 `100vh` → `100dvh` | 0.3h |
| 🟡 P1 | M3 | Chat toolbar 手机堆叠优化 | 1h |
| 🟡 P1 | D1 | Chat 宽屏 max-width 提升 | 0.5h |
| 🟡 P1 | D6 | Auth dialog 桌面居中 | 0.5h |
| 🟡 P1 | M4 | 底部导航 5 列改 4 列 | 0.3h |
| 🔵 P2 | M2 | 快捷按钮窄屏 3×2 网格 | 0.5h |
| 🔵 P2 | D3 | 城市卡片宽屏 5-6 列 | 0.3h |
| 🔵 P2 | D2 | 横屏 Chat 高度优化 | 0.5h |
| 🔵 P2 | G2 | 流式对话禁止输入编辑 | 0.3h |
| 🔵 P2 | M5 | 键盘弹出时隐藏底部 nav | 0.5h |
| 🔵 P2 | M6 | Tab 切换 scroll to top | 0.2h |
| ⚪ P3 | D4/D5/G1/G4 | 其他优化 | 1h |

**总计：** ~7 小时
