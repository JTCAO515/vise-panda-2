# Changelog

## v5.0.9 — 2026-06-20

### Fixed
- Repaired the production sign-in trigger and hardened the frontend bootstrap path
- Added resilient image fallback handling for production-facing visuals
- Added loading/error shells so key views no longer feel unresponsive
- Restored mobile tab/navigation visibility on portrait layouts

### Docs
- Updated `README.md` and `HANDOFF.md` to record the Production Stability Pass release state
- Synced `api/index.py`, `web/index.html`, `web/app.js`, and `web/app.css` to `v5.0.9`

### Regression
- Ran `python3 -m unittest discover -s tests -v` — 14 backend tests passed
- Ran `node --test web/tests/*.test.js` — 28 frontend structure/stability tests passed
## v5.0.8 — 2026-06-19

### Added
- Expandable English-first toolkit detail sheets for packing, pricing, visa, phrases, and emergency guidance
- An English-only compatibility version of `static/i18n.js` so the legacy path can no longer fall back to Chinese UI copy
- Frontend structure checks for the new tool detail overlay and `v5.0.8`

### Changed
- The tools page now opens real detail sheets instead of acting like a mostly static index
- Visa and emergency toolkit content shown to users now reads in natural English
- README/HANDOFF were updated to English-first project documentation
- Unified backend `APP_VERSION`, visible frontend version, and release docs to `v5.0.8`

### Regression
- Ran `python3 -m unittest discover -s tests -v` — 14 backend tests passed
- Ran `node --test web/tests/*.test.js` — 19 frontend structure tests passed

## v5.0.7 — 2026-06-19

### Added
- 英文原生网站内容收口：城市、餐饮、住宿等运行时主数据改为自然英文表达
- 特殊地名与中文专属词采用 `English（中文）` 的显示格式
- 前端新增统一双语显示 helper，城市、地图点位、餐饮条目与比较视图改为更一致的英文主展示
- 前端结构测试同步更新到 `v5.0.7`

### Changed
- `/data/cities.json`、`/data/food.json`、`/data/hotels.json` 的用户可见文案改为英文原生
- `/api/cities.py` 的 summary/compare 默认值改为英文口径
- 统一后端 `APP_VERSION`、前端壳层显示与文档版本到 `v5.0.7`

### Regression
- 执行 `python3 -m unittest discover -s tests -v`，后端 14 项测试通过
- 执行 `node --test web/tests/*.test.js`，前端 18 项结构测试通过

## v5.0.6 — 2026-06-19

### Added
- Chat 新增 `chat-quick-scroll` 与 `chat-quick-scroll-btn`，支持更快回到最新消息
- Trips 卡片新增 `trip-card-mobile-head` 与 `trip-card-mobile-actions`，强化拇指优先的操作区
- Cities 新增 `cities-mobile-intro` 与 `city-card-caption`，提升手机端扫读节奏
- Tools 新增 `tools-mobile-gallery`、`tools-mobile-gallery-copy` 与 `tool-card-kicker`
- 前端结构测试新增对 `v5.0.6` 和移动端细化结构的校验

### Changed
- 手机端 Chat 输入区、快捷操作、Trips 卡片、Cities 浏览说明、Tools 画廊进行第二轮细化
- 统一后端 `APP_VERSION`、前端壳层显示与文档版本到 `v5.0.6`

### Regression
- 执行 `python3 -m unittest discover -s tests -v`，后端 14 项测试通过
- 执行 `node --test web/tests/*.test.js`，前端 18 项结构测试通过

## v5.0.5 — 2026-06-19

### Added
- 新增移动端竖屏结构钩子：`hero-content-portrait`、`hero-note-card-compact`、`planner-entry-card-compact`
- 新增 Chat 安全区结构：`chat-mobile-shell`、`chat-action-rail-mobile`、`chat-input-bar-safe`
- 新增竖屏优化相关声明：`data-scrollable="true"` 的 `cities-filter-rail`、`trips-atlas-mobile`、`tools-section-mobile`
- 前端结构测试新增对 `v5.0.5` 与手机端结构钩子的校验

### Changed
- 首页首屏压缩为更适合竖屏的单列节奏，CTA、metrics、note card 改为更稳定的手机布局
- Chat 输入区、action rail 与底部导航完成 safe-area 避让优化
- Cities filter rail 改为更适合拇指操作的横向滑动过滤条
- Trips / Tools 完成更适合单手浏览的卡片与留白调整
- 统一后端 `APP_VERSION`、前端壳层显示与文档版本到 `v5.0.5`

### Regression
- 执行 `python3 -m unittest discover -s tests -v`，后端 14 项测试通过
- 执行 `node --test web/tests/*.test.js`，前端 14 项结构测试通过

## v5.0.4 — 2026-06-19

### Added
- 首页新增 `hero-metrics` 与 `editorial-lead` 结构，强化 Editorial Atlas 的双栏叙事与指标信息层
- Cities 新增 `cities-filter-rail`，支持 `all / history / food / nature / urban` 过滤导轨
- Trips 新增 `trips-atlas-note`，为 recent / archive 结构提供更清晰的编辑式说明
- 前端结构测试新增对 `hero-metrics`、`editorial-lead`、`cities-filter-rail`、`trips-atlas-note` 与 `v5.0.4` 可见版本的校验

### Changed
- 首页、Cities、Trips 完成一轮受控视觉深化，增强 Atlas 化排版、信息节奏与卡片层次
- 统一后端 `APP_VERSION`、前端壳层显示与文档版本到 `v5.0.4`

### Regression
- 执行 `python3 -m unittest discover -s tests -v`，后端 14 项测试通过
- 执行 `node --test web/tests/*.test.js`，前端 10 项结构测试通过

## v5.0.3 — 2026-06-19

### Changed
- 同步 `README.md`、`HANDOFF.md`、`CHANGELOG.md`，将当前实现状态更新为 foundation 契约测试基座 + `Editorial Atlas` 首页/主页面结构推进到 `v5.0.3`
- 文档口径明确当前活跃持久化链路为 `api/auth.py` 中的 SQLite（auth / session / trips / chat history）
- 文档补充 Atlas 结构落地点：`Home` 的 Hero / Trust Layer / City Rail / Planner Entry，`Chat` 的 action rail，`Trips` 的 recent/saved 分组，`Tools` 主导航接入，以及 `Admin` overview hero

### Docs
- README 改写为当前前端主结构与回归入口说明，避免继续沿用旧版模块清单
- HANDOFF 收口为当前真实架构说明，并同步到统一后的 `v5.0.3` 版本口径

### Regression
- 按 Task 10 执行 `python3 -m unittest discover -s tests -v`，14 项后端契约测试通过
- 按当前前端测试集执行 `node --test web/tests/*.test.js`，8 项前端结构测试通过

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
