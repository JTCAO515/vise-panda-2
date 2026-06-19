# VisePanda TDD 实施计划

## 目标

在 `Editorial Atlas` 前端重构之前，先用 TDD 把项目主链路的结构性问题锁住。  
本计划遵循一个原则：

`没有先失败的测试，就不写生产代码。`

---

## 实施原则

### 原则 1

所有 P0/P1 修复都必须先写失败测试，再改实现。

### 原则 2

优先测试“真实行为”，不要只测 mock。

### 原则 3

先保护接口契约和状态流，再做视觉层重构。

### 原则 4

每完成一个小修复，就回归一次对应测试，不等到最后一起查。

---

## 当前必须先保护的风险

### 风险 1

鉴权失败时部分接口可能返回空 body，导致前端和测试端直接崩。

### 风险 2

聊天 `split` 主路径有运行时错误风险。

### 风险 3

admin 页面与主站 token key 不一致，导致管理后台无法稳定进入。

### 风险 4

trip 保存模型不完整，当前只能保存 preview。

### 风险 5

文档、接口、前端版本号与字段名已出现多源漂移。

---

## 测试分层

## 第一层：后端契约测试

工具建议：

- Python stdlib `unittest`
- `wsgiref` / 内部 handler 直接调用
- 独立测试数据库路径，避免污染现有数据

### 计划文件

#### 1. `tests/test_auth_contract.py`

覆盖：

- 注册成功
- 登录成功
- `me` 成功
- 未登录访问受保护接口时，返回稳定 JSON 错误
- `display_name` 在注册/登录/获取用户信息链路中表现一致

#### 2. `tests/test_admin_contract.py`

覆盖：

- `user` 访问 admin 接口被拒绝
- `ops` 可读 admin 数据
- `admin` 可编辑用户
- 删除用户返回稳定成功结构
- 不允许删除自己

#### 3. `tests/test_trips_contract.py`

覆盖：

- 创建 trip 时保存 `content` 与 `preview`
- 获取 trip 时保留完整内容
- owner 可删，非 owner 不可删
- `admin` 可跨用户删除

#### 4. `tests/test_config_contract.py`

覆盖：

- `/api/health` 版本存在
- `/api/config` 版本与 health 一致
- Google 配置字段在未配置/已配置时行为稳定

#### 5. `tests/test_chat_contract.py`

覆盖：

- `messages` 缺失时报错结构稳定
- FAQ 事件、split 事件、done 事件序列可被消费
- 发生异常时有可解析的错误输出

---

## 第二层：前端纯逻辑测试

在不引入复杂框架的前提下，优先把易错逻辑拆出做可测试函数。

工具建议：

- `node --test`
- 轻量模块化拆分

### 计划文件

#### 1. `web/tests/chat-stream.test.js`

覆盖：

- split 事件处理不会重新赋值常量
- token / image / faq / done 的处理顺序正确
- 消息容器选择逻辑不会误用错误节点

#### 2. `web/tests/auth-state.test.js`

覆盖：

- 统一 storage key
- 登录态读取一致
- admin 入口判断与角色逻辑一致

#### 3. `web/tests/view-registry.test.js`

覆盖：

- 每个 view 都存在唯一容器
- `tools` 若被导航，必须有实际 view
- 聊天主容器和聊天历史查看器容器 id 唯一

#### 4. `web/tests/timeline-parser.test.js`

覆盖：

- 多种 `Day N:` 格式都能解析
- bullet 内容能正确分类
- 空内容或非 itinerary 不会错误注入 timeline

---

## 第三层：结构性 smoke 检查

这部分不是完整 E2E，而是最小的防退化检查。

### 检查项

1. 首页能加载
2. 聊天页能打开且输入区可用
3. 登录后用户菜单正常显示
4. admin 可在合法角色下进入
5. trips 页面正常渲染
6. cities 页面正常渲染
7. map 页面正常渲染

---

## 代码修复顺序

## Phase 1：接口与鉴权收口

### 任务

1. 统一鉴权失败响应
2. 消除空 body 返回
3. 收口 admin / auth / trips 的成功与失败结构

### 先写失败测试

- 未登录访问 `/api/admin/users`
- 未登录访问 `/api/trips`
- 权限不足访问 admin 修改接口

### 通过标准

- 所有失败场景都返回稳定 JSON
- 测试端不再出现 `JSONDecodeError`

---

## Phase 2：聊天主链路修复

### 任务

1. 修 `split` 流程常量重赋值问题
2. 抽离聊天事件处理逻辑
3. 统一消息容器选择逻辑

### 先写失败测试

- 处理 split 事件时不报错
- 多 bubble 渲染顺序正确
- FAQ / image / token 共同出现时结构稳定

### 通过标准

- 聊天主链不因 split 中断
- DOM 容器不会误命中聊天历史面板

---

## Phase 3：auth 与 admin 一致性修复

### 任务

1. 统一 `vp_token`
2. 修复 admin 删除用户成功判断
3. 前后端统一 `ops` / `admin` 权限口径
4. 补齐 `display_name`
5. 登录校验 `status`

### 先写失败测试

- 主站登录后 admin 可读取 token
- `ops` 用户具备只读后台权限
- `disabled` 用户无法登录
- 注册时的 `display_name` 可以读回

### 通过标准

- 认证与后台行为对齐
- 用户状态真正生效

---

## Phase 4：trips 数据模型修复

### 任务

1. trips 表补 `content`
2. 列表保留 `preview`
3. 明细使用 `content`
4. 保持旧数据兼容

### 先写失败测试

- 创建 trip 后能取回完整内容
- preview 不影响详情内容
- 老数据缺 content 时有降级策略

### 通过标准

- trip 保存语义和用户认知一致

---

## Phase 5：版本与配置收口

### 任务

1. 建立单一版本源
2. 同步 `health`、`config`、前端显示
3. Google 配置从 `config` 正式注入

### 先写失败测试

- 版本字段一致
- `GOOGLE_CLIENT_ID` 缺失时前端行为可预期
- 配置存在时 GSI 初始化链稳定

### 通过标准

- 不再出现多版本号和假配置占位符

---

## Phase 6：视图结构整理

### 任务

1. 清理重复 id
2. 明确每个 view 的容器
3. 决定 Tools 页接入或下线
4. 收口 legacy `static/*` 与 `web/*` 的职责

### 先写失败测试

- 所有关键 id 唯一
- `navigate('tools')` 时有真实页面容器
- 页面结构对 mobile/desktop 都稳定

### 通过标准

- 前端结构可以承接视觉重构

---

## Phase 7：Editorial Atlas UI 落地

这部分仍然遵循“先测试结构，再改界面”。

### 结构性检查

#### 首页

- 必须有 Hero
- 必须有 Trust Layer
- 必须有城市专题区
- 必须有 Planner Entry

#### Chat

- 必须有清晰的消息舞台
- 必须有统一行动区
- 输入区在移动端可稳定使用

#### Cities

- 必须有筛选与专题卡结构

#### Trips

- 必须有 recent / saved 分层

#### Admin

- 必须有概览层和列表层

---

## 重构时的文件策略

### 现状问题

`web/app.js` 过大，已经同时承担：

- 视图路由
- 聊天流
- auth
- map
- trips
- modal
- settings

### 建议拆分

#### 第一批可拆

- `web/app-shell.js`
- `web/chat-client.js`
- `web/auth-state.js`
- `web/trips-view.js`
- `web/cities-view.js`
- `web/tools-view.js`

#### 第二批可拆

- `web/map-view.js`
- `web/admin-shared.js`
- `web/ui-kit.js`

### 注意

拆分本身也要走 TDD，不允许“先拆再看坏没坏”。

---

## 文档同步要求

每修完一个阶段，至少同步以下文档：

- `README.md`
- `HANDOFF.md`
- `CHANGELOG.md`

如果不做这一步，项目很快还会再次漂移。

---

## 完成标准

这份计划执行完成后，应达到：

1. 后端关键接口都有失败测试和成功测试
2. 前端关键状态流有最小逻辑测试
3. 主链路不再靠人工记忆维护
4. `Editorial Atlas` 可以在稳定底座上实施

---

## 建议的执行批次

### Batch A

- auth/admin 契约修复
- chat split 修复
- token key 统一

### Batch B

- display_name / status / trips content
- 版本与 config 收口

### Batch C

- 视图容器清理
- tools / PWA / legacy 结构决策

### Batch D

- 首页
- Chat
- Cities
- Trips
- Admin 的 `Editorial Atlas` 落地

---

## 下一步建议

如果进入实施阶段，应该从 `Batch A` 开始，不建议先做视觉页。
