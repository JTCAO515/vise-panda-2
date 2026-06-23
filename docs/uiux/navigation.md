# 导航系统

> Tab 导航、顶部栏、底部栏规范

---

## 整体结构

```
┌─────────────────────────┐
│      Topbar (品牌)       │  ← 仅桌面显示
├─────────────────────────┤
│  Plan │ Ask │ Cities... │  ← 桌面：顶部 Tab 栏
│                         │    移动：底部 Tab 栏
│                         │
│      Content Area       │
│                         │
│                         │
├─────────────────────────┤
│  Plan │ Ask │ Cities │  │  ← 仅移动：底部固定导航
│  Tools │ Trips          │
└─────────────────────────┘
```

---

## Tab 列表

| Tab | 图标 (SVG) | 视图 | 说明 |
|-----|-----------|------|------|
| Plan | 房子 | `dashboard` | 首页规划工作台 |
| Ask | 聊天气泡 | `chat` | AI 咨询流 |
| Cities | 建筑 | `cities` | 城市浏览 |
| Tools | 工具 | `tools` | 旅行工具 |
| Trips | 书签 | `trips` | 保存的行程 |
| Translate | 翻译 (🆕) | `translate` | 翻译功能 |

---

## 桌面导航

- 顶部栏 + Tab 行
- 品牌 logo 在左上角
- Tab 居中排列
- 激活 Tab：`--surface-tint` 背景 + `--accent` 底部线条
- 右侧：账号按钮

## 移动导航

- 固定底部，`position: fixed; bottom: 0`
- 安全区域适配（`env(safe-area-inset-bottom)`）
- 5-6 个等宽 Tab
- 激活 Tab：图标色变为 `--brand`
- 隐藏条件：Ask 视图输入态时隐藏（`is-chat-composing`）

## 导航切换逻辑

```js
setView(view) → 更新 data-view → 切换面板 visible
```
