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

---

## Iteration 125 — 聊天/SSE 稳定性修复

**日期**: 2026-05-30  
**目标**: 修复“页面无法对话/一直加载”的潜在后端异常，保证 SSE 流不会被后处理阶段打断  
**状态**: ✅ 完成

### Iter 125 — Bug 修复（SSE 后处理） ⭐⭐
| 问题 | 根因 | 修复 |
|------|------|------|
| SSE 流结束后可能异常中断，前端表现为一直 loading/无回复 | `generate()` 后处理阶段使用了未定义变量 `db2`（UnboundLocalError），异常会直接终止 SSE | 重排 DB 操作：先 `db2 = get_db()` 再使用；并用 `try/except` 保护后处理，失败时向前端返回 `post_process_failed` 错误事件而不是静默断流 |

### 测试
```
python -m py_compile api/index.py ✅
```

---

## Iteration 126 — English-native UI + DeepSeek + DB fallback

**日期**: 2026-05-30  
**目标**:
- 英文为默认 UI（除非手动切换到中文，否则页面不出现中文）
- LLM 默认切换为 DeepSeek（OpenAI-compatible）
- 无 Supabase 凭据时也能正常对话（SQLite /tmp fallback）
**状态**: ✅ 完成

### Iter 126 — 语言与 UI（英文原生） ⭐⭐
| 改动 | 说明 |
|------|------|
| 移除 `/_inject_config()` 的 IP 语言自动切换逻辑 | 不再根据 IP/国家自动把站点切到中文 |
| Header 语言按钮默认显示 `ZH`（英文 UI 下不出现“中”） | 中文模式下自动显示 `EN` |
| Chat / Landing / Trips / Profile 中的中文文案与中文快捷 chips 全部替换为英文 | 中文只在用户切换语言后由 i18n 渲染 |

### Iter 126 — LLM（DeepSeek 默认） ⭐⭐
| 改动 | 说明 |
|------|------|
| 默认 `LLM_BASE_URL=https://api.deepseek.com/v1` | OpenAI-compatible `/chat/completions` |
| 默认 `LLM_MODEL=deepseek-v4-flash` | 可用环境变量覆盖 |
| `/api/chat` 请求携带 `lang` | 后端按 UI 语言选择 system prompt（英文/中文） |

### Iter 126 — DB（可用性修复） ⭐⭐⭐
| 问题 | 根因 | 修复 |
|------|------|------|
| 未配置 Supabase PAT 时，所有 DB 操作会失败导致聊天不可用 | `get_db()` 强制使用 Supabase Management API | 加入 SQLAlchemy fallback：优先 `DATABASE_URL`，否则无 PAT 时用 `/tmp/visepanda.sqlite3` |
| 站点包含 `/static/pwa.js` 但文件缺失 | 引发 PWA/缓存脚本不一致 | 恢复 `static/pwa.js`，并新增 `/sw.js` 根路径路由注册 SW |

### 测试
```
python -m py_compile api/index.py ✅
```

---

## Iteration 127 — Chat reply rendering + DeepSeek stream compatibility

**日期**: 2026-05-30  
**目标**: 修复“发送后无回答/空白”的问题，确保 DeepSeek 流式返回可被后端解析、前端渲染可见  
**状态**: ✅ 完成

### Iter 127 — 后端：DeepSeek 流式字段兼容 ⭐⭐
| 改动 | 说明 |
|------|------|
| stream parser 支持 `delta.reasoning_content` 与 legacy `text` | 部分 DeepSeek 流式包不会走 `delta.content`，导致前端永远收不到 token |

### Iter 127 — 前端：避免把 bot 消息容器清空 ⭐⭐⭐
| 问题 | 根因 | 修复 |
|------|------|------|
| bot 回复不显示（甚至 skeleton 也消失） | 前端收到非 token 的 SSE 包时会把整个 bot DOM `innerHTML` 覆盖为 `''` | 改为只更新 `.bubble` 内容；若尚未收到 token，不覆盖 skeleton；若 stream 结束仍无 token，显示明确错误提示 |

### Iter 127 — PWA 缓存：强制客户端拿到新脚本 ⭐⭐
| 改动 | 说明 |
|------|------|
| SW cache name `vp-v2` → `vp-v3` | 避免旧版 chat.js 被 SW 长期缓存导致修复无法生效 |

### 测试
```
python -m py_compile api/index.py ✅
```

---

## Iteration 128 — Better error surfacing + non-SSE stream compatibility

**日期**: 2026-05-30  
**目标**: 解决“已配置但依然无输出/仅提示 No response”的盲区，让真实错误在页面可见，并兼容非 SSE 的流式/单包 JSON 返回  
**状态**: ✅ 完成

### Iter 128 — 后端：兼容非 SSE / 单包 JSON ⭐⭐
| 改动 | 说明 |
|------|------|
| stream parser 允许解析“无 data: 前缀”的 JSON 行 | 有些供应商不会用标准 SSE 前缀 |
| 支持 `choices[0].message.content` | 当供应商忽略 `stream=true` 并一次性返回 JSON 时仍能取到内容 |

### Iter 128 — 前端：HTTP 错误直接显示 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| `fetch('/api/chat')` 若 `!r.ok`，直接在气泡里显示 HTTP 状态码与部分响应内容 | 避免 401/500 被误判为“模型无响应” |

### Iter 128 — PWA 缓存刷新 ⭐
| 改动 | 说明 |
|------|------|
| SW cache name `vp-v4` | 确保线上立即拿到最新 chat.js |

---

## Iteration 129 — VisePanda Logo 替换（YS Panda）

**日期**: 2026-05-30  
**目标**: 将你提供的 YS Panda 图片作为 VisePanda 全站 logo / favicon / PWA 图标  
**状态**: ✅ 完成

### Iter 129 — 资源与图标 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| 新增 `static/img/logo-{32,64,192,512,1024}.png` | 透明背景，多尺寸适配 |
| 新增 `static/img/favicon.ico` | 浏览器 favicon |
| `static/manifest.json` icons 更新为 png（192/512 + maskable） | PWA 安装图标正确显示 |
| 全站 `<header>` seal 替换为新 logo 图片 | 视觉统一，替代原 emoji |
| `/favicon.ico` 与 `/favicon.png` 路由返回真实图标文件 | 不再 204，占位变为可用 favicon |

---

## Iteration 130 — 对话兜底可用性（可诊断）

**日期**: 2026-05-30  
**目标**: 让“无回复/配置错误/后端异常”变成可见、可定位、可重试的问题  
**状态**: ✅ 完成

### Iter 130 — Request ID + 结构化错误 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| 全站中间件注入 `X-Request-Id` | 每个请求都有可追踪 request_id（可用于 Vercel 日志定位） |
| `/api/chat` 的错误事件增加 `code` + `request_id` | 前端可以展示更明确的错误原因与追踪 ID |
| 前端在错误气泡中展示 `request_id` + Retry | 方便你直接用 request_id 去 Vercel logs 对齐排查 |

### Iter 130 — 诊断接口 ⭐⭐
| 改动 | 说明 |
|------|------|
| `GET /api/llm/diag` | 返回 LLM 配置状态（不泄露密钥） |
| `GET /api/llm/diag?test=1` | 发起最小化请求测试连通性，返回 status/错误摘要 |

---

## Iteration 131 — DeepSeek 兼容与对话体验增强

**日期**: 2026-05-30  
**目标**: 提升 DeepSeek 流式返回兼容性与首包等待体验，便于线上排障  
**状态**: ✅ 完成

### Iter 131 — 前端：首包慢提示 ⭐⭐
| 改动 | 说明 |
|------|------|
| 8s 未收到首 token 自动显示 “Still working…” 提示 | 避免用户误以为卡死；不覆盖骨架屏 |

### Iter 131 — 后端：流式指标日志 ⭐⭐
| 改动 | 说明 |
|------|------|
| 输出 `chat_stream_done` 日志（duration/first_token/token_chars/error_code/request_id） | Vercel logs 可直接定位“是否首包、耗时、是否有错误码” |

---

## Iteration 132 — 英文原生一致性（核心页面无中文泄漏）

**日期**: 2026-05-30  
**目标**: 核心页面（Landing/Chat/Trips/Profile/Share/404）英文模式下不出现中文文案  
**状态**: ✅ 完成

### Iter 132 — 文案清理 ⭐⭐
| 改动 | 说明 |
|------|------|
| 去除核心页面中的零散中文字符串 | 例如 placeholder 示例、提示文案等改为英文 |
| `POST /api/itinerary/validate` 返回 warning 全英文化 | 避免英文站点下接口返回中文提示 |

---

## Iteration 133 — 品牌落地（YS Panda 视觉系统）

**日期**: 2026-05-30  
**目标**: 统一全站品牌资产（Logo/Favicon/PWA/OG），并补充品牌使用规范  
**状态**: ✅ 完成

### Iter 133 — OG 分享图 ⭐⭐
| 改动 | 说明 |
|------|------|
| 新增 `static/img/og-image.png`（1200×630） | 用 YS Panda Logo + 暗色渐变背景生成 |
| Landing 的 `og:image` 更新为本地 `/static/img/og-image.png` | 避免依赖外部域名资源 |

### Iter 133 — 品牌规范文档 ⭐
| 改动 | 说明 |
|------|------|
| 新增 `BRAND.md` | 记录 Logo/Favicon/OG/PWA 资产与使用建议 |

---

## Iteration 134 — 生产化（README + 启动自检 + CI）

**日期**: 2026-05-30  
**目标**: 提升部署可维护性与可排障性，让每次提交都有最基本的自动校验  
**状态**: ✅ 完成

### Iter 134 — 文档与自检 ⭐⭐
| 改动 | 说明 |
|------|------|
| 新增 `README.md` | 本地启动、Vercel 环境变量、诊断与排障说明 |
| 启动自检 warnings + `/api/health` 暴露 | LLM key 缺失、配置不完整会在 health 里体现 |

### Iter 134 — GitHub Actions CI ⭐⭐
| 改动 | 说明 |
|------|------|
| 新增 `.github/workflows/ci.yml` | push/PR 自动执行 `py_compile` 基础语法检查 |

---

## Iteration 135 — 页面加载加速（首屏稳定）

**日期**: 2026-05-30  
**目标**: 提升 Chat 首屏加载速度与稳定性，减少第三方资源导致的阻塞/白屏  
**状态**: ✅ 完成

### Iter 135 — Chat 初始化不阻塞 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| Chat 页不再 `await` Supabase 动态 import | 避免 esm.sh 网络波动导致事件绑定延后、页面“看似卡住” |

### Iter 135 — 地图资源懒加载 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| Chat 页移除 Leaflet CSS/JS 的默认引入 | 首屏不加载地图相关大资源 |
| 仅在检测到 itinerary 且需要展示地图时，按需加载 Leaflet + `/static/map.js` | 加速首屏、减少外部 CDN 失败对核心对话的影响 |

---

## Iteration 136 — 页面加载稳定性（去第三方字体阻塞）

**日期**: 2026-05-30  
**目标**: 减少第三方资源导致的首屏阻塞与不稳定（尤其是 fonts.google 访问不稳定的场景）  
**状态**: ✅ 完成

### Iter 136 — 移除 Google Fonts 引用 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| 全站移除 `fonts.googleapis.com / fonts.gstatic.com` 的 `<link>` 引用 | 统一回退到系统字体栈，减少外部网络依赖 |

---

## Iteration 137 — 静态资源缓存策略（速度 + 稳定性）

**日期**: 2026-05-30  
**目标**: 提升二次打开速度并减少资源抖动，同时避免 HTML/manifest/SW 被错误缓存  
**状态**: ✅ 完成

### Iter 137 — Cache-Control 分层 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| `/sw.js`、`/static/manifest.json` 禁用缓存 | 确保 SW/manifest 更新及时生效 |
| `/static/img/*` 长缓存（immutable） | 图片资源稳定、减少重复下载 |
| `/static/*.js/.css` 中等缓存（1 天） | 提升二次打开速度，配合 SW 版本滚动更新 |

---

## Iteration 138 — Service Worker 缓存升级（更稳更快）

**日期**: 2026-05-30  
**目标**: 提升重复访问速度，并在弱网/抖动场景下让页面更稳定可用  
**状态**: ✅ 完成

### Iter 138 — Precache 扩展 ⭐⭐
| 改动 | 说明 |
|------|------|
| Precache 增加 trips/profile/manifest 与核心品牌图片 | 让关键资源更容易命中缓存 |
| 缓存版本滚动 `vp-v4` → `vp-v6` | 避免旧缓存导致资源不一致 |

### Iter 138 — 导航请求策略 ⭐⭐⭐
| 改动 | 说明 |
|------|------|
| `navigate` 采用 network-first + 3s 超时回退缓存 | 弱网时避免白屏，优先展示可用页面 |

---

## Iteration 139 — 关键资源预加载（关键路径优化）

**日期**: 2026-05-30  
**目标**: 加速首屏与路由切换时的关键资源获取，降低“首次交互前等待”  
**状态**: ✅ 完成

### Iter 139 — preload 关键脚本 ⭐⭐
| 改动 | 说明 |
|------|------|
| Landing/Chat/Trips/Profile head 增加 `preload` | 预加载 `i18n.js` 与对应页面脚本（landing/chat/trips/profile）及 `pwa.js` |
