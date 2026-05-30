---
## Iteration 2 (跳过) — Supabase Postgres
**原因**: 缺少数据库密码，无法直连。
**替代**: SQLite /tmp 对 MVP 够用。
**待办**: 获取 Supabase DB password → `DATABASE_URL=postgresql://postgres:[PWD]@db.jdlinmdhmulozrjeseyc.supabase.co:5432/postgres`

---

## Iteration 3 — 首页改版 + 行程生成 Beta

**日期**: 2026-05-24
**目标**: 首页有推荐卡片，行程输出好看
**状态**: ✅ 完成

### 改动清单

| # | 改动 | 效果 |
|---|------|------|
| 1 | 卡片 CSS（.card/.cards/.card-emoji） | hover 上浮 + 发光边框 |
| 2 | 首页 3 个快捷卡片（北京/成都/云南） | 点击自动带 prompt 进聊天 |
| 3 | `goChat()` 函数 | 统一跳转逻辑 |
| 4 | 骨架屏 CSS（.skeleton + shimmer） | 等待 LLM 时的加载动画 |
| 5 | 行程卡片 CSS（.trip-card） | LLM 输出行程自动包裹高亮框 |
| 6 | `M()` 函数增强 | 检测 `**Day N**` → 自动套 trip-card |
| 7 | 发送按钮防重复 | 发送时 disabled + ...，完成恢复 |

### 测试结果（本地）

```
cards=4 | goChat=1 | skeleton=2 | trip=3 | btnDisable=2 | mobile=1
6/6 PASS
```

---

## Iteration 3 — 首页改版 + 行程生成 Beta

**日期**: 2026-05-24
**目标**: 首页有推荐卡片，行程输出好看
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | 卡片 CSS | hover 上浮 + 发光边框 |
| 2 | 首页 3 个快捷卡片 | 北京/成都/云南，点击自动带 prompt 进聊天 |
| 3 | `goChat()` 函数 | 统一跳转逻辑 |
| 4 | 骨架屏 CSS + shimmer 动画 | 等待 LLM 时显示加载条 |
| 5 | 行程卡片 `.trip-card` | LLM 输出行程自动高亮框 |
| 6 | `M()` 函数增强 | 检测 `**Day N**` → 套 trip-card |
| 7 | 发送按钮防重复 | disabled + "..." → 完成恢复 |

**测试**: 6/6 PASS

### 部署

- [x] 本地测试通过
- [ ] 待部署


---

## Iteration 4 — 聊天体验打磨

**日期**: 2026-05-24
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | 消息时间戳 | 每条消息右下角显示 HH:MM |
| 2 | `smartScroll()` | 用户在看历史时不强制滚动，靠近底部才自动滚 |
| 3 | `clearChat()` 按钮 | Header 新增 Clear 按钮，清空聊天 + localStorage |
| 4 | 游客 ID 持久化 | `vp_trip` 存 localStorage，刷新不丢 trip |

**测试**: 6/6 PASS


---

## Iteration 5 — 错误处理 + 离线韧性

**日期**: 2026-05-24
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | favicon 路由 | 返回 204，消灭 500 错误日志 |
| 2 | 错误重试按钮 | LLM 失败时显示 "Retry" 链接 |
| 3 | 网络错误捕获 | "Connection failed" + 重试按钮 |
| 4 | Supabase 加载 fallback | 5s 未加载显示刷新提示 |
| 5 | health 增强 | 返回 version + db 类型 |

**测试**: 7/7 PASS


---

## Iteration 7+8 — 空态欢迎 + 安全加固

**日期**: 2026-05-24
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | 欢迎页 + 4 个快捷 chip | 空聊天时显示引导，点 chip 直接提问 |
| 2 | 有历史消息时自动隐藏欢迎页 | loadHistory 检测到消息 → 移除 welcome |
| 3 | `_sanitize()` 函数 | 去 HTML 标签、控制字符、限长 2000 |
| 4 | IP 级限流 | 60s 窗口内最多 20 次请求 |

**测试**: 7/7 PASS


---

## Iteration 9 — 行程列表页

**日期**: 2026-05-24
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | `GET /api/trips` | 按用户查询所有行程，含消息数 |
| 2 | `/trips` 页面 | 卡片网格展示行程，空态引导 |
| 3 | Chat header 新增 "Trips" 链接 | 导航到行程列表 |
| 4 | 首次消息自动设 trip title | 用前 80 字做行程标题 |

**测试**: 5/5 PASS


---

## Iteration 11 — 分享行程

**日期**: 2026-05-24
**状态**: ✅ 完成

| # | 改动 | 效果 |
|---|------|------|
| 1 | Trip 模型加 `share_id` | 唯一分享标识 |
| 2 | `POST /api/trips/{id}/share` | 生成/返回分享链接 |
| 3 | `GET /api/trips/{id}/share` | 获取已有分享链接 |
| 4 | `/share/{share_id}` 只读页 | 公开查看行程，无登录 |
| 5 | Trips 页加 🔗 Share 按钮 | 一键复制分享链接 |

**测试**: 4/4 PASS

---

## Iteration 13 (Phase 1) — 数据库升级 Postgres + 用户中心

**日期**: 2026-05-24
**目标**: SQLite → Supabase Postgres 迁移，用户中心 UI
**状态**: ✅ 完成

### 改动清单

| # | 改动 | 效果 |
|---|------|------|
| 1 | Supabase Management API 集成 | HTTP-based 数据库操作替代 SQLAlchemy Session |
| 2 | `_row_to_model` 重构 | 绕过 ORM  instrumentation，支持 _Row 对象 |
| 3 | `filter()` 支持 SQLAlchemy BinaryExpression | 自动编译为原始 SQL |
| 4 | `QueryBuilder.delete()` 方法 | 支持 DELETE 操作 |
| 5 | 代理修复 (SOCKS5→HTTP) | 通过 Xray HTTP proxy 连接 Supabase API |
| 6 | 全量 Postgres schema (6 张表 + 4 索引) | 通过 Supabase Management API 创建 |
| 7 | `GET /api/profile` | 返回用户资料（email/phone/name） |
| 8 | `PUT /api/profile` | 更新用户姓名 |
| 9 | `POST /api/auth/change-password` | 邮箱用户修改密码 |
| 10 | `/profile` 页面 | 用户资料编辑 UI（姓名/语言/密码） |
| 11 | `static/profile.js` | 前端交互（保存/改密码/登出） |

### 待办（需人工操作）

| # | 内容 | 原因 |
|---|------|------|
| 1 | 设 `DATABASE_URL` 切原生 Postgres 连接 | 需数据库密码 |
| 2 | 阿里云短信配置 | 需 AccessKey + Secret |
| 3 | CDN 加速 (Cloudflare) | 需域名 DNS 接入 |
| 4 | 微信登录 | 需微信开放平台账号 |

### 测试

- 健康检查: `{"db":"postgres"}` ✅
- 邮箱注册/登录: 全流程通过 ✅
- 资料读取/更新: GET/PUT profile ✅
- 修改密码: old→new 验证通过 ✅
|- 页面路由: `/profile` 302 → `/?login=1`（未登录正确）✅
|

---

## Iteration 107-112 — 美观+速度 Phase 1

**日期**: 2026-05-30
**目标**: 加载速度优化 + CSS 动画系统 + 微交互 + 骨架屏 v2
**状态**: ✅ 完成

### Iter 107 — 字体加载优化 ⭐
| 改动 | 效果 |
|------|------|
| 删除 `@import url('geist')`（阻塞渲染） | 消除字体加载的渲染阻塞 |
| 新增 `_font_links()` 异步加载（preconnect + preload + noscript fallback） | 字体异步下载，文字立即以系统回退字体显示 |
| 所有页面 `<head>` 集成 `{_font_links()}` | Geist 加载完成后自动替换，无闪烁 |

### Iter 108 — 脚本按需加载 ⭐
| 改动 | 效果 |
|------|------|
| Landing 页去掉 2 个 Vercel Analytics 脚本 | -2 个 HTTP 请求，Landing 首屏更快 |
| Landing 页去掉 `esm.sh/@supabase/supabase-js@2`（60KB） | Landing 首屏省 60KB 带宽 |
| Auth Callback 页去掉 2 个 Vercel Analytics + supabase-js | 一页式跳转页无需这些依赖 |
| Trips 页去掉 2 个 Vercel Analytics | 列表页无需分析 |
| Chat 页保留 Analytics + supabase-js | 核心交互页面，数据有用 |
| Share 页保留 Analytics | 公开分享页，追踪分享转化 |

### Iter 109 — CSS 关键内联优化 ⭐
| 改动 | 效果 |
|------|------|
| bg-shanshui 修复双 opacity（SVG opacity + CSS opacity 叠乘） | 视觉正确性修复 |
| 添加 `will-change: transform` 到 bg-shanshui + bg-glow | GPU 层提前合成，滚动/动画更流畅 |
| 添加 `content-visibility: auto` 到目的网格 | 首屏不渲染下方元素，加快 LCP |
| dest-card hover 添加 `backface-visibility: hidden` | hover 上浮更平滑 |

### Iter 110 — CSS 动画系统增强 ⭐⭐
| 改动 | 效果 |
|------|------|
| 新增 `@keyframes slideUp` + `.msg-enter` 类 | 聊天消息从底部滑入动画 |
| 新增 `.stagger-d1` 到 `.stagger-d6` 延迟类 | 卡片列表支持步进式入场 |
| 新增 `@keyframes breathe` + `.bg-glow` 呼吸动画 | 背景光晕自动缓慢脉动 |
| fadeUp 添加 `scale(.98)` → `scale(1)` | 入场效果更丰富 |
| 所有动效遵循 `prefers-reduced-motion` | 无障碍兼容 |

### Iter 111 — 微交互增强 ⭐
| 改动 | 效果 |
|------|------|
| Send 按钮: hover scale(1.04) + glow, active scale(.96) | 点击反馈更自然 |
| Input focus: 额外外层 glow | 焦点状态更醒目 |
| Search box focus: 额外外层光晕 | 搜索框交互感更强 |
| .btn 使用 `cubic-bezier(.16,1,.3,1)` 缓动 | 按钮动画更弹手 |
| .btn 添加 `backface-visibility: hidden` | hover 时避免像素抖动 |

### Iter 112 — 骨架屏 v2 ⭐⭐
| 改动 | 效果 |
|------|------|
| `.skel-text` — 文字骨架变体 | 不同场景使用更精准的骨架 |
| `.skel-card` — 卡片骨架（伪元素 shimmer，渐变背景） | 替代纯色占位，更有质感 |
| `.skel-circle` — 圆形头像骨架 | 聊天头像加载前的占位 |
| `.skel-msg` — 完整消息骨架布局（头像+双行文字） | 消息加载模拟更真实 |
| shimmer 缓动改为 `cubic-bezier(.4,0,.2,1)` | 动画更自然不机械 |

### 测试结果
```
syntax check: 713 lines, ✅ Python AST clean
@import urls remaining: 0 ✅
Vercel Analytics (仅保留 Chat + Share): 2 ✅
Supabase JS (仅保留 Chat): 1 ✅
CSS animations: fadeUp ✓ slideUp ✓ shimmer ✓ breathe ✓ blink ✓ fadeIn ✓ scaleIn ✓ fadeInOut ✓
```

---

## Iteration 113-115 — 美观+速度 Phase 2

**日期**: 2026-05-30
**目标**: Hero视觉升级 + Logo + Bento网格 + Chat气泡
**状态**: ✅ 完成

### Iter 113 — Panda SVG Logo + Hero 装饰 ⭐⭐
| 改动 | 效果 |
|------|------|
| 创建 Panda SVG 头像（熊猫脸 SVG data URI）替换 `.brand-dot` | 品牌从抽象圆点变为具象熊猫 Logo |
| 所有页面 Header 统一更新 | 品牌一致性 |
| 新增 Hero 浮动装饰圈（`hero-decor`） | 背景更丰富，有层次感 |
| 新增 `@keyframes float` 轻轻浮动动画 | 微交互增加页面活力 |
| 移动端自动隐藏装饰（`display:none`） | 不干扰小屏体验 |

### Iter 114 — Bento 目的网格 ⭐⭐⭐
| 改动 | 效果 |
|------|------|
| 北京卡片 `.featured` 跨越 2 行（`grid-row:1/3`） | 打破均匀网格，视觉层次 |
| 桂林卡片 `.wide` 佔满第 3 行全宽（`grid-column:1/4`） + flex 横排布局 | 底部横向宽卡收尾，更像 Bento |
| 移动端 responsive 降级为普通 2 列 | 不破坏小屏体验 |

### Iter 115 — Chat 气泡升级 ⭐⭐
| 改动 | 效果 |
|------|------|
| AI 消息：30px 熊猫 SVG 头像 | 品牌识别，对话沉浸感 |
| 用户消息：渐变色圆 + "Y" 首字母 | 区分自己 vs AI |
| 新增 `.msg-body` 包裹层 | 排版结构清晰 |
| 新增 `@keyframes typing` + `.typing-indicator` | 三圆点弹跳等待动画 |
| 消息间距从 8px → 12px，增加间隙呼吸感 | 阅读舒适度 |

### 测试结果
```
syntax: ✅ AST clean
SW: ✅ stale-while-revalidate + cache-first
Cache: ✅ max-age=31536000 immutable
GZip: ✅ middleware
supabase-js: ✅ 0 script tags (dynamic import only)
```

---

## Iteration 116-119 — 速度专项

**日期**: 2026-05-30
**目标**: Service Worker + 懒加载 + 缓存策略 + 传输优化
**状态**: ✅ 完成

### Iter 116 — Service Worker v2 ⭐⭐
| 改动 | 效果 |
|------|------|
| 重写 SW：HTML stale-while-revalidate + 静态 cache-first + 字体CDN runtime cache | 二次访问秒开 |
| `Promise.allSettled` + `skipWaiting()` + `clients.claim()` | 可靠注册 + 立即生效 |

### Iter 117 — 冗余supabase-js移除 ⭐
| 改动 | 效果 |
|------|------|
| Chat页删掉 `<script src="supabase-js">`（chat.js已用动态import） | 首屏省1 HTTP + 60KB |

### Iter 118 — 浏览器缓存策略 ⭐
| 改动 | 效果 |
|------|------|
| 静态文件 `max-age=31536000, immutable` | 浏览器永久缓存 |
| `/sw.js` 路由 + `Service-Worker-Allowed: /` | SW 覆盖全站 |

### Iter 119 — GZip压缩 ⭐
| 改动 | 效果 |
|------|------|
| `GZipMiddleware(minimum_size=500)` | HTML/CSS减5-10倍 |
| 删除废弃 `static/pwa.js` | 清理 |

---

## Iteration 120-121 — Bug修复 + 英文化

**日期**: 2026-05-30
**目标**: 修复对话不可用 + 站点英文化
**状态**: ✅ 完成

### Iter 120 — Bug修复 ⭐⭐
| Bug | 根因 | 修复 |
|-----|------|------|
| 对话发送后一直显示骨架，无回复 | 骨架CSS类名`skel-block/skel-line/skel-w-*`不存在（Iter 112只加了skel-text/skel-card） | 新增`.skel-block`, `.skel-line.skel-w-*` 宽度变体 |
| SSE stream返回error时前端忽略 | `j.error` 在chat.js的stream解析中没有处理分支 | 新增`if (j.error)` 处理：显示错误文字+恢复按钮 |

### Iter 121 — 英文化 ⭐
| 改动 | 说明 |
|------|------|
| 所有目的地卡片中文prompt→英文 | `北京3天深度游` → `Beijing 3 days history culture mid budget` |
| welcome chips中文→英文 | `北京3天行程` → `Beijing 3-day itinerary` |
| 移除i18n自动检测中文逻辑 | 站点默认英文，不再根据浏览器语言自动切换中文 |

---

## Iteration 122 — 城市卡片图片化

**日期**: 2026-05-30
**目标**: Landing页目的地卡片使用Seedream图片
**状态**: ✅ 完成

### 改动
| 项 | 说明 |
|----|------|
| 6个dest-card内部嵌入`.dest-img-wrap` + `<img>` | 卡片从纯emoji文本→图片卡片 |
| 图片路径 `/static/img/city-{name}.jpg` | 北京/成都/上海/西安/桂林有图，Yunnan回退 |
| `loading=lazy` + `onerror` emoji回退 | 首屏不加载下方图片，出图失败自动降级 |
| hover `.dest-bg{scale(1.07)}` 放大 | 图片悬停动效 |
| 移动端wide图全宽 | 响应式适配 |

---

## Iteration 123 — 暗色/亮色主题切换

**日期**: 2026-05-30
**目标**: 一键主题切换 + 系统偏好检测 + 持久化
**状态**: ✅ 完成

### 改动
| 项 | 说明 |
|----|------|
| `[data-theme="light"]` 覆盖8组CSS变量 | 完整亮色配色（auto bg/text/muted/line/accent） |
| `<head>`内联主题初始化脚本 | 读取localStorage > prefers-color-scheme > 默认dark |
| header `.theme-toggle` 按钮 | 🌙→☀️ 双向切换，点击即时生效 |
| `localStorage.setItem('vp_theme')` | 刷新/下次访问保留偏好 |
| `*{transition:background/border/color}` | 切换时全站平滑过渡，无闪烁 |
| onload自动匹配图标 | 切到light显示🌙，切到dark显示☀️ |

---

## Iteration 124 — 移动端深度适配

**日期**: 2026-05-30
**目标**: iOS/Android触屏优化、交互修复
**状态**: ✅ 完成

### 改动
| 项 | 说明 |
|----|------|
| `*{touch-action:manipulation}` | 防双击缩放（文字太小不会意外放大） |
| `-webkit-tap-highlight-color:transparent` | 去掉点击灰色半透明框 |
| `#thread{-webkit-overflow-scrolling:touch}` | iOS弹性滚动 |
| `#thread{overscroll-behavior:contain}` | 下拉到顶不触发页面刷新 |
| `@media(hover:none)` | 触屏取消hover变形动画 |
| `input{font-size:16px}` | 防iOS自动缩放（<16px会放大） |
| `@media(max-width:480px)` header隐藏品牌名 | 小屏省空间 |
| `.chip/.welcome-chip` tap target增大 | 更容易触碰 |
