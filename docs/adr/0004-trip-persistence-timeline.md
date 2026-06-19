# 0004 — Trip Persistence + Timeline Visualization

**Status:** Accepted
**Date:** 2026-06-19

## Context

VP-Hermes 当前行程数据只存在浏览器 localStorage 中，用户切换设备或清缓存后丢失。同时，AI 输出的行程是纯文本段落，用户难以快速浏览和消化。需要解决：

1. 登录用户行程跨设备持久化
2. 把文字行程渲染为可视化时间线

## Decision

### Trip Persistence

- 后端新增 `POST/GET /api/trips` 端点（纯 WSGI，零依赖）
- 数据存储用 `data/trips.json` 文件缓存（Vercel 无持久磁盘的替代：每次请求从 Supabase 读取，冷启动时先返回 localStorage 再静默同步）
- 前端策略：`if (loggedIn) → sync with API else → localStorage only`
- 冷启动优化：页面渲染不阻塞 API 调用 — 先展示 localStorage 缓存的行程，API 返回后静默更新

### Timeline Visualization

- 纯前端渲染，不依赖后端 API
- AI 回复规范：DeepSeek system prompt 统一要求行程输出用 `### Day N: [标题]` 格式
- 前端新模块 `web/trip-timeline.js`：
  - 正则 `^###\s+Day\s+(\d+):\s*(.+)$` 解析每站
  - 垂直 CSS 时间线（无第三方库）
  - 每站按类型着色：🟢景点 / 🔵交通 / 🟠餐饮 / 🟣住宿

## Consequences

- ✅ 行程跨设备可用
- ✅ 冷启动不阻塞用户交互
- ✅ 时间线解析无外部依赖
- ⚠️ Vercel 无持久磁盘 → Supabase 冷启动 +10ms（可接受）
- ⚠️ AI 输出格式靠 prompt 约束，非强制，解析应有容错
