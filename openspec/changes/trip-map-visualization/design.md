# 设计文档：行程地图可视化

## 技术选型

| 项 | 选择 | 原因 |
|---|------|------|
| 地图引擎 | Leaflet + OpenStreetMap | 免费，无 API Key 要求，CDN 加载，Vercel 可用 |
| 瓦片源 | OpenStreetMap 默认瓦片 | 中国城市覆盖完整 |
| 标记图标 | Leaflet.divIcon（纯 CSS） | 无需加载外部图标集 |
| 坐标数据 | LLM 生成 + Nominatim 反向地理编码 | LLM 知道景点城市名，Nominatim 解析为经纬度 |

## 架构

### 数据流

```
LLM 输出行程文本
    │
    ▼
_parse_itinerary() 提取结构化数据
    │
    ▼
Trip.current_itinerary（已有，已保存）
    │
    ▼
前端 /api/trips/{id} 获取 itin
    │
    ▼
Leaflet 渲染：
  - 城市名 → Nominatim 逆地理 → [lat, lng]
  - Day 分段 → 不同颜色路线图层
  - POI → 自定义标记
```

### 后端新增

1. **`POST /api/geocode`** — 反向地理编码缓存代理（避免重复请求 Nominatim）
   ```json
   POST /api/geocode {"places": ["西安", "成都", "兵马俑"]}
   → {"西安": [34.3416, 108.9398], ...}
   ```

### 前端新增

1. **`static/map.js`** — Leaflet 地图组件
   - `initMap(containerId, data)` — 初始化地图
   - `addCityMarkers(cities)` — 城市大头针
   - `addRouteLine(cities, color)` — 路线连线
   - `addDayLayer(dayData, color)` — 单日路线
   - `switchDay(dayIndex)` — 切换显示某天

2. **聊天页面改造** — 检测到结构化行程后显示地图按钮/面板

### 性能考虑

- Nominatim 有每秒 1 请求限制 → 后端做缓存去重
- Leaflet 约 40KB gzipped，不影响页面加载
- 不会在地图上显示 50+ POI，控制单次 20 个以内

## 配色

沿用现有深色主题：
- 地图瓦片：CartoDB Dark Matter（暗色风格）
- 路线线：`#7dd3fc`（accent blue）
- 城市标记：`#38bdf8` 带呼吸动画
- Day 颜色：循环色盘 `#7dd3fc, #fbbf24, #f87171, #4ade80, #a78bfa`
