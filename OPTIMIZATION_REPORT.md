# VP-Codex-Web 优化报告 v1.0

> 审查日期：2026-06-22
> 审查范围：UI/UX、前端代码、设计一致性
> 站点：https://codex.go2china.space
> 仓库：https://github.com/JTCAO515/VP-Codex-Web

---

## 🐛 一、Bug 清单（按严重程度排序）

### 🔴 P0 — 功能缺陷

#### 1. SSE 流式 JSON 解析无异常保护
**文件：** `web/app.js` 第 338 行
```javascript
const payload = JSON.parse(line.slice(5).trim());
```
**问题：** 没有 try/catch 包裹。如果服务端返回的 SSE `data:` 行包含非 JSON 内容（例如错误消息或代理中间件注入的 HTML），`JSON.parse` 会抛出异常，直接导致整个聊天会话崩溃。
**修复：** 使用 try/catch 包裹，解析失败时跳过该行或显示友好错误。

#### 2. Quick Planner 表单 `values.length` 为 undefined
**文件：** `web/app.js` 第 483 行
```javascript
sendChat(`Plan a ${values.length} China trip for ${values.destination || "a first-time visitor"}.`)
```
**问题：** `Object.fromEntries(new FormData(form).entries())` 返回的对象没有 `.length` 属性。结果发送的消息变成 "Plan a undefined China trip for..."。
**修复：** 确认表单 `<select name="...">` 的 name 属性，将 `values.length` 改为正确的字段名（可能是 `values.duration`）。

#### 3. `api()` 函数无请求超时
**文件：** `web/app.js` 第 81-95 行
**问题：** `fetch()` 没有设置 AbortController/signal。Vercel 冷启动最长达 10 秒，期间界面完全挂起无反馈。
**修复：** 添加 AbortController 超时（建议 15s），配合 `setStatus` 显示加载状态。

---

### 🟡 P1 — 逻辑缺陷

#### 4. `sendChat()` 使用 raw fetch 而非 `api()` 函数
**文件：** `web/app.js` 第 319 行
**问题：** 除聊天外的所有 API 调用都使用 `api()` 统一函数（含 auth header、错误处理），唯独 `sendChat` 自己实现了 fetch。如果后续聊天接口需要认证，这里会漏掉 Authorization header。
**修复：** 保持 header 一致性，或统一使用 `api()` 模式。

#### 5. 空 `catch {}` 静默吞错误
**文件：** `web/app.js` 第 168 行（loadAuthConfig）、第 431 行（restoreSession）
**问题：** `loadAuthConfig()` 失败时没有提示用户；`restoreSession()` 失败时静默清除 token，用户不会知道自己已被登出。
**修复：** 添加 showToast 告知状态变化。

#### 6. 城市卡片无图片 fallback
**文件：** `web/app.js` 第 178 行 `image.src = city.image;`
**问题：** 如果后端返回的 `city.image` 为 null/undefined/404 路径，显示破损图片。
**修复：** 添加默认 fallback 图片或隐藏图片容器。

#### 7. 城市 API 返回的图片路径可能是前端不可解析的
**问题：** `city.image` 如果是后端静态文件路径（如 `/static/img/beijing.jpg`），需确认 Vercel 路由是否正确代理到该文件。否则全部城市卡片图片 404。

---

### 🔵 P2 — 代码质量问题

#### 8. `withButtonBusy` 对含 SVG 的按钮行为异常
**文件：** `web/app.js` 第 82-93 行
**问题：** 设置了 `label` 参数时，`button.textContent = label` 会清除所有子元素（包括 SVG 图标）。恢复时 `innerHTML = oldHtml` 可能不匹配。
**修复：** 仅修改文本节点或添加 loading 动画，不覆盖 innerHTML。

#### 9. `addMessage` 从模板中取 span 不够精确
**文件：** `web/app.js` 第 296 行 `$("span", node).textContent = author;`
**问题：** `$("span", node)` 返回第一个 span。如果模板中有多个 span，选错了元素。
**修复：** 使用 class 精确匹配：`.querySelector(".message__author")`。

#### 10. `saveTrip()` 认证路径无错误处理
**文件：** `web/app.js` 第 388-398 行
**问题：** 当 `state.token` 存在时调用 `api()` 但不在 try/catch 中。
**修复：** 使用 try/catch 包裹 API 调用。

---

## 🎨 二、UI/UX 优化建议

### 🔴 严重

#### U1. DESIGN.md 设计系统未实现 — 最大痛点
**现状：** `DESIGN.md` 定义了暗色 "熊猫中国风" 设计系统（深色背景、ink-wash 山水、竹绿/金/硃砂红、Noto Sans SC），但**实际 CSS (`app.css`) 是纯浅色主题**（白底蓝橙配色、Plus Jakarta Sans 字体、无任何中国风元素）。
- 品牌识别完全丢失
- 产品名叫 "VisePanda"/"熊猫行"，视觉上没有任何熊猫或中国元素
- 与 VP-Hermes-Web 的暗色设计系统不统一

#### U2. 无 Dark Mode 支持
**文件：** `app.css` 第 42 行 `color-scheme: light;`
**问题：** 没有 `prefers-color-scheme: dark` 的媒体查询。

#### U3. Google Fonts 渲染阻塞
**文件：** `app.css` 第 1 行 CSS `@import` 引用 Plus Jakarta Sans
**问题：** CSS `@import` 会阻止浏览器渲染，用户看到空白页面约 0.5-1.5 秒。
**修复：** 改用 `<link rel="preconnect">` + `<link rel="stylesheet">` 在 HTML head 中，配合 `font-display: swap`。

---

### 🟡 建议

#### U4. 缺少 `theme-color` meta 标签
**文件：** `web/index.html`
**影响：** 手机浏览器 chrome 颜色与页面不匹配，PWA 体验不完整。

#### U5. Featured Cities 无加载骨架屏
**文件：** `web/app.js` 第 218-220 行
**问题：** Featured cities 直接渲染无 skeleton loading。

#### U6. Toast 错误消失过快（3.2s）
**问题：** 错误信息在 3.2 秒后自动消失，用户来不及阅读长错误消息。建议提升到 5-6s。

#### U7. Chat 流式响应时输入框仍然可编辑
**问题：** `withButtonBusy` 只禁用了发送按钮，但输入框 `#chatInput` 未被禁用。

#### U8. 页面切换无过渡动画
**问题：** `setView()` 直接切换 `is-hidden`，没有任何 transition/fade 效果。

#### U9. 城市搜索结果无关键词高亮
**问题：** 搜索时只显示数量变化，无匹配关键词的视觉反馈。

#### U10. 浅色主题 CSS 对比度可能不达标
**问题：** `--text-muted: #486474` 在 `--bg: #eef8fc` 背景上，AA 对比度可能不达标。

---

## 📐 三、文档问题

| 问题 | 详情 |
|------|------|
| CONTEXT.md 写 CSS 是 `style.css` | 实际文件是 `app.css` |

---

## 📋 四、优化优先级

### 立即修复
1. SSE JSON 解析加 try/catch
2. Quick Planner `values.length` 字段名修正
3. `api()` 添加 AbortController 超时

### 高优先级
4. 实现 DESIGN.md 暗色设计系统（或更新 DESIGN.md 匹配现有主题）
5. 统一 `sendChat` 使用 `api()` 函数
6. 城市图片添加 fallback

### 中优先级
7. 添加 Dark Mode 支持
8. Google Fonts 改为非阻塞加载
9. 添加 `theme-color` meta
10. 空 catch 增加有意义的状态反馈
