# 设计令牌

> 真实来源：`web/app.css` 中的 CSS 自定义属性

---

## 颜色

### 主色板

| Token | 值 | 用途 | 预览 |
|-------|-----|------|------|
| `--brand` | `#0ea5e9` | 品牌色/主要操作/链接 | 🔵 天空蓝 |
| `--brand-strong` | `#075985` | 品牌文字/强调 | 🔵 深蓝 |
| `--accent` | `#f97316` | 主要CTA按钮 | 🟠 暖橙 |
| `--accent-strong` | `#c2410c` | CTA hover | 🟠 深橙 |

### 背景

| Token | 值 | 用途 |
|-------|-----|------|
| `--bg` | `#eef8fc` | 页面背景 |
| `--bg-elevated` | `#f8fcff` | 升高背景 |
| `--surface` | `#ffffff` | 卡片、控件、面板 |
| `--surface-soft` | `#f3f9fc` | 柔和区块 |
| `--surface-tint` | `#dff4fb` | 选中态/着色 |

### 文字

| Token | 值 | 用途 |
|-------|-----|------|
| `--text` | `#0f2633` | 主要文字 |
| `--text-muted` | `#486474` | 次要文字 |
| `--text-subtle` | `#6f8794` | 弱化文字 |

### 边框

| Token | 值 | 用途 |
|-------|-----|------|
| `--border` | `#d4e6ee` | 默认边框 |
| `--border-strong` | `#a9cedc` | 强调边框 |

### 语义色

| Token | 值 | 用途 |
|-------|-----|------|
| `--success` | `#2d8a63` | 成功/完成 |
| `--warning` | `#b7791f` | 警告 |
| `--danger` | `#b42318` | 错误/删除 |

### 阴影

| Token | 值 | 用途 |
|-------|-----|------|
| `--shadow-soft` | `0 8px 20px rgba(7, 89, 133, 0.07)` | 卡片阴影 |
| `--shadow-raised` | `0 16px 34px rgba(7, 89, 133, 0.12)` | 升高阴影 |
| `--shadow-sticky` | `0 18px 44px rgba(23, 33, 38, 0.2)` | 固定元素阴影 |

---

## 字体

| 属性 | 值 |
|------|-----|
| Font Stack | `"Plus Jakarta Sans", Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` |
| 字重 | 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold), 800 (ExtraBold) |
| 行高 | Body: 1.6, Heading: 1.1 |

### 字号规范

| 层级 | 大小 | 字重 | 用途 |
|------|------|------|------|
| Display | `clamp(2.5rem, 6vw, 4.5rem)` | 800 | Hero 标题 |
| H1 | `1.5rem` | 700 | 页面标题 |
| H2 | `1.25rem` | 700 | 区块标题 |
| H3 | `1.05rem` | 600 | 卡片标题 |
| Body | `0.92rem` | 400 | 正文 |
| Small | `0.82rem` | 400 | 辅助文字 |
| Meta | `0.78rem` | 500 | 标签/状态 |
| Caption | `0.72rem` | 500 | 极小文字 |

---

## 间距

| Token | 值 |
|-------|-----|
| `--space-1` | `6px` |
| `--space-2` | `10px` |
| `--space-3` | `14px` |
| `--space-4` | `18px` |
| `--space-5` | `24px` |
| `--space-6` | `32px` |

---

## 圆角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius` | `8px` | 卡片、控件、面板 |
| 药丸 | `999px` | CTA按钮、标签 |
| 底部导航 | `16px` | 移动端底部栏 |

---

## 图标

- 所有图标使用内联 SVG
- 不用 emoji 作为主要 UI 图标
- 图标大小统一：`20px`（导航栏）、`16px`（内联）、`24px`（操作按钮）
- stroke-width: `2`，圆头端点
