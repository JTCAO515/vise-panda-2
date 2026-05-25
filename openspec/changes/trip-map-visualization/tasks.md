# 实现清单：行程地图可视化

## 1. 后端：地理编码 API

- [ ] 1.1 在 `api/index.py` 添加 `POST /api/geocode` 端点
  - [ ] 请求体：`{"places": list[str]}`
  - [ ] 缓存逻辑：内存 Dict，key=地名，value=[lat, lng]
  - [ ] Nominatim 调用：`https://nominatim.openstreetmap.org/search?q={place}&format=json&limit=1`
  - [ ] 节流：`time.sleep(1.2)` 间隔
  - [ ] User-Agent: `VisePanda/1.0`
  - [ ] 错误处理：单地名失败不影响其他
- [ ] 1.2 添加到 `vercel.json` 路由（如果未自动匹配）

## 2. 前端：Leaflet 地图组件

- [ ] 2.1 创建 `static/map.js`
  - [ ] `initMap(containerId)` — 初始化 Leaflet 地图
  - [ ] `loadCities(citiesData)` — 添加城市标记 + label
  - [ ] `loadRoute(routeData, color)` — 添加路线 Polyline
  - [ ] `loadPOIs(pois, icon)` — 添加 POI 标记
  - [ ] `switchDay(dayIndex)` — 显示/隐藏图层组
  - [ ] `fitBounds()` — 自适应缩放
- [ ] 2.2 Leaflet CSS 通过 CDN 引入：`https://unpkg.com/leaflet@1.9/dist/leaflet.css`
- [ ] 2.3 Leaflet JS 通过 CDN 引入：`https://unpkg.com/leaflet@1.9/dist/leaflet.js`
- [ ] 2.4 暗色瓦片配置：`https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`

## 3. 聊天页面集成

- [ ] 3.1 在 `page_chat()` HTML 中新增地图容器 `<div id="tripMap">`
- [ ] 3.2 检测 `trip_update` SSE 事件 → 请求 `/api/geocode` + 渲染地图
- [ ] 3.3 添加 Day 切换标签 UI
- [ ] 3.4 地图默认收起？按用户滚动到位置时展示

## 4. 分享页面集成

- [ ] 4.1 在 `page_share()` 中嵌入地图容器
- [ ] 4.2 分享页面只显示全部路线（无 Day 切换）

## 5. 测试与验证

- [ ] 5.1 本地启动 uvicorn 测试 geocode API
- [ ] 5.2 浏览器打开聊天页，发送行程相关的 prompt，观察地图渲染
- [ ] 5.3 移动端触摸操作验证
- [ ] 5.4 分享页面地图显示验证
- [ ] 5.5 Git commit + push
- [ ] 5.6 Vercel 部署验证

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `api/index.py` | +30 行（geocode 端点 + Nominatim 调用） |
| `static/map.js` | +200 行（新文件） |
| `api/index.py` : `page_chat()` | +10 行（地图容器 + JS 加载） |
| `api/index.py` : `page_share()` | +5 行（地图容器） |
