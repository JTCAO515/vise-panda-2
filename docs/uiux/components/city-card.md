# 城市卡片 `.city-card`

> 目的地城市展示卡片

## 结构

```
┌──────────────────┐
│                   │
│    城市图片        │  ← 4:3 宽高比
│                   │
├──────────────────┤
│  城市名称 (h3)     │
│  省份 · 天数 · 季节 │  ← facts
│  一句话氛围描述     │  ← vibe
│  [标签] [标签]     │  ← highlights
└──────────────────┘
```

## 规格

| 属性 | 值 |
|------|-----|
| 宽度 | 自适应（grid） |
| 边框 | 1px solid `--border` |
| 圆角 | `--radius` (8px) |
| 背景 | `--surface` |
| 内边距 | 18px |
| 图片比例 | 4:3 |

## 交互

| 事件 | 效果 |
|------|------|
| Hover | `--shadow-raised`，`translateY(-2px)` |
| Tilt (ViseBits) | 3D 透视倾斜，`maxTilt: 6°` |
| Spotlight (ViseBits) | 径向渐变跟随鼠标 |

## 变体

### 特色卡片（Featured / City Strip）
- 水平滚动容器 `scroll-snap-type: x mandatory`
- 宽度 260px
- 用于首页精选城市

### 网格卡片（Grid）
- `repeat(auto-fill, minmax(240px, 1fr))`
- 用于城市浏览页面
