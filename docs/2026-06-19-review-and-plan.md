# VP-Hermes-Web 深度审查与改造方案

## 结论摘要

这个仓库已经具备可运行产品雏形，但当前最大问题不是“功能少”，而是“真实实现、项目文档、前端入口、认证链路、管理后台、测试体系”之间已经明显漂移。  
如果不先把基础层收口，继续叠功能只会让后面的迭代成本越来越高。

最优先处理的不是新功能，而是以下四类问题：

1. 统一真实架构与文档口径
2. 修复聊天流、管理后台、认证链路中的可复现断点
3. 建立最小 TDD 回归保护
4. 在不破坏 Panda × China 品牌识别的前提下，重做前端信息层级与视觉系统

---

## 深读后确认的项目现状

### 真实架构

- 后端是 `api/index.py` 做入口，实际分发到 `api/auth.py`、`api/chat.py`、`api/cities.py`、`api/tools.py`、`api/visa.py`、`api/config.py`
- 前端是 `web/index.html` + `web/app.js` + `web/app.css` 的 Vanilla SPA
- 数据层主体是本地 JSON + SQLite
- 会话是随机 token + `sessions` 表，不是 JWT
- 用户、trip、chat history 都在 `api/auth.py` 维护

### 和文档不一致的地方

- `HANDOFF.md` 多处写 `Supabase Postgres + JWT`，但代码实际是 SQLite + session token
- `README.md`、`CHANGELOG.md`、`api/config.py`、`api/index.py`、`web/index.html` 的版本号彼此不一致
- 文档写有 `view-tools` 与工具页入口，但页面里并不存在对应 view/container
- 历史文档里仍保留 `GLM`、`api/main.py`、`Supabase`、`SQLAlchemy` 等旧架构信息

---

## 对抗性 coding review

## P0

### 1. 多 bubble 聊天在 split 事件上会直接崩

证据：
- `web/app.js` 中 `typingId` 被声明为 `const`
- 同一流程里又执行 `typingId = newId`

影响：
- 只要后端返回 `split` 事件，多段回答功能就可能直接抛出 `Assignment to constant variable`
- 这是核心主路径故障

修复：
- 将该变量改为可重新赋值的 `let`
- 增加 split 事件回归测试

### 2. 管理后台 token key 和主站不一致

证据：
- 主站使用 `localStorage['vp_token']`
- `web/admin.html` 读取的是 `localStorage['vp_auth_token']`

影响：
- 用户从主站进入 admin 页面时，大概率被误判为未登录

修复：
- 统一成单一 key
- 补一条前端 auth-state 回归用例

### 3. admin 删除用户成功后，前端仍可能提示失败

证据：
- `web/admin.html` 判断 `data.success`
- `api/auth.py` 删除接口返回 `{ "message": "User deleted", "user_id": ... }`

影响：
- 删除行为成功但前端 toast 失败，造成操作结果错觉

修复：
- 统一响应契约，推荐后端统一返回 `ok: true`
- 或前端以 `res.ok` / `message` 判定

### 4. middleware 鉴权失败时，多处接口会返回空 body

证据：
- `require_auth()` / `require_role()` 内部调用 `_json_error(...)`
- 外层路由在 `user is None` 时直接 `return []`
- `api/test_auth.py` 运行到 admin list 时已实际触发 `JSONDecodeError`

影响：
- 客户端会收到状态码但没有 JSON body
- 前端/测试脚本都可能因为空响应体崩掉

修复：
- 鉴权函数返回标准响应对象，而不是先写响应再交给上层空返回
- 或统一抛出异常，由 router 收口成 JSON 错误

### 5. 默认 admin 弱口令硬编码

证据：
- `api/auth.py` 中默认 admin email/password 有硬编码 fallback

影响：
- 线上环境一旦忘记覆写环境变量，风险很高

修复：
- 生产环境强制要求配置
- 未配置时拒绝初始化默认 admin

---

## P1

### 6. 页面里存在重复 `id="chat-messages"`

证据：
- `web/index.html` 主聊天区一个
- My Chats viewer 里又一个

影响：
- 依赖 `getElementById('chat-messages')` 的逻辑可能命中错误容器
- 聊天记录查看器和主聊天区互相污染

修复：
- 所有聊天容器 id 唯一化
- 抽象容器选择函数，不再依赖全局重复 id

### 7. 注册的 `display_name` 实际没有落库

证据：
- 前端注册会提交 `display_name`
- `handle_register()` 只读取 email/password

影响：
- 注册昵称是假字段
- 用户感知为“注册成功但资料不生效”

修复：
- 后端补入 `display_name`
- 登录与 `me` 响应都要返回它

### 8. 用户 `status` 被设计出来了，但登录并未校验

证据：
- `users` 表有 `status`
- admin 统计也按 `status` 聚合
- `handle_login()` 查询用户时没有校验 `status`

影响：
- `disabled`/`pending` 用户仍可能正常登录

修复：
- 登录、Google 登录、`me` 都应校验状态
- UI 给出明确提示

### 9. trips 只保存 preview，不保存完整 itinerary

证据：
- trips 表只有 `preview`
- 前端保存时也只传截断内容

影响：
- 登录用户重新打开 trip 时，只能看到被截断版本
- “保存行程”名义上成立，实际上无法完整恢复

修复：
- trips 表新增 `content`
- preview 仅用于列表摘要

### 10. Google 登录前端链路未真正打通

证据：
- `web/index.html` 仍是 `PENDING_GOOGLE_CLIENT_ID`
- 前端没有把真实配置注入 GSI 组件

影响：
- 后端虽有 `/api/auth/google/login`，但前端无法稳定使用

修复：
- `GET /api/config` 返回 `google_client_id`
- 前端初始化时动态注入 GSI

### 11. `/api/config` 版本号还是旧值

证据：
- `api/index.py` `/api/health` 返回 `4.1.2`
- `api/config.py` 返回 `3.2.0`

影响：
- 客户端显示和真实版本错位

修复：
- 把版本提取为单一常量源

---

## P2

### 12. Tools 相关代码存在，但页面没有接入

证据：
- `web/app.js` 有 `loadTools()` / `navigate('tools')`
- `web/index.html` 没有 `view-tools` / `tools-grid`

影响：
- 代码和产品入口脱节
- 文档说有工具箱，但用户看不到

修复：
- 要么正式接上工具页
- 要么先删掉死代码与文档描述

### 13. PWA 只做了一半

证据：
- 有 `manifest.json` 和 `sw.js`
- 没看到清晰的 service worker 注册链
- `static/sw.js` 与 `web/sw.js` 双份残留

影响：
- 看起来支持安装，实际离线与缓存行为不稳定

修复：
- 保留唯一 service worker 实现
- 加入注册、更新、回退策略

### 14. `weather.py` 使用 `httpx`，与“stdlib only”承诺冲突

证据：
- `requirements.txt` 仍写无外部依赖
- `api/weather.py` 直接 `import httpx`

影响：
- 真实约束与宣传口径不一致

修复：
- 要么改为 `urllib`
- 要么承认并补依赖声明

---

## 优化方案

### 架构收口

1. 建立单一版本源
2. 建立单一 auth state 源
3. 明确主线数据模型：`user`、`session`、`trip`、`conversation`
4. 删除或归档废弃入口：旧 `static/*`、未接入的 tools/PWA 残留
5. 让文档只保留“当前真实实现”和“未来目标”，不要混写

### 接口契约收口

1. 所有 API 统一返回 `{ ok, data, error }` 或稳定等价结构
2. 鉴权失败一定返回 JSON，不允许空 body
3. 所有写接口返回一致的成功语义
4. 前后端统一字段：`display_name`、`status`、`content`、`preview`

### 前端状态收口

1. 建立集中式 `authStore`
2. 建立集中式 `viewRegistry`
3. DOM 节点 id 唯一化
4. 将聊天流、admin、trip、modal 相关逻辑从超大 `app.js` 拆分

---

## 前端美化方案

推荐方向：**Editorial Atlas / 旅行志式中国地图册**

理由：
- 和现有 Panda × China 品牌最契合
- 能保留文化气质，但不落入“旅游模板站”俗套
- 适合承载城市卡片、地图、行程时间线、工具箱四类内容

### 视觉关键词

- 编辑感
- 深色墨黑底
- 朱砂红主 CTA
- 铜金信息锚点
- 大幅城市摄影 + 薄雾纹理 + 地图坐标感
- 更克制但更高级的动效

### 落地改造点

1. Header 重做为“品牌栏 + 任务入口 + 用户态”三段结构
2. Hero 从 emoji 堆叠升级为“主标题 + 城市带状拼贴 + 搜索/开始规划双 CTA”
3. 首页加一层“为什么信任它”的结构：36 城市、签证、价格、行程时间线
4. 城市卡片从统一网格升级为大小错落的 editorial masonry
5. Chat 区域改成更清晰的左右层级：历史/消息/行动条
6. Map 页做成“总览地图 + 城市摘要抽屉”结构
7. Trips 页增加进度感与封面摘要，不再像纯文本列表
8. Admin 单页从“纯表格”升级为“概览 + 用户列表 + 明细抽屉”

### 不建议做的事

- 不建议继续使用大量 emoji 作为主视觉骨架
- 不建议再往 `app.js` 里直接堆视觉逻辑
- 不建议只调颜色不调信息架构，那样只是“换皮”

---

## 可选视觉路线

### A. Editorial Atlas（推荐）
- 最强品牌识别
- 最适合旅行产品
- 需要重做首页、城市卡、地图页层级

### B. Refined Ink Glass
- 保留现有结构，重点升级质感与排版
- 风险最小
- 适合先做一轮快速上线

### C. Map-first Planner
- 以地图和 itinerary 为主舞台
- 更偏工具型
- 更适合“行程生成器”而不是“旅行灵感产品”

---

## TDD 实施计划

### Phase 1：先给断点上护栏

先写失败测试，再改代码。

#### 后端测试

建立 `tests/`，优先用 Python stdlib `unittest`：

1. `test_auth_register_login.py`
   - 注册成功
   - 登录成功
   - disabled 用户不可登录
   - display_name 正确返回

2. `test_admin_routes.py`
   - user 访问 admin 返回稳定 JSON 错误
   - ops 可读，admin 可写
   - 删除用户响应契约一致

3. `test_trips_api.py`
   - trip 保存完整 content
   - preview 仅做摘要
   - 仅 owner/admin 可删

4. `test_config_version.py`
   - `/api/health`、`/api/config`、前端注入版本一致

#### 前端测试

对于纯逻辑部分，拆出可测试函数，再写 `node --test` 级别测试：

1. 聊天流 split 处理
2. auth storage key 一致性
3. view 注册与容器存在性
4. timeline parser 对典型 itinerary 的解析

### Phase 2：按风险顺序修

顺序建议：

1. 修 auth middleware 空 body
2. 修聊天 split 崩溃
3. 修 admin token key / delete 判定 / ops 权限
4. 修 display_name / status / Google config
5. 修 trips content 模型
6. 修版本单一来源
7. 接上 tools / 清理死代码 / 统一 PWA

### Phase 3：视觉重构也走 TDD 思路

前端视觉不是传统单元测试主场，但仍然可以先写“结构性失败检查”：

1. 首页必须存在 hero、trust strip、city rail、CTA group
2. 所有交互 view 必须有唯一容器
3. keyboard focus 不丢
4. mobile 下 header、bottom nav、chat input 不重叠

### Phase 4：回归门槛

每次提交前至少跑：

1. Python 测试全绿
2. 关键前端逻辑测试全绿
3. 本地 smoke：首页、聊天、登录、admin、trip、cities、map
4. 无版本号错位

---

## 后续迭代方案

### Iteration A：把产品先变“可信”

目标：
- 修复基础断点
- 清理文档漂移
- 建立测试护栏

交付重点：
- auth/admin/chat/trips 主链路稳定
- README/HANDOFF/CHANGELOG 与代码一致
- 版本统一

### Iteration B：把产品从“能跑”变成“好用”

目标：
- 完成前端信息架构重构
- 补齐工具页、PWA、Google 登录
- 提升 itinerary 可读性与操作感

交付重点：
- 新首页
- 新城市页
- 新 trips 体验
- 新 admin 信息层级

### Iteration C：把产品从“好用”变成“值得回来”

目标：
- 增加用户复访和留存理由

建议方向：
- 行前 checklist / packing timeline
- 城市对比结果收藏
- trip share/export
- post-trip feedback
- 季节性专题内容页

### Iteration D：把产品从“工具”变成“差异化品牌”

建议方向：
- Panda persona 强化，但从“表情”走向“导游人格”
- 旅行叙事卡片、可分享长图
- 行程可信度解释层
- 更丰富的签证/预算/区域路线决策辅助

---

## 我建议的执行顺序

1. 先修 P0 和 P1，不动大视觉
2. 再做一次结构性前端重构
3. 最后做视觉升级与体验润色

如果顺序反过来，项目会进入“视觉漂亮但主链不稳”的状态。

---

## 下一步建议

如果继续由我执行，最合理的是：

1. 先确定前端改版风格方向
2. 我按 TDD 补第一批失败测试
3. 先修 P0/P1
4. 再开始首页、聊天、城市、trip 的视觉重构
