<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-25T12:18:30+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_role_home/requirements/requirements_spec.md</file><file>project_workspace/ocap_role_home/requirements/user_stories.md</file><file>project_workspace/ocap_role_home/architecture/architecture_design.md</file><file>frontend/src/portal/Home.vue</file><file>frontend/src/stores/auth.js</file><file>frontend/src/shared/style.css</file><file>miniprogram/pages/index/index.vue</file><file>miniprogram/store/auth.js</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 模块设计（增量）

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-215 | Web 身份能力派生 | 修改 `frontend/src/stores/auth.js` | 从 `/me` 派生委员/代表/户主/游客能力 | REQ-FUNC-366、367、368、369、370、372；US-354~359 | — |
| MOD-216 | Web 首页角色化编排 | 修改 `frontend/src/portal/Home.vue` | 计算模块清单与数据计划，按档案渲染并控制请求 | REQ-FUNC-366~374；US-354~359 | MOD-215、MOD-217 |
| MOD-217 | Web 首页共享骨架样式 | 修改 `frontend/src/shared/style.css`；按需修改 `themes/*.theme.json` 并重生成 `frontend/src/theme/generated/themes.css` | 统一 4 栏 Bento 骨架与模块占位，删除统计卡样式 | REQ-FUNC-374、375；US-360 | — |
| MOD-218 | 小程序身份能力派生 | 修改 `miniprogram/store/auth.js` | 与 MOD-215 同口径的能力 getter | REQ-FUNC-366、367~372；US-354~359 | — |
| MOD-219 | 小程序首页角色化编排 | 修改 `miniprogram/pages/index/index.vue` | 单列卡片流的模块顺序、空态与按能力请求 | REQ-FUNC-366~375；US-354~360 | MOD-218、主题生成物 |

## 模块详情

### MOD-215 Web 身份能力派生（修改现有）

- 文件：`frontend/src/stores/auth.js`（现有 getter：`isCommittee`、`isChairOrVice`、`identitySummary`，见 `frontend/src/stores/auth.js:7-18`）。
- 职责：只读派生能力，不改变登录/登出行为。
- 接口 IFC-436（前端契约，JSDoc/TS 类型）：

```ts
type UnitRole = 'HEAD' | 'OWNER' | 'RESIDENT'
interface UnitIdentity { role: UnitRole; /* 其余字段沿用 /me */ }

// useAuthStore().getters
interface WebAuthCapabilities {
  isGuest: boolean            // me.identities.is_guest === true
  position: '' | 'CHAIR' | 'VICE_CHAIR' | 'MEMBER' | 'REPRESENTATIVE'
  isCommittee: boolean        // CHAIR | VICE_CHAIR | MEMBER
  isRepresentative: boolean   // position === 'REPRESENTATIVE'
  isChairOrVice: boolean
  ownerUnits: UnitIdentity[]  // units.filter(u => u.role === 'HEAD' || u.role === 'OWNER')
  hasOwnerUnit: boolean       // ownerUnits.length > 0
  residentUnits: UnitIdentity[] // units.filter(u => u.role === 'RESIDENT')
  hasResidentUnit: boolean
}
```

- 鉴权方式：无（纯内存计算，数据源为已鉴权的 `GET /me`）。
- 输入校验：`me` 为空时全部返回安全默认值（`isGuest: false`、数组为空）。
- 依赖模块：无。

### MOD-216 Web 首页角色化编排（修改现有）

- 文件：`frontend/src/portal/Home.vue`（现有 Hero/待办/统计卡/账户/快捷/投票/决议，`frontend/src/portal/Home.vue:2-107`）。
- 职责：生成模块清单与数据加载计划；模板只消费清单；移除 4 张统计卡、Hero 计数徽章与快捷宫格。
- 接口 IFC-437（模块视图模型）：

```ts
type HomeModuleKey =
  | 'welcome' | 'housing' | 'pendingReview' | 'pendingVotes' | 'pendingTasks'
  | 'finance' | 'management' | 'polls' | 'resolutions' | 'info'

type HomeModuleKind = 'content' | 'task'   // content 恒渲染（含空态）；task 数量 0 不渲染

interface HomeModule {
  key: HomeModuleKey
  kind: HomeModuleKind
  title: string          // 数量只在此处出现一次，如 “待我处理 · 2”
  count: number | null   // 仅 task/content 有计数时使用
  to: string             // 模块级跳转路由
  emptyText?: string     // content 类空态文案
}
```

- 模块顺序（ADR-196，逐角色满足 AC）：

| 档案（判定顺序） | 顺序 |
|---|---|
| committee（含兼代表/户主） | welcome → housing → [pendingTasks] → [pendingVotes] → [pendingReview] → finance → management → polls → resolutions → info |
| representative | welcome → housing → [pendingVotes] → [pendingReview] → polls → resolutions → finance → info |
| owner | welcome → housing → [pendingReview] → polls → resolutions → info → finance |
| resident | welcome → housing → polls → resolutions → info → finance |
| guest | welcome → resolutions → polls → info → finance |

说明：`[pendingTasks]` 仅 `isCommittee && tasks.length > 0`；`[pendingVotes]` 仅 `isRepresentative && openRepVotes.length > 0`；`[pendingReview]` 仅 `hasOwnerUnit && pendingReviewCount > 0`；`housing` 仅 `units.length > 0`；`management` 仅 `isCommittee`。三个任务模块固定按 `pendingTasks → pendingVotes → pendingReview` 排序。

- 接口 IFC-438（公开决议双来源）：

```ts
type ResolutionSource = 'COMMITTEE' | 'REPRESENTATIVE'
interface PublicFeedItem {
  id: number
  title: string
  source: ResolutionSource
  statusText: string        // 决议 status 或投票 CLOSED
  to: string                // /resolutions/{id} 或 /polls/{id}
}
// loadPublicFeed(limit=5): Promise<PublicFeedItem[]>  // 合并后按 created_at/deadline 倒序取前 limit
```

- 接口 IFC-439（待我表决）：

```ts
interface PendingVoteItem {
  id: number
  title: string
  deadline: string
  participation: 'VOTED' | 'NOT_VOTED' | 'UNKNOWN'  // 详情失败降级 UNKNOWN
  to: string
}
// loadPendingVotes(openRepPolls, limit=3): Promise<PendingVoteItem[]>
// 只对前 limit 条并发 GET /polls/{id}，Promise.allSettled 容错，不展示参与率
```

- 接口 IFC-440（数据加载计划）：

```ts
interface HomeDataPlan {
  me: true
  housing: boolean          // hasOwnerUnit
  approvalTasks: boolean    // isCommittee
  polls: true
  pollDetails: number[]     // isRepresentative 时前 3 条 OPEN+REP_VOTE 的 id
  resolutions: true
  accounts: true            // 所有登录用户：合计 + 报表入口
  info: true
}
```

- 鉴权方式：全部复用现有登录令牌（`IsMember` / `IsCommitteeMember`，见 HTTP 契约表）。
- 输入校验：响应既可能是分页对象 `{ results: T[] }`，也可能是数组；统一取 `data.results || data || []`（沿用现有写法，`frontend/src/portal/Home.vue:209,226,233`）。
- 依赖模块：MOD-215（能力）、MOD-217（样式类名）。

### MOD-217 Web 首页共享骨架样式（修改现有）

- 文件：`frontend/src/shared/style.css`（现有 `.home-grid`、`.home-hero`、`.home-quick*`、`.stat-*`，`frontend/src/shared/style.css:178-219`）。
- 职责：定义 Web 首页 4 栏骨架与模块占位；删除统计卡与快捷宫格相关样式（如无其他页面引用）；三主题只覆盖颜色/圆角/动效。
- 接口 IFC-441（样式契约）：

```css
/* 类名契约（GROUP_C 实现时必须保留，测试据此断言） */
.home-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(120px, auto); }
.home-hero   { grid-column: span 4; }
.home-wide   { grid-column: span 2; }   /* 财务、公开决议等 */
.home-full   { grid-column: span 4; }   /* 投票、信息公开等 */
/* 删除：.home-stat / .home-quick / .home-metrics 的计数徽章 */
@media (max-width: 767px) { .home-grid { grid-template-columns: 1fr; } .home-wide, .home-full, .home-hero { grid-column: span 1; } }
```

- 鉴权方式：不适用（静态样式）。
- 输入校验：不适用。
- 依赖模块：无；被 MOD-216 使用。

### MOD-218 小程序身份能力派生（修改现有）

- 文件：`miniprogram/store/auth.js`（现有 `isCommittee`、`identitySummary`，`miniprogram/store/auth.js:6-12`）。
- 职责：与 MOD-215 同口径的 getter。
- 接口 IFC-442：

```ts
interface MiniAuthCapabilities {
  isCommittee: boolean
  isRepresentative: boolean
  hasOwnerUnit: boolean
  isGuest: boolean
  ownerUnits: UnitIdentity[]
}
```

- 鉴权方式：无；输入校验（`me` 为空）同 MOD-215。
- 依赖模块：无。

### MOD-219 小程序首页角色化编排（修改现有）

- 文件：`miniprogram/pages/index/index.vue`（现有徽章/待办/统计宫格/认证房屋/快捷/投票/决议，`miniprogram/pages/index/index.vue:3-70`）。
- 职责：与 Web 相同的模块 key 与顺序，单列卡片流；移除统计宫格与 Hero 计数徽章；任务 0 隐藏、内容空态保留。
- 接口 IFC-443（小程序模块视图模型）：

```ts
type MiniHomeModule = {
  key: HomeModuleKey            // 与 MOD-216 同名同序
  kind: 'content' | 'task'
  title: string
  count: number | null
  to: string
  emptyText?: string
}
// miniHomeModules(caps, data): MiniHomeModule[]
```

- 接口 IFC-444（数据加载计划）：与 IFC-440 同字段；请求经 `miniprogram/utils/api.js` 的 `api.me/housing/tasks/polls/poll/resolutions/accounts/infoPosts`（`miniprogram/utils/api.js:12,14,47,50,51,58,64,69`）。
- 鉴权方式：复用小程序现有令牌与 `GET` 权限。
- 输入校验：同 IFC-440 的响应归一化。
- 依赖模块：MOD-218。

## HTTP 契约（复用现有接口，无新增）

| 接口 | 方法与路径 | 鉴权（现有） | 请求 | 使用字段 | 错误与降级 | 触发条件 |
|---|---|---|---|---|---|---|
| IFC-445 | `GET /me` | `IsMember` | 无 | `identities.units[].role`、`committee.position`、`is_guest`、`summary` | 401 由 http 层跳登录；失败显示“加载失败，请重试” | 恒调用 |
| IFC-446 | `GET /me/housing` | `IsMember`（`backend/apps/residency/views.py:82-84`） | 无 | `pending_review_count` | 失败按 0；不发请求则不发 | 仅 `hasOwnerUnit` |
| IFC-447 | `GET /approval/tasks` | `IsCommitteeMember`（`backend/apps/approval/views.py:220-221`） | 无 | `instance_id`、`title/subject_title`、`scope`、`submitted_at` | 403/失败按空；不发请求则不发 | 仅 `isCommittee` |
| IFC-448 | `GET /polls` | `IsMember`（`backend/apps/polls/views.py:31-37`） | 无 | `id`、`kind`、`title`、`status`、`deadline`、`created_at` | 失败保留空态 | 恒调用 |
| IFC-449 | `GET /polls/{id}` | `IsMember`（`backend/apps/polls/views.py:125-127`） | 无 | `can_respond`、`my_response` | 单条失败标 `UNKNOWN` | 仅代表前 3 条 OPEN REP_VOTE |
| IFC-450 | `GET /resolutions?scope=public&page_size=5` | `IsMember`（`backend/apps/resolutions/views.py:77-81`） | 查询参数 | `id`、`title`、`status` | 失败保留空态 | 恒调用 |
| IFC-451 | `GET /ledger/accounts/summary?status=ENABLED&recent=0` | `IsMember`（`backend/apps/ledger/views.py:41-44`） | 查询参数 | `accounts[]`、`total_balance` | 失败显示“加载失败 + 重试” | 恒调用（仅游客不渲染明细行） |
| IFC-452 | `GET /info/posts?page_size=3` | `IsMember`（`backend/apps/content/views_member.py:14-15`） | 查询参数 | `results[]` 的 `id`、`title` | 失败保留空态 | 恒调用 |

输入校验说明：以上均为只读 GET，无用户输入写入；查询参数由前端常量或白名单值提供（`scope=public`、`status=ENABLED`），不拼接用户自由文本。非分页返回与分页返回都做归一化。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-366 | US-354、355、359 | MOD-215、MOD-216、MOD-218、MOD-219 |
| REQ-FUNC-367 | US-355 | MOD-215、MOD-216、MOD-218、MOD-219 |
| REQ-FUNC-368 | US-356、359 | MOD-215、MOD-216、MOD-218、MOD-219 |
| REQ-FUNC-369 | US-357 | MOD-215、MOD-216、MOD-218、MOD-219 |
| REQ-FUNC-370 | US-358、359 | MOD-215、MOD-216、MOD-218、MOD-219 |
| REQ-FUNC-371 | US-354、355、356、357 | MOD-216、MOD-219 |
| REQ-FUNC-372 | US-354、355、356、358 | MOD-216、MOD-219 |
| REQ-FUNC-373 | US-358 | MOD-216、MOD-219 |
| REQ-FUNC-374 | US-356、358、359 | MOD-216、MOD-217、MOD-219 |
| REQ-FUNC-375 | US-360 | MOD-216、MOD-217、MOD-219 |
| REQ-NFUNC-079 | US-354~360 | MOD-216、MOD-219（数据计划）；MOD-217（无横向溢出） |

## 依赖关系

- MOD-216 → MOD-215（读 IFC-436 能力）
- MOD-216 → MOD-217（使用 IFC-441 类名契约）
- MOD-219 → MOD-218（读 IFC-442 能力）
- MOD-219 → 主题生成物 `miniprogram/theme/generated/themes.scss`
- MOD-216 → HTTP IFC-445~452（只读）

已检查：无循环依赖；两端模块互不引用。

## 数据迁移

无。本次不新增/修改数据库字段、表、索引与迁移文件。

## 受影响的运行单元 / 构建

| 单元 | 影响 | 验证命令（画像 P4） |
|---|---|---|
| Web 前端 | `Home.vue`、`auth.js`、`style.css` 变更，需重新构建 | `frontend/`：`npm run build -- --base=/ocap/`；测试 `npx vitest run --passWithNoTests` |
| 主题产物 | 若修改 `themes/*.theme.json`，需重新生成 | 仓库根：`node scripts/themes/build.mjs`（并跑 `frontend/tests/theme_build.spec.js`） |
| 微信小程序 | `index.vue`、`store/auth.js` 变更，需重新构建 | `miniprogram/`：`npm run build:mp-weixin`；测试 `npm test` |
| Django 后端 | 无变更 | 不重启、不迁移 |

## 领域与外部依赖出处

本次改动不涉及画像 P11-1 专用硬件、P11-2 领域算法，也不新增或修改 P11-3 闭源 API 调用（微信登录链路未触碰）。因此不适用；上文引用的均为仓库现有代码：`backend/apps/committee/services.py:37-62`、`backend/apps/resolutions/views.py:74-99`、`backend/apps/polls/models.py:5-19`、`backend/apps/polls/views.py:24-37,136-147`、`backend/apps/ledger/views.py:41-44`、`backend/apps/approval/views.py:220-221`、`backend/apps/content/views_member.py:14-15`。
