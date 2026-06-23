# ViseBits 动画组件

> 从 React Bits 适配的 5 个动画组件（vanilla JS，无框架依赖）

---

## 1. Aurora Hero（极光光束背景）

**文件：** `web/visebits.js` — `AuroraHero` 类

**位置：** Hero 区 Canvas

**效果：** 动态流动的极光光晕 + 射线光束

**参数：** 自动适应容器大小

**性能：** 使用 `devicePixelRatio` 缩放 Canvas，降低绘制负载

---

## 2. Tilted Card（3D 倾斜卡片）

**文件：** `web/visebits.js` — `TiltedCard` 类

**应用：** 所有 `.city-card` 元素

**效果：**
- 鼠标移入：3D 透视倾斜（`perspective: 1000px`）
- 跟随鼠标位置旋转，最大 `8°`
- Hover 时放大 `1.02x`
- 可选光泽/眩光层

**注意：** 触摸设备自动禁用（`pointer: coarse` 检测）

---

## 3. Spotlight Card（聚光灯卡片）

**文件：** `web/visebits.js` — `SpotlightCard` 类

**应用：** 所有 `.city-card` 元素

**效果：**
- 鼠标移入：径向渐变跟随鼠标
- 渐变中心 = 鼠标位置
- 颜色：`--brand` (rgba 14,165,233) 微光

---

## 4. Count Up（数字滚动动画）

**文件：** `web/visebits.js` — `CountUp` 类

**应用：** `[data-vise-countup]` 属性标记

**效果：**
- IntersectionObserver 监听进入视口
- 进入后从 0 滚动到目标值
- Ease-out cubic 缓动
- 支持后缀、前缀、小数位

**HTML 示例：**
```html
<div data-vise-countup="36" data-vise-duration="2000" data-vise-suffix="+"></div>
```

---

## 5. Splash Cursor（点击粒子飞溅）

**文件：** `web/visebits.js` — `SplashCursor` 类

**应用：** 全局

**效果：**
- 点击任意位置 → 色彩粒子向四周飞溅
- 12 个粒子，800ms 生命周期
- 颜色池：品牌色 + 点缀色
- 受重力影响，自然下落

**注意：** 固定定位 Canvas，`pointer-events: none`，不干扰交互
