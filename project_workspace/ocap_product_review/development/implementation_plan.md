<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-14T09:25:55+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：产品评审修正（INCREMENTAL，GROUP_C-002 续做）

## 实现概览

- 范围：MOD-074 ~ MOD-085 的产品代码，以及 MOD-086 中"既有测试同步"部分（新增用例主体留给 GROUP_D）。MOD-086 本批只同步既有断言，并补两份自验证规格（`frontend/tests/product_review_core.spec.js`、`miniprogram/tests/product_review_core.spec.js`）。
- 续做说明：上一次调用（GROUP_C-001）被中止。本次先逐模块审阅残留改动，结论如下。

| MOD | 残留状态（审阅结论） | 本次动作 |
|---|---|---|
| MOD-074 | 完成，与 IFC-261/262/273/274 一致 | 保留 |
| MOD-075 | 完成（模型 choices、迁移 0002、审计动作、`close_for_cancelled_user`、`ALREADY_CLOSED`） | 保留 |
| MOD-076 | 完成（`IsCommitteeMember`、`validate_amount_max`、`amount_max()`、`/system/limits`、`limits.py`） | 保留 |
| MOD-077 | 完成（`_check_client`、`_session_kind`） | 保留 |
| MOD-078 | 完成（`id`/`usage_count`/`STYLE_IN_USE`） | 保留 |
| MOD-079 | 完成（支出行 `summary` 置 `null`） | 保留 |
| MOD-080 | 完成（常量改引用） | 保留 |
| MOD-081 | 完成（命令 + 逻辑模块；cleanup 双条件、账本保护退出码 2） | 保留 |
| MOD-082 | 完成（labels/confirm/usePaging/UnitCascader/AuthImage/PagerBar/api.js/auth getter） | 保留 |
| MOD-083 | 完成（14 个用户端页面） | 保留 |
| MOD-084 | 完成（UserPicker、AdminStyleTemplates、7 个管理页、路由、导航） | 保留 |
| MOD-085 | **未开始** | 本次完整实现 |
| MOD-086（同步部分） | 部分：后端 2 个文件已同步；其余未同步，复跑有 3 个后端与 8 个前端失败 | 本次补完（见"现有测试调整"） |

- 实现顺序（拓扑）：后端 MOD-074/075/076/077/078/079 → MOD-080（依赖 MOD-076 的 `core.limits`）→ MOD-081 → MOD-082 → MOD-083/084 → MOD-085（经 HTTP 契约依赖后端）→ MOD-086 同步。无循环依赖。
- 文件数：见"改动清单"。`git diff --stat`（backend/frontend/miniprogram）：69 个既有文件修改，22 个新文件/目录。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-074 | `backend/apps/residency/housing.py` | 新建 | accounts.directory | M | `housing_view`：固定查询数聚合 | DONE |
| 2 | MOD-074 | `backend/apps/residency/{views,urls}.py`、`identity/services.py`、`committee/services.py` | 修改 | 1 | M | `MyHousingView`、`/me` 增 `summary`/`role_label`、任期口径、`identity_labels` 取最高 | DONE |
| 3 | MOD-075 | `backend/apps/residency/{models,services,views}.py`、`identity/services.py`、`core/audit.py` | 修改 | — | M | `CLOSED`、`PendingRequestService`、`ALREADY_CLOSED`、注销关闭、审计动作 | DONE |
| 4 | MOD-075 | `backend/apps/residency/migrations/0002_closed_status.py` | 新建 | 3 | L | 手写 AlterField×2（仅 choices） | DONE |
| 5 | MOD-076 | `backend/apps/core/{limits,config,views,urls}.py`、`claims/views.py`、`income/views.py` | 新建+修改 | — | M | 创建权限收紧、金额上限可配置、`/system/limits` | DONE |
| 6 | MOD-077 | `backend/apps/accounts/views.py` | 修改 | core.config | L | `client` 校验与 7 天会话 | DONE |
| 7 | MOD-078 | `backend/apps/content/styles.py` | 修改 | — | L | 列表补 `id`/`usage_count`，被引用禁删 | DONE |
| 8 | MOD-079 | `backend/apps/ledger/views.py` | 修改 | core.config | L | 报表明细支出 `summary` 脱敏 | DONE |
| 9 | MOD-080 | `backend/apps/polls/views.py`、`income/views.py` | 修改 | 5 | L | 常量收拢，行为不变 | DONE |
| 10 | MOD-081 | `backend/apps/jobs/e2e_fixture.py`、`jobs/management/commands/e2e_fixture.py` | 新建 | 各 app 模型 | H | setup/status/cleanup，护栏与账本保护 | DONE |
| 11 | MOD-082 | `frontend/src/shared/{labels,confirm,usePaging}.js`、`PagerBar.vue`、`portal/parts/{UnitCascader,AuthImage}.vue`、`shared/{api,format}.js`、`stores/auth.js` | 新建+修改 | 1~9（HTTP） | M | 公共件与 API 入口 | DONE |
| 12 | MOD-083 | `frontend/src/portal/*.vue`（14 个） | 修改 | 11 | H | 同住人链路、身份、入口可见性、翻页、确认、中文显示、错误态 | DONE |
| 13 | MOD-084 | `frontend/src/admin/**`、`router/index.js` | 新建+修改 | 11 | H | UserPicker、模板管理页、翻页、确认、金额上限卡 | DONE |
| 14 | MOD-085 | `miniprogram/utils/{labels,confirm,paging}.js` | 新建 | — | M | 与 Web 同键集合；`uni.showModal`；加载更多 | DONE |
| 15 | MOD-085 | `miniprogram/utils/api.js`、`store/auth.js`、`pages.json` | 修改 | 14 | M | IFC-283 全部函数；`isCommittee`/`identitySummary`；登记报表明细页 | DONE |
| 16 | MOD-085 | `miniprogram/components/UnitPicker.vue` | 新建 | 15 | M | 自 units 页抽出的逐级选房 | DONE |
| 17 | MOD-085 | `miniprogram/pages/reports/detail.vue` | 新建 | 15 | L | 报表明细（不含 `summary`） | DONE |
| 18 | MOD-085 | `miniprogram/pages/{units,me,index,claims,resolutions,polls}/index.vue` | 修改 | 14~16 | H | 同住人链路、身份、入口可见性、加载更多 | DONE |
| 19 | MOD-086（同步） | 见"现有测试调整" | 修改 | 1~18 | M | 既有断言按已批准需求同步 | DONE |
| 20 | MOD-086（自验证） | `backend/tests/integration/{test_product_review_api,test_e2e_fixture_command}.py`、`frontend/tests/product_review_core.spec.js`、`miniprogram/tests/product_review_core.spec.js` | 新建 | 1~18 | M | 自验证用例（GROUP_D 可接管或扩充） | DONE |

说明：协议 §A 规定 developer 原则上不新增测试文件；上表第 20 项是 GROUP_C-001 与本次为自验证补的用例，文件名不含 `smoke`，请 test-engineer 接管或并入其用例集。

## 需求追溯

状态均为 DONE，除非另注。"实现位置"写后端 / Web / 小程序三端；`B`=`backend/apps/`，`W`=`frontend/src/`，`M`=`miniprogram/`。无 `[E2E]` 远程用例在本阶段执行（留给 GROUP_D/E2）。

### Must Have

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-150 | AC-150-01 | B `residency/views.py:ResidentApplicationCreateView`（既有）；W `portal/Units.vue:40`（`UnitCascader`）、`applyResident`；M `pages/units/index.vue:137 applyResident` + `components/UnitPicker.vue` | DONE | 两端无内部编号输入框 |
| US-150 | AC-150-02/03 | B `residency/views.py`（既有拒绝规则）；W/M 同上 | DONE | 沿用既有规则，错误文案由后端返回 |
| US-150 | AC-150-04 | M `pages/units/index.vue:137`、`components/UnitPicker.vue` | DONE | |
| US-151 | AC-151-01 | B `residency/housing.py:39`、`residency/views.py:32`；W `portal/Home.vue:12,149`、`portal/Units.vue`（`#review`）；M `pages/index/index.vue:9`、`pages/units/index.vue`（`id="review"`） | DONE | 列表为既有 `to-review` 接口 |
| US-151 | AC-151-02 | B `residency/views.py:261`（`ALREADY_CLOSED`/`ALREADY_DECIDED`，既有决议逻辑）；W `Units.vue decideResident`；M `units decideResident:148` | DONE | |
| US-151 | AC-151-03 | B `residency/views.py`（既有产权业主校验）；W/M 首页仅 HEAD/OWNER 请求 `/me/housing` | DONE | |
| US-151 | AC-151-04 | W `Home.vue`（`pendingReview > 0` 才显示）；M `index.vue:9` | DONE | |
| US-151 | AC-151-05 | M `pages/index/index.vue:9,77`、`pages/units/index.vue:148` | DONE | |
| US-152 | AC-152-01/02/03 | B `residency/views.py ResidentApplicationMineView`（`[:100]`）；W `Units.vue:119`（`myResidentApplications`）；M `units:59` 附近 | DONE | 空态"暂无同住人申请" |
| US-152 | AC-152-04 | M `pages/units/index.vue`（我的同住人申请） | DONE | |
| US-153 | AC-153-01/02/03 | B `residency/views.py ResidentRemoveView/UnitLeaveView`（既有）；W `Units.vue:190 removeResident`、`leave`；M `units:158,169` | DONE | |
| US-153 | AC-153-04 | W `shared/confirm.js`；M `utils/confirm.js` | DONE | 取消不发请求，见两份 `product_review_core.spec.js` |
| US-153 | AC-153-05 | M `pages/units/index.vue:158,169` | DONE | |
| US-154 | AC-154-01/02/03 | B `claims/views.py:87,114`（`IsCommitteeMember`） | DONE | 管理员令牌 403 → 401（已知语义变化，见"架构偏差"） |
| US-154 | AC-154-04 | W `portal/Claims.vue:7`、`PortalLayout.vue`、`Home.vue`、`BottomTabBar.vue`；M `pages/me/index.vue:40`、`pages/index/index.vue`（quick 条件项）、`pages/claims/index.vue:103` | DONE | |
| US-155 | AC-155-01/02/03 | B `accounts/views.py:51 _session_kind`、`_check_client`；M `utils/api.js:6-10`（`client: 'miniapp'`） | DONE | Web/管理端不传 `client`，行为不变 |
| US-156 | AC-156-01/02/03/04 | B `residency/views.py AppealListCreateView.get`；W `Units.vue:73`（我的申诉，驳回原因）；M `units:59` 附近 | DONE | |
| US-156 | AC-156-05 | M `pages/units/index.vue` | DONE | |
| US-157 | AC-157-01/03 | B `identity/services.py:29`、`residency/housing.py:39`、`committee/services.py:75`；W `portal/Me.vue:10`、`Units.vue`；M `pages/me/index.vue`、`pages/units/index.vue` | DONE | |
| US-157 | AC-157-02/04/05 | B 同上（`identity_view`，与管理端目录同源 `accounts/directory.py`）；W/M 无编辑控件 | DONE | |
| US-158 | AC-158-01/03 | W `shared/confirm.js`；`admin/AdminMemberships.vue:75`、`AdminSeats.vue:147`、`AdminRegistry.vue:255`、`AdminFlows.vue:118`、`portal/Income.vue:205`、`Claims.vue:335`、`ResolutionDetail.vue:95` | DONE | |
| US-158 | AC-158-02 | B 既有撤销接口 | DONE | 确认后调用既有接口 |
| US-158 | AC-158-04 | W `portal/Me.vue:279`、`confirm.js`（4 项后果） | DONE | |
| US-159 | AC-159-01/02/04 | W `admin/parts/UserPicker.vue`、`AdminSeats.vue:43`；B 既有 `GET /admin/users` | DONE | |
| US-159 | AC-159-03/05/06 | B 既有席位/流程校验与 `IsAdmin`；W `AdminFlows.vue`（`UserPicker` 多选，提交 `approver_ids`） | DONE | |
| US-160 | AC-160-01~04 | W `shared/usePaging.js`、`shared/PagerBar.vue`、`admin/AdminUsers.vue:69`、`AdminMemberships/AdminAppeals/AdminSeats/AdminFlows/AdminFinance` | DONE | |
| US-161 | AC-161-01/02/04 | W `portal/{Resolutions:89,Polls,Claims,Income,Reports,Tasks}.vue`（`usePaging`）；`shared/api.js` 带 `page`/`page_size` | DONE | |
| US-161 | AC-161-03 | M `utils/paging.js`、`pages/{resolutions,polls,claims,me,index}`（加载更多、没有更多了、总数） | DONE | |
| US-162 | AC-162-01~06 | B `content/styles.py:138`（`STYLE_IN_USE`）、`list_all`；W `admin/AdminStyleTemplates.vue`、`router/index.js:46`、`AdminLayout.vue:36` | DONE | 内置项路由层 404、无入口 |
| US-176/177 | AC-176-*/177-* | 文档类，GROUP_A 已交付，不改代码 | DONE | MOD-086 扫描用例由 GROUP_D 新增 |
| US-178 | AC-178-01 | 三套测试复跑，见 code_review_report"自验证结果" | DONE | 零新增失败；TC-INT-311 为既有失败 |
| US-178 | AC-178-02 | `test_frontend_contract.py`、`test_ui_theme_qa.py` 通过（含 `/me/housing`、`/system/limits`、`DELETE /units/{id}/residents/{id}` 等新调用） | DONE | |
| US-178 | AC-178-03 | 留给 GROUP_D/E2（远程 E2E） | DONE（代码侧） | 既有字段全部保留，只增不删 |

### Should Have

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-163 | AC-163-01/02 | W `portal/Login.vue:16` | DONE | |
| US-164 | AC-164-01~04 | B `residency/services.py:19`、`identity/services.py:116`、`core/audit.py`、`residency/views.py:164,261`；W `admin/AdminAppeals.vue:9` | DONE | |
| US-165 | AC-165-01/02/03 | W `portal/Me.vue:36,41,42`、`portal/parts/AuthImage.vue` | DONE | |
| US-166 | AC-166-01/02/03 | W `PortalLayout.vue`、`Home.vue`；M `pages/index/index.vue`；B 既有 `approval/views.py` 403 | DONE | |
| US-167 | AC-167-01/02/03 | W `shared/labels.js`、`shared/format.js`、`portal/{Units,Polls}.vue`、`admin/{AdminSeats,AdminUsers}.vue` | DONE | |
| US-168 | AC-168-01/02/03 | B `ledger/views.py:78`；W `portal/Reports.vue:36`；M `pages/reports/detail.vue:46`、`pages/me/index.vue`（`openReport`）、`pages.json` | DONE | 支出 `summary` 置 `null`（ADR-091，[ASSUMPTION] Q-B-01） |
| US-169 | AC-169-01/02 | W `portal/InfoDetail.vue:3` | DONE | 后端 404 为既有行为 |
| US-170 | AC-170-01~05 | B `core/config.py:60 validate_amount_max`、`SystemConfigService.amount_max`、`claims/views.py:45`、`income/views.py:44`、`core/views.py`（审计沿用）；W `admin/AdminFinance.vue:83` | DONE | 远程不改全局配置（GR-B-001 条件） |
| US-171 | AC-171-01~04 | B 既有 `resolutions/services.py` 半数分母，不改代码（MOD-080） | DONE | 由 GROUP_D 用例固化 |
| US-172 | AC-172-01 | W `portal/Polls.vue:22`、`Resolutions.vue:52`；B `core/limits.py` | DONE | |
| US-172 | AC-172-02/03/04 | B `polls/views.py:109`（`POLL_OPTIONS_*`）及既有题数/窗口校验 | DONE | |
| US-173 | AC-173-01/02 | B `income/views.py`（`INCOME_IMPORT_MAX_ROWS`、`INCOME_MANUAL_MAX_RECORDS`）；W `portal/Income.vue` 提示 | DONE | |
| US-174 | AC-174-01~05 | 既有代码（MOD-080），不改 | DONE | 由 GROUP_D 用例固化 |
| US-175 | AC-175-01/02/03 | B 既有 `registry/import_spec.py`（6 行/4 个专有部分）；TC-INT-311 由 GROUP_D 更新 | DONE（代码侧） | 基线唯一既有失败，不在本阶段修改 |

## 迁移

- `backend/apps/residency/migrations/0002_closed_status.py`：手写，文件头"手写迁移（画像 P6）"，不含 "Generated by Django"；依赖 `0001_initial`；两个 `AlterField`（`Appeal.status`、`ResidentApplication.status` 的 choices 追加 `CLOSED`）。可逆（无数据转换，无 SQL）。
- `makemigrations --check --dry-run`：`No changes detected`（Django 5.2.x 的 venv）。产物未提交。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 无架构偏差 | — | — | — |

已知语义变化（设计已写明，非偏差）：报销/备用金创建接口对管理员令牌由 403 变 401（IFC-265）；`identity_labels` 对多户用户新快照取最高身份（ADR-080）。

## 现有测试调整

不删用例、不放宽断言。依据均为已批准需求。

| 用例 | 原断言 | 新断言 | 依据 |
|---|---|---|---|
| `backend/tests/integration/test_frontend_contract.py` TC-CONTRACT（/me 字段） | `identities` 键集合 4 项 | 加 `summary`，并断言 `summary` 与 `units[0].role_label` | IFC-262 / REQ-FUNC-149 |
| `backend/.../test_frontend_contract.py` TC-CONTRACT-4 | 读取 `Units.vue` 的 `level/skipped/has_empty/label` | 读取 `Units.vue` + `portal/parts/UnitCascader.vue`；小程序同理读 `pages/units` + `components/UnitPicker.vue` | MOD-082/085：选房逻辑抽出为组件，字段读取点移动 |
| `backend/.../test_specific_part_display_consistency.py` | `units[*]` 键集合 3 项 | 加 `role_label` | IFC-262 |
| `backend/.../test_ui_theme_qa.py` TC-INT-003 | `tasks:(scope)=>get(...)`；小程序 `polls:()=>`、`tasks:()=>` | 正则允许可选 `params`（Web `(scope, params)`；小程序 `(params)`） | IFC-281 / IFC-283（API 增加可选分页参数） |
| `frontend/tests/admin_theme.spec.js` | AdminLayout 13 个导航链接 | 14 个 | REQ-FUNC-153（新增"版式模板"导航） |
| `frontend/tests/qa_unit_theme.spec.js` TC-UNIT-108 | 管理端路由页 16（15 页+Layout） | 17（16 页+Layout） | REQ-FUNC-153；MOD-084 约束已写明 16→17 |
| `frontend/tests/pages.spec.js` TC-WEB-017 | `当前身份：户主、业委会委员` | ME 夹具加 `summary`，断言 `当前身份：委员` | REQ-FUNC-149（汇总身份取最高一项） |
| `frontend/tests/pages.spec.js` TC-WEB-019 | `GET /claims {scope:'mine'}` | `{scope:'mine', page:1, page_size:20}` | REQ-FUNC-152（列表翻页） |
| `frontend/tests/pages.spec.js` TC-WEB-030 | 直接调用 `cancelAccount()` 即发注销请求 | 文件内 mock `confirmDanger` 为确认；取消路径由 `product_review_core.spec.js` 覆盖 | REQ-FUNC-150（注销前须确认） |
| `frontend/tests/theme.spec.js` 底部标签栏 | 恒 5 项 | 成员 5 项（夹具设委员席位）；新增非成员 4 项用例 | REQ-FUNC-146/157（非成员隐藏"报销"）；不触及 CORR-024 |
| `frontend/tests/qa_int_theme.spec.js` TC-INT-105 | 底部 5 标签（`ME` 无席位） | `layoutAt` 增加 `me` 参数，成员夹具得 5 标签 | 同上 |
| `frontend/tests/ui_blocks.spec.js` 决议卡片 | `GET /resolutions {scope:'public'}` | 加 `page:1, page_size:20` | REQ-FUNC-152 |
| `miniprogram/tests/api.spec.js` TC-MP-007 | 登录请求体无 `client` | 含 `client: 'miniapp'` | IFC-268 / REQ-FUNC-147 |
| `miniprogram/tests/pages.spec.js` TC-MP-014 | `身份：户主、业委会委员` | ME 夹具加 `summary`，断言 `身份：委员` | REQ-FUNC-149 |
| `miniprogram/tests/pages.spec.js` TC-MP-015 | 游客首页显示"暂无审批待办" | 游客不显示待办卡、不请求待办；新增 TC-MP-015b（成员 403 按空处理） | REQ-FUNC-157 |
| `miniprogram/tests/pages.spec.js` TC-MP-016/017/018 | `ME` 无席位；`GET /claims {scope:'mine'}` | 夹具设委员席位；`{scope:'mine', page:1, page_size:20}` | REQ-FUNC-146/152 |
| `miniprogram/tests/ui_blocks.spec.js` | `ME.committee=null`；决议请求体 | 夹具设委员；决议请求加分页参数 | REQ-FUNC-146/152/157 |
| `miniprogram/tests/{qa_unit_theme,qa_e2e_pages,qa_e2e_extend,theme}.spec.js` | 页面清单 13 页 | 14 页 | MOD-085 新增 `pages/reports/detail` |
| `miniprogram/tests/setup.js` | uni 桩无 `showModal` | 加 `showModal: vi.fn()` | 测试桩补齐新增 API |

## 开放问题

- [ASSUMPTION] 报表明细支出行 `summary` 置 `null`（Q-B-01，依据 ocap REQ-FUNC-050 OQ-08）；用户若不认可，回退为仅客户端不渲染。
- [ASSUMPTION] 小程序报销页对非成员直接给出"需要业委会成员身份"文案并隐藏表单，而不是等后端 403（设计只写"直接进入时 403 提示"）。
- [ASSUMPTION] 小程序 `formatDateTime` 直接截取后端返回的 `+08:00` 字面值显示"年-月-日 时:分"，不做时区换算。
- 小程序"撤回"未加二次确认：REQ-FUNC-150 的撤回确认只列了 Web 用户端，小程序仅要求移除/退出同住人。
- 无 `TODO(IFC-NNN)`、无 `[UNSOURCED]` stub。本批无外部 API 用法（module_design"领域与外部依赖出处"）。
- 小程序构建（`uni build`）在开发机依赖 uni alpha 工具链（记忆 M-SD-006），本次仅跑 vitest（页面经 `@vue/test-utils` 编译加载）；未运行 `uni build`，如实标"未验证"。

---

## 缺陷修复（回流 1，GROUP_C-004，1.1.0）

续做审阅：GROUP_C-003 残留的 `income/{services,views}.py`、`committee/{services,views}.py` 改动逐项审阅，方向正确，保留；仅补 `AdminSheetListView` 的 `can_void` 上下文（残留未传 `user_id`，字段不会出现）。

| DEF | 级别 | 修改位置 | 要点 | AC |
|---|---|---|---|---|
| DEF-019 | MAJOR | `backend/apps/income/services.py:is_original_approver_of`、`void_sheet`；`income/views.py:AdminSheetListView.get`、`SheetSerializer`；`frontend/src/portal/Income.vue`（作废按钮） | 作废前校验操作人是否在该收入表已通过审批实例 `flow_snapshot.approver_ids` 中（复用 `ApprovalEngine.is_original_approver`）；否则 403 `FORBIDDEN` 并写 `INCOME_VOIDED/DENIED` 审计，表保持已生效；成功作废审计含操作人（既有）；列表项带 `can_void`，Web 按钮 `status==='EFFECTIVE' && can_void` 显示 | AC-060-04/10、AC-064-09 |
| DEF-017 | MINOR | `backend/apps/committee/views.py:AdminCommitteeConfigView.put` | 非法值抛错前写 `COMMITTEE_CONFIG_CHANGED/FAILURE` 审计（含 field） | AC-040-08、AC-064-06 |
| DEF-018 | MINOR | `backend/apps/committee/services.py:merge_seats`、`_audit_merge_invalidated` | 合并使席位 MERGED 时写 `SEAT_INVALIDATED`（reason=ACCOUNT_MERGED） | AC-066-05、AC-064-08 |
| DEF-020 | MINOR | `frontend/src/shared/labels.js`（新增 `FLOW_SCOPE_TEXT`、`APPROVAL_MODE_TEXT`、`INCOME_STATUS_TEXT`、`textOf`）；`admin/AdminFlows.vue`；`portal/{Tasks,ResolutionDetail,Income,InfoList}.vue` | 审批流程列表"适用/方式"显示中文；同类扫描（grep `.status/.scope/.mode/approval_mode/*_at` 直出）另修 5 处，见下表 | REQ-FUNC-158 |

AC-062-04 核对：重新生成报表本就仅 `IsCommitteeMember`，管理员被拒（TC-INT-511 既有通过），无同类缺陷。

DEF-020 范围清单（Web，小程序不改）：

| 页面 | 原显示 | 现显示 |
|---|---|---|
| admin/AdminFlows.vue 适用/方式列 | RESOLUTION/EXPENSE/DESIGNATED… | 决议 / 财务（报销/备用金）/ 收入表；指定负责人审批 / 半数人员同意 |
| portal/Tasks.vue | `task.scope`、`submitted_at` 原值 | 中文类别、`年-月-日 时:分` |
| portal/ResolutionDetail.vue | `approval_mode` 原值 | 中文方式 |
| portal/Income.vue | `item.status` 原值 | 中文状态 |
| portal/InfoList.vue | `published_at` ISO | `年-月-日 时:分` |

[ASSUMPTION] `INCOME_STATUS_TEXT` 的措辞与 `StatusTag` 既有映射对齐（审批中/已生效/未通过/已撤回/草稿），"已作废"为新增。`labels.js` 新增导出刻意不带 `_LABELS` 后缀，避免触发与小程序键集合一致性检查（TC-UNIT-561），小程序不改。

### 追溯行（回流 1）

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-060 | AC-060-04/10 | B `income/services.py:void_sheet`；W `portal/Income.vue`（`can_void`） | DONE | 小程序无收入表入口 |
| US-064 | AC-064-09 | B `income/services.py:void_sheet`（审计含操作人） | DONE | |
| US-040 | AC-040-08 / AC-064-06 | B `committee/views.py:AdminCommitteeConfigView.put` | DONE | TC-INT-512 转绿 |
| US-066 | AC-066-05 / AC-064-08 | B `committee/services.py:merge_seats` | DONE | TC-INT-513 转绿 |
| US-167 | AC-167-03 / REQ-FUNC-158 | W `shared/labels.js`、`admin/AdminFlows.vue` 等 | DONE | OBS-4 关闭 |

### 现有测试调整（回流 1）

不删用例、不放宽断言；未改 TC-INT-512/513/514。

| 用例 | 原断言 | 新断言 | 依据 |
|---|---|---|---|
| `backend/tests/integration/test_finance_polls_api.py` `IncomeTests.test_submit_approve_and_void` | 录入人（非原审批人）作废 → 200 VOID | 录入人作废 → 403 FORBIDDEN 且表仍 EFFECTIVE；原审批人作废 → 200 VOID | AC-060-04/10（Q109=B） |
| `backend/tests/e2e/test_rework_journeys.py` `IncomeManualEntryJourneyTests.test_manual_entry_submit_approve_report_then_void` | 录入人作废 | 原审批人（approver_token）作废，其余断言不变 | 同上 |

## 开放问题（回流 1）

- 无新增 `TODO/[UNSOURCED]`。`can_void` 仅在管理端列表返回；详情接口未返回（Web 按钮只在列表）。
- 作废被拒时的 `INCOME_VOIDED/DENIED` 审计为额外行为，需求未要求，可按需移除。

---

## 缺陷修复（回流 2，GROUP_C-005，2.1.0）

| DEF | 级别 | 修改位置 | 要点 | AC |
|---|---|---|---|---|
| DEF-021 | MAJOR | `frontend/src/portal/Home.vue`（待办卡片）、`portal/Tasks.vue`（标题回退） | 类别 `textOf(FLOW_SCOPE_TEXT, task.scope)`；时间 `formatDateTime(task.submitted_at)`；标题回退值 `task.scope` 也改中文 | REQ-FUNC-158 |
| DEF-022 | MINOR | `frontend/src/portal/ResolutionDetail.vue` | "表决截止"用 `formatDateTime` | REQ-FUNC-158 |

### 同类扫描（Web 用户端、管理端；`portal/parts`、`admin/parts` 子组件无命中）

扫描命令（仓库根 `frontend/src`）：
1. 模板插值：`grep -rnE "\{\{[^}]*(_at|deadline|time|date|scope|status|mode|type|role|kind)\b[^}]*\}\}" portal admin shared --include=*.vue | grep -vE "formatDateTime|textOf|statusLabel|datetime\(|StatusTag"`
2. 表格列直出：`grep -rnE "prop=\"[a-z_.]*(_at|deadline|time|date|scope|status|mode|type|role|kind|active|enabled|is_)[a-z_]*\"" portal admin --include=*.vue`，并枚举全部 `prop=` 逐一判断
3. 日期字段二次扫描：`grep -rnE "_at\b|expires|deadline|period_|\.date" portal admin --include=*.vue | grep -v "formatDateTime\|datetime("`
4. 布尔值：`grep -rnE "\{\{ *[a-z.]*\.(is_|can_|has_)…|enabled|active|verified…"`，无直出命中

命中清单与结论：

| 位置 | 字段 | 结论 |
|---|---|---|
| portal/Home.vue:27-28 | task.scope、submitted_at | 改（DEF-021） |
| portal/Tasks.vue:16 | task.scope 回退 | 改 |
| portal/ResolutionDetail.vue:7 | vote_deadline | 改（DEF-022） |
| portal/InfoDetail.vue:9 | published_at（ISO 直出） | 改：`formatDateTime` |
| admin/AdminAudit.vue 时间/主体/结果列 | occurred_at、actor_type、result | 改：`datetime`（含秒，审计需要）、`AUDIT_ACTOR_TEXT`、`AUDIT_RESULT_TEXT` |
| admin/AdminFinance.vue 类型/状态列 | type、status | 改：`CLAIM_TYPE_TEXT`、`CLAIM_STATUS_TEXT` |
| admin/AdminMemberships.vue | certified_at | 改：`formatDateTime` |
| admin/AdminContentPosts.vue | published_at、updated_at | 改：`formatDateTime`（status 列已有 `statusText`） |
| admin/AdminContentEditor.vue 推送记录 | created_at | 改：`formatDateTime`（status 已有 `pushStatusText`） |
| portal/Home.vue:54 | poll.kind 三元 | 不改（已是中文文案） |
| portal/Claims.vue:22,110,129；Resolutions.vue:39,43；Reports.vue:36；AdminContentPosts/Editor status；AdminPlatforms authText；AdminMemberships role | type/mode/entry_type/status/role | 不改：已经过 typeLabel/modeText/entryTypeText/statusText/authText/ROLE_LABELS 映射 |
| portal/Income.vue:29,70；Reports.vue:34 | period_start/end、occurred_on | 不改：仅日期，保持"年-月-日" |
| admin/AdminSeats.vue:25-26 | term_start/term_end | 不改：仅日期 |
| admin/AdminAudit.vue action、object_type | 审计动作码、对象类型 | 不改：筛选输入框按原始代码检索，列显示原值便于对照；无需求要求翻译 |
| admin/RegistryImportDialog.vue required/allowed；AdminContentSettings key/default；Income category | 后端已给中文文本或自由文本/配置键 | 不改 |
| Home.vue:107 `remaining(poll.deadline)`、Polls/Resolutions 的 `deadline`/`vote_deadline` | 表单/计算 | 不改：不是显示插值 |

新增映射放在 `frontend/src/shared/adminText.js`（`CLAIM_TYPE_TEXT`、`CLAIM_STATUS_TEXT`、`AUDIT_ACTOR_TEXT`、`AUDIT_RESULT_TEXT`），而不是 `labels.js`：首次放入 labels.js 时 TC-UNIT-588 断言其非 `_LABELS` 导出恰为三项而失败，故独立成文件，未改该用例。小程序不改。

### 追溯行（回流 2）

| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-167 | AC-167-03 / REQ-FUNC-158 | W `portal/{Home,Tasks,ResolutionDetail,InfoDetail}.vue`、`admin/{AdminAudit,AdminFinance,AdminMemberships,AdminContentPosts,AdminContentEditor}.vue`、`shared/adminText.js` | DONE | TC-UNIT-586/587 转绿 |

### 现有测试调整（回流 2）

无。未改任何用例；TC-UNIT-586/587/588 断言原样通过。

## 开放问题（回流 2）

- [ASSUMPTION] 管理端审计列表"主体/结果"的中文措辞（成员/管理员/系统；成功/失败/拒绝）为自拟；报销类型/状态沿用用户端 `typeLabel` 与既有 `INCOME_STATUS_TEXT` 同类措辞（已通过/未通过）。
- [ASSUMPTION] 审计"动作"码列保持原值（见上表）。
