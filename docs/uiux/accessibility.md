# 可访问性

> A11y 标准与检查清单

## 语义化

- 使用 `<button>` 而非 `<div>` 做点击操作
- Tab 栏使用 `role="tablist"` / `role="tab"` / `role="tabpanel"`
- 状态文字使用 `role="status"` / `aria-live="polite"`
- 图标按钮使用 `aria-label`
- 图片使用 `alt` 描述

## 焦点管理

- 所有可交互元素有可见 focus ring（`--focus-ring`）
- 模态框打开时焦点锁定
- Tab 切换遵循 `aria-selected`
- 使用 `tabIndex` 控制 Tab 顺序

## 色彩对比度

- 主要文字 `--text (#0f2633)` on `--bg (#eef8fc)` — 通过 AA
- 品牌文字 `--brand-strong (#075985)` on `--surface (#ffffff)` — 通过 AA
- 次要文字 `--text-muted (#486474)` — 注意在浅色背景上需 >= 4.5:1

## 动效

- 尊重 `prefers-reduced-motion` 媒体查询
- 动画非核心功能必要
- 不影响任务完成
