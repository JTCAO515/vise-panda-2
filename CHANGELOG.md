# Changelog

## v5.0.2 — 2026-06-19

### Added
- 新增 `tests/test_config_contract.py`，覆盖 `/api/health` 与 `/api/config` 的版本一致性及 `google_client_id` 行为
- 新增 `web/tests/auth-state.test.js`，覆盖 Tools 视图接入与导航结构存在性
- 正式接入 `Tools` 视图与导航入口，新增 `view-tools` 与 `tools-grid`

### Changed
- 版本号统一升级为 `v5.0.2`，同步到后端接口、前端展示和核心文档
- 前端通过 `/api/config` 动态注入 `google_client_id` 和版本信息

### Fixed
- 修复 `/api/config` 缺少 `google_client_id` 的问题
- 修复 Tools 相关代码存在但页面未接入的结构脱节问题

## v5.0.1 — 2026-06-19

### Added
- 后端与前端测试基座：新增 `tests/` 与 `web/tests/`，覆盖 auth/admin/trips/chat 关键契约与结构检查
- 方案文档：新增 `docs/2026-06-19-editorial-atlas-spec.md`、`docs/2026-06-19-tdd-implementation-plan.md`、`docs/2026-06-19-iteration-roadmap-text.md`
- 正式实施计划：新增 `docs/superpowers/plans/2026-06-19-vp-hermes-foundation-editorial-atlas.md`

### Changed
- 版本号统一为 `v5.0.1`，同步到后端 health/config、前端页头页脚与核心文档
- trips 模型新增 `content`，创建与读取行程时支持完整正文与旧数据回退

### Fixed
- 修复 auth/admin 鉴权失败时返回空 body，统一输出稳定 JSON 错误
- 修复注册 `display_name` 未持久化的问题，并让 `disabled` 用户无法登录
- 修复 admin 页面 token key 与主站不一致的问题，统一为 `vp_token`
- 修复聊天 `split` 流程中的 `typingId` 重赋值问题
- 修复聊天历史查看器与主聊天区重复使用 `chat-messages` id 的问题

## v4.0.5 — 2026-06-19

### Added
- B5: 签证材料包 MVP — `data/visa_policies.json`（美/英/澳/加/申根 5 国政策）
- B5: `api/visa.py` — `GET /api/visa/info` 查要求 + `POST /api/visa/generate` 生成行程单
- B5: 前端签证弹窗（工具箱🛂入口），选择国籍→查要求→生成标准行程单→复制
- B5: 行程自动填充最新 trip，不支持国家显示警告

## v4.0.4 — 2026-06-19

### Added
- B4: 熊猫导游表情系统 — SSE 流中根据关键词动态切换熊猫表情
- B4: 10 种情绪（😋美食/💰价格/🕶️景点/📌提示/😊开心/🤔思考/😅抱歉/🏨酒店/🚄交通）
- B4: 熊猫头像右下角弹出式情绪徽章 + CSS pop 动画
- B4: 流结束后自动恢复默认表情（🐼）

## v4.0.3 — 2026-06-19

### Added
- B3: 城市对比模式 — `GET /api/cities/compare?cities=a,b` 后端端点
- B3: 前端对比弹窗渲染（Vibe / Best Season / Budget / Highlights 横向对比）
- B3: Chat 中自动检测「对比北京和成都」「compare beijing chengdu」触发对比
- B3: 缺字段显示 N/A，不崩不藏

## v4.0.2 — 2026-06-19

### Added
- B2: Trip Timeline 可视化 — `web/trip-timeline.js` + `web/trip-timeline.css`
- B2: AI 行程回复自动渲染为垂直时间线卡片（按活动类型颜色编码）
- B2: 一键复制行程（Timeline 上的 Copy 按钮）

## v4.0.1 — 2026-06-19

### Added
- B1a: Auth 系统加固 — `POST /api/auth/logout` 端点（后端删除 token）
- B1a: 前端登出 → 调用后端 API 销毁 token + 清 localStorage + reload

### Changed
- 版本号从 v3.x → v4.0.1
