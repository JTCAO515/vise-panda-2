# 交互模式

> 动画、加载、手势、过渡

## 过渡

默认过渡：`180ms ease`

适用元素：
- 按钮 hover/active
- Tab 切换
- 面板显隐
- 颜色/边框变化

## 加载态

| 模式 | 实现 |
|------|------|
| 骨架屏 | `.skeleton-card` 3 个灰色占位条 |
| 按钮加载 | `aria-busy="true"` 禁用态 |
| 文字加载 | "Loading..." 状态文字 |
| 流式输出 | 逐字显示（AI 回答） |
| 全页加载 | 面板级 loadingCards() |

## 手势

| 手势 | 场景 |
|------|------|
| 点击 | 主要操作 |
| 滑动 | City Strip 横向滚动 |
| 长按 | 暂未使用 |
| 下拉 | 暂未使用（保留空间） |

## 动画性能守则

- 优先使用 `transform` 和 `opacity`（GPU 加速）
- 避免动画 `width`/`height`/`top`/`left`
- 动画元素使用 `will-change`
- 尊重 `prefers-reduced-motion`
