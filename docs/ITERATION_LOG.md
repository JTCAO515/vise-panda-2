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

