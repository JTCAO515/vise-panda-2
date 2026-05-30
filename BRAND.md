# VisePanda 品牌资产与使用规范（YS Panda）

本文件定义 VisePanda 的基础品牌资产、尺寸与使用建议，保证 Landing / Chat / Share / PWA 的视觉一致。

## 1. 主要 Logo

- 主图标：`static/img/logo-1024.png`（透明背景）
- 常用尺寸：
  - `static/img/logo-512.png`
  - `static/img/logo-192.png`（PWA / apple-touch-icon 推荐）
  - `static/img/logo-64.png` / `static/img/logo-32.png`（站内 UI / favicon 辅助）

## 2. Favicon

- `static/img/favicon.ico`
- 路由：`/favicon.ico`（由后端返回该文件）

## 3. Open Graph 分享图（OG）

- `static/img/og-image.png`（1200×630）
- Landing 的 `og:image` 指向该文件，用于社交分享卡片预览。

## 4. 使用原则

1) **优先使用透明底 PNG**：确保在深色背景下更干净。  
2) **留白**：Logo 周围建议至少保留图标宽度的 12% 作为安全区。  
3) **避免拉伸**：只等比缩放。  
4) **深色背景优先**：当前 UI 为深色风格，Logo 线条与霓虹色更突出。

## 5. 开发提示

- 如遇浏览器缓存导致图标不更新，请强制刷新（Ctrl+F5 / Cmd+Shift+R），或清除站点缓存与 Service Worker。

