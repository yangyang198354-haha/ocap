<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-25T12:18:30+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_role_home/requirements/requirements_spec.md</file><file>project_workspace/ocap_role_home/requirements/user_stories.md</file><file>frontend/src/portal/Home.vue</file><file>frontend/src/stores/auth.js</file><file>frontend/src/shared/style.css</file><file>miniprogram/pages/index/index.vue</file><file>miniprogram/store/auth.js</file></input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 架构设计（增量）

## 架构概览

本次改动是**纯前端展示层增量**：Web 用户端（Vue 3 + Element Plus）与微信小程序（uni-app Vue 3）各自把固定模块首页改为按当前用户能力渲染的角色化首页。系统边界、后端接口、权限模型、数据库与主题生成机制均不变（C-390、REQ-NFUNC-079）。

改动在现有系统中的位置：

- Web：`frontend/src/portal/Home.vue`（页面编排）+ `frontend/src/stores/auth.js`（能力派生）+ `frontend/src/shared/style.css` 与 `themes/*.theme.json` 的 Web 样式段（统一骨架）。
- 小程序：`miniprogram/pages/index/index.vue`（页面编排）+ `miniprogram/store/auth.js`（能力派生）。
- 不新增接口、不新增依赖、不新增数据表；复用的现有接口见 module_design 的 HTTP 契约表。

关键质量属性（REQ-NFUNC-079）：

- 首屏请求只包含当前角色实际渲染的模块：非委员不请求 `/approval/tasks`，无 HEAD/OWNER 房屋不请求 `/me/housing`（AC-355-02、AC-356-03）。
- 模块顺序在 Web 三主题与小程序两端一致（REQ-FUNC-375、AC-360-01/02）。
- 数量只在模块标题出现一次，删除 4 张统计卡与 Hero 重复徽章（REQ-FUNC-374）。

## 部署视图

| 组件 | 运行单元 | 环境 | 本次是否变化 |
|---|---|---|---|
| Web 前端 | `frontend` 构建产物（`npm run build -- --base=/ocap/`）→ 树莓派 nginx `8090` / frp `443` | 测试（内网/外网，画像 P7） | 需重新构建与发布前端静态产物 |
| 微信小程序 | uni-app 构建（`npm run build:mp-weixin`）→ 微信开发者工具上传 | 画像 P7 未声明小程序发布环境 | 需重新构建；发布动作不在本次范围 |
| 主题产物 | `node scripts/themes/build.mjs` 生成 `frontend/src/theme/generated/themes.css` 与 `miniprogram/theme/generated/themes.scss` | 构建期 | 若修改 `themes/*.theme.json` 则需重跑 |
| Django 后端 | systemd `ocap-backend`（gunicorn） | 测试 | 不变化，无需重启 |

## ADR

### ADR-195: 前端从 `/me` 派生能力，不新增身份字段或接口

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-366 要求按“是否户主/产权业主、是否业主代表、是否业委会成员”渲染模块；C-390 禁止改后端，C-391 要求复用 `/me` 的 `units[].role` 与 `committee.position`。
- 被排除方案与约束来源：新增 `/me/capabilities` 接口或扩展 `/me` 返回字段（被 C-390、REQ-NFUNC-079 排除）；直接按 `identities.labels` 文本判断（labels 为单一最高身份，会丢失多重身份信息，违反 AC-359-01/02，`backend/apps/committee/services.py:71-85`）。
- Decision: 在 Web 与小程序各自的 auth store 中新增只读 getter，从 `units[].role` 与 `committee.position` 派生能力集合：`isCommittee`、`isRepresentative`、`hasOwnerUnit`、`isGuest`、`ownerUnits`。
- Consequences: 正向——零后端改动、与接口权限同口径（`isCommittee` 与 `IsCommitteeMember` 一致，`isRepresentative` 对应 `CommitteeQuery.is_representative`）；负向——能力判定散落两端需保持一致，由 ADR-200 的“同模块键/同顺序”约束与测试守齐。

### ADR-196: 首页模块可见性与顺序集中为一份视图模型

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-366/374/375 与 AC-354~359 要求不同角色看到不同模块及顺序；现有 `Home.vue` 用零散 `v-if` 与 `stats` 数组拼接（`frontend/src/portal/Home.vue:15-46`），无法保证顺序一致。
- Options:
  - A. 继续在模板里逐块 `v-if`：改动最小；缺点——顺序、数量和“0 隐藏”规则分散，两端易漂移，难以用单元测试覆盖。
  - B. 用纯函数生成模块清单（key、标题、数量、跳转、是否渲染），模板只按清单渲染：缺点——需一次重构模板；优点——顺序/隐藏规则单点定义，可直接被 vitest 断言。
- Decision: 选择 B。按“能力档案（profile）”定义四组内容尾部顺序，任务类模块按固定优先级插入，满足各角色 AC。
- Consequences: 正向——AC-354~359 的顺序差异可由数据表表达并测试；负向——模板改动面较大，需回归三主题布局。

### ADR-197: “业主代表决议”以已截止的 REP_VOTE 投票作为公开决议来源之一

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-371 要求公开决议同时展示业委会决议与业主代表决议并带来源标签。现有后端只有 `Resolution`（发起限主任/副主任，`backend/apps/resolutions/views.py:75-81`）与 `Poll.kind=REP_VOTE`（业主代表投票，`backend/apps/polls/models.py:7`），没有独立的“业主代表决议”实体。
- 被排除方案与约束来源：新增后端决议类型或转换逻辑（被 C-390 禁止）；只展示 `Resolution`（不满足 REQ-FUNC-371）。
- Decision: 前端把 `GET /resolutions?scope=public` 的结果标为来源 `COMMITTEE`，把 `GET /polls` 中 `kind=REP_VOTE` 且 `status=CLOSED` 的结果标为来源 `REPRESENTATIVE`，合并为一个“公开决议”列表（按可见时间倒序，前端合并上限 5 条）。
- Consequences: 正向——零后端改动即满足“双来源 + 标签”；负向——两类数据字段不同（决议有 `status`，投票有 `result_snapshot`），需在视图模型中归一化展示字段；此口径为展示层约定，见开放问题 A-01。

### ADR-198: “待我表决”的参与状态用有界详情请求获取

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-369 与 AC-357-01 要求业主代表看到投票标题、截止时间与**参与状态**。`GET /polls` 列表不返回 `my_response` 或 `can_respond`，只有 `GET /polls/{id}` 返回（`backend/apps/polls/views.py:136-147`）。
- Options:
  - A. 后端列表增加字段：被 C-390 排除。
  - B. 只展示标题与截止时间，不展示参与状态：不满足 AC-357-01。
  - C. 只对“待我表决”卡中实际展示的前 3 条 OPEN + REP_VOTE 投票逐个请求详情，`Promise.allSettled` 容错：请求数有上界（≤3），失败降级为“未确认”。
- Decision: 选择 C，请求上限固定为 3（与卡片最多展示 3 条一致）。
- Consequences: 正向——满足 AC 且不引入 N+1 无界请求；负向——首屏多最多 3 个并行请求，需在 REQ-NFUNC-079 的“只请求实际渲染模块”范围内（仅业主代表触发）。

### ADR-199: 财务公开按角色分层，游客不展示逐账户明细

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-372 要求财务公开对所有登录用户可见；D-RH-03 决策“游客只显示账户合计 + 报表入口，不展示逐账户明细”；`GET /ledger/accounts/summary` 权限为 `IsMember`（`backend/apps/ledger/views.py:41-44`），所有登录用户可读。
- 被排除方案与约束来源：后端按角色裁剪账户列表（被 C-390 排除）；游客完全不展示财务（违反 REQ-FUNC-372 与 D-RH-03）。
- Decision: 所有登录用户展示“启用账户合计 + 财务报表入口”；游客（`identities.is_guest=true`）不渲染逐账户行；非游客保留现有逐账户行；业委会成员只多出“管理快捷”，不改财务读取口径。
- Consequences: 正向——口径与决策记录一致，且不新增接口；负向——前端隐藏不是权限边界，越权读取仍由后端 `IsMember` 兜底（C-396）。

### ADR-200: Web 三主题共用骨架，小程序独立实现但共享模块键与顺序

- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-375、C-392、C-393；Web 主题由 `themes/*.theme.json` 经 `node scripts/themes/build.mjs` 生成统一 CSS（`scripts/themes/build.mjs:1-10,188-191`），三主题已按 4 栏 `.home-grid` 生成（`frontend/src/theme/generated/themes.css:248,432,644`）。小程序为独立 uni-app 工程，不能直接复用 Web 组件。
- 被排除方案与约束来源：抽取跨端共享组件库（引入新依赖/构建改造，违反 C-394 与最小改动）；三主题各自定制首页布局（违反 C-393）。
- Decision: Web 端只用共享 `style.css` + 主题变量控制视觉，`.home-grid` 保持 4 栏；小程序用单列卡片流，模块 key 与顺序常量与 Web 同名同序，样式随现有小程序主题生成物。
- Consequences: 正向——主题差异只在视觉层，顺序一致可测；负向——两端各维护一份模块顺序常量，需要一致性测试（GROUP_D）。

### ADR-201: 空态保留与任务类 0 隐藏

- Status: Proposed
- Type: constraint-driven
- Context: C-397 与 D-RH-02：投票与公开决议无数据保留空态；任务类（待我处理/待我表决/待办审批）数量为 0 不渲染。AC-354-01、AC-358-01、AC-359-03。
- 被排除方案与约束来源：统一隐藏（违反 C-397）；统一保留空态（任务卡出现 0 噪音，违反 D-RH-02）。
- Decision: 在模块视图模型中以 `kind: 'content' | 'task'` 区分：`content` 恒渲染并带空态文案；`task` 在数量为 0 时不进入渲染清单。
- Consequences: 正向——规则单点、可断言；负向——内容类模块在无数据时占据首屏空间（用户已确认接受）。

## 开放问题 / ASSUMPTION

| 编号 | 内容 | 处理 |
|---|---|---|
| A-01 | “业主代表决议”在现有系统中无独立实体，本设计以“已截止的 REP_VOTE 投票”充当（ADR-197） | 非阻断；已按此设计，GROUP_D 按 AC-357-03/AC-354-02 的“来源标签”验证；若用户要求改为后端实体需另立需求 |
| A-02 | REQ-FUNC-372 正文“业委会成员额外看到账户合计与报表入口”与 D-RH-03“游客看到账户合计 + 报表入口”表述不一致 | 以 D-RH-03 与 AC-354-02/AC-358-02 为准：所有登录用户看合计 + 报表；游客不看逐账户行；非游客保留逐账户行 |
| A-03 | 各故事给出的模块顺序不完全相同（如 AC-354 决议在投票前，AC-355 投票在决议前） | 以“能力档案 + 任务优先”实现，逐角色满足各自 AC，见 ADR-196 与 module_design 的顺序表 |
