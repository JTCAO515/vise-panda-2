# VisePanda 高风险文件修改指南

## 1. 文档目的

这份文档帮助新接手开发者识别高风险文件，理解为什么危险，以及修改前后至少要确认什么。

## 2. `web/app.js`

### 负责什么

当前前端主逻辑入口，负责 bootstrap、auth、chat、cities、trips、tools、view navigation。

### 为什么危险

这是当前最重的前端文件，多个功能耦合在一起，小改也可能影响多个视图。

### 修改前先确认什么

- 改动是否涉及 nav / auth / bootstrap
- 是否会影响已有 view state
- 是否有对应前端测试

### 修改后至少测什么

- `node --test web/tests/*.test.js`
- 首页 / Chat / Cities / Trips / Tools

## 3. `api/auth.py`

### 负责什么

当前活跃的登录、session、profile、trip、chat history、admin 数据链路。

### 为什么危险

登录、用户态和历史记录都依赖它，改错容易产生连锁问题。

### 修改前先确认什么

- 是否改动响应字段、token 读取或用户态恢复逻辑
- 是否触碰 SQLite schema、初始化、`AUTH_DB_PATH` 或 Vercel `/tmp` 行为
- 是否会同时影响 trips、chat history、admin 共用查找链路

### 修改后至少测什么

- `python3 -m unittest discover -s tests -v`
- 注册 / 登录 / `/api/auth/me` / Trips / Chat History / Admin 基本链路

## 4. `web/app.css`

### 负责什么

当前主样式系统，覆盖桌面端、移动端、底部导航、overlay、安全区和稳定性补丁。

### 为什么危险

它直接决定 header、bottom nav、chat 容器和各 view 的布局，小样式改动也可能让移动端被遮挡或交互失效。

### 修改前先确认什么

- 是否影响 `--header-h`、`--bottom-nav-safe`、safe-area 或 `.bottom-nav`
- 是否改动 chat、modal、overlay、view 容器的尺寸关系
- 是否存在桌面与移动端断点差异

### 修改后至少测什么

- `node --test web/tests/*.test.js`
- 桌面 header/nav、移动端 bottom nav、chat 输入区、安全区留白

## 5. `web/index.html`

### 负责什么

当前唯一主站 SPA 壳层，包含 header、各 view 容器、聊天区、Trips、Cities、Tools、认证弹层和移动端 overlay 挂载点。

### 为什么危险

`web/app.js` 大量依赖这里的 DOM 结构、element id 和按钮触发，结构名或层级变化会直接破坏运行时行为。

### 修改前先确认什么

- 是否改动了 `id`、`data-view`、认证区、聊天输入区或关键容器层级
- 是否会影响 `web/app.js` 里的 DOM 查询与事件绑定
- 是否仍然保留 `app.css`、`app.js`、`trip-timeline.js` 的加载关系

### 修改后至少测什么

- `node --test web/tests/*.test.js`
- 首屏加载、导航切换、Sign In、Chat 输入、Cities / Trips / Tools 容器显示

## 6. `api/chat.py`

### 负责什么

SSE 流式聊天出口，负责 FAQ 匹配、system prompt 构建、图片标记拆出和 DeepSeek 调用。

### 为什么危险

这里同时承担模型请求、流式事件格式和前端消费契约，轻微格式变化都可能让聊天 UI、FAQ badge 或图片渲染失效。

### 修改前先确认什么

- 是否改动 SSE event 类型、`done` 事件、错误事件或 token 输出格式
- 是否会影响 FAQ 匹配、图片标记 `[img:...]` 或 system prompt 拼装
- 是否确认环境变量 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL` 的兼容逻辑

### 修改后至少测什么

- `python3 -m unittest discover -s tests -v`
- Chat 流式输出、FAQ 命中、图片消息、异常时错误返回

## 7. `api/index.py`

### 负责什么

WSGI 路由总入口，负责 `/api/*` 分发、`/admin` 页面回退和静态文件兜底。

### 为什么危险

这里的路由顺序本身就是契约，catch-all 或兜底位置一旦变化，多个接口会一起回归。

### 修改前先确认什么

- 是否保持 `/api/cities/compare` 先于 `/api/cities` catch-all
- 是否改变 auth/admin/chat/config/static fallback 的优先级
- 是否会影响 `/admin` 与静态资源返回关系

### 修改后至少测什么

- `python3 -m unittest discover -s tests -v`
- `/api/health`、`/api/chat`、`/api/cities/compare`、`/api/config`、`/admin`

## 8. 相对安全的改动区

- 低风险文案修正
- 非核心展示层样式
- 某些独立数据文件
- 非主链路工具文案
- 不改 DOM 契约的静态说明文字
- 已有测试覆盖下的小范围空状态或错误提示优化
