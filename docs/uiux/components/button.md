# 按钮

## 主要按钮 `.primary`

| 状态 | 样式 |
|------|------|
| 默认 | `--accent` 背景，白色文字，`--radius` 圆角 |
| Hover | `--accent-strong` 背景，轻微上移 |
| 禁用 | 灰色背景，`cursor: progress` |
| Busy | `aria-busy` 属性，显示加载态 |

```css
.primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
}
```

## 次要按钮 `.secondary`

| 状态 | 样式 |
|------|------|
| 默认 | 白色背景，`--border` 边框 |
| Hover | `--surface-tint` 背景 |

## 图标按钮 `.icon-button`

- 40px 正方形
- 内联 SVG 图标
- 用作账号、设置等

## CTA 按钮（Hero区）

- 圆角 `999px`（药丸形）
- 品牌色 `--brand`
- 带阴影 `box-shadow`
- Hover 时上移 + 放大
