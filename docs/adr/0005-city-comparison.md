# 0005 — City Comparison Mode

**Status:** Accepted
**Date:** 2026-06-19

## Context

用户在规划中国行程时，最常遇到的决策问题是「去北京还是成都？」当前方案需要用户分别问两个城市，再自己对比。需要一种方式让用户一键看到多个城市的横向对比。

## Decision

- 后端新增 `GET /api/cities/compare?cities=beijing,chengdu` 端点
- 从现有 36-city 知识库 JSON 中聚合数据，返回结构：

```json
{
  "cities": ["北京", "成都"],
  "comparisons": {
    "budget_per_day": [500, 400],
    "best_season": ["春秋", "春秋"],
    "attractions_top3": [["故宫","长城","天坛"], ["大熊猫","宽窄巷子","都江堰"]],
    "food_highlights": ["烤鸭", "火锅"],
    "weather_summary": ["四季分明", "温和湿润"],
    "transport_hub": ["PEK/PKX", "CTU"]
  }
}
```

- 数据容错：知识库缺字段 → 返回 `null`，前端显示「暂无」
- 前端渲染为对比表格（响应式，移动端两列+横向滚动）
- Chat 中检测 `对比|vs|还是|compare` 关键词，自动触发对比

## Consequences

- ✅ 复用现有知识库，无新增数据采集
- ✅ 零依赖后端（纯 WSGI + JSON 读取）
- ✅ 容错设计保证不崩
- ⚠️ 对比维度固定（第一版不开放自定义增减维度）
- ⚠️ 知识库中部分城市缺少 best_season / budget 字段，UI 需优雅处理缺失
