<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-18T10:58:00+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>requirements/user_stories.md（1.0.0）</file>
    <file>architecture/architecture_design.md（1.0.0）</file>
    <file>architecture/module_design.md（1.0.0）</file>
    <file>architecture/tech_stack.md（1.0.0）</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划（终稿，INCREMENTAL）

## 实现概览

- 模块 14 个（MOD-139~152），全部 DONE；另按用户答复（2026-11-18 "全部按照推荐"，Q5=A）修复时区缺陷。
- 改动文件：修改 36 个、新建 7 个（后端 `committee/binding.py`、`registry/listing.py`、两个迁移；前端 `SeatHolderPicker.vue`、`ParticipantList.vue`、`shared/unitSearch.js`）。未改 `deploy/`、`miniprogram/`、测试代码、画像、需求/架构文档。
- 实现顺序（模块依赖拓扑）：MOD-139 → MOD-140 → MOD-141 → MOD-142 → MOD-143 → MOD-144 → MOD-145（后端）→ MOD-147 → MOD-146/148/149/150/151/152（前端）。
- 无新增依赖、环境变量、服务。无 P11 外部 API 用法（未调用微信/阿里云/邮件），故无出处注释需求。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-139 | backend/apps/core/attachments.py | 修改 | — | M | 新增 `ValidatedUpload`/`StoredFile`、`validate_upload`/`store_validated`/`discard`；`store` 改为二者组合，行为与错误码不变；`open` 对 AVATAR（TEMP）放行已登录主体（IFC-360） | DONE |
| 1 | MOD-139 | backend/apps/residency/views.py | 修改 | — | M | `AppealListCreateView.post` 按 content-type 走 `_post_multipart`（IFC-345：先校验、限频、事务内建申诉并落盘关联、失败 `discard`）；JSON 分支原样 | DONE |
| 2 | MOD-140 | backend/apps/committee/models.py、migrations/0002_seat_registry_holder.py | 修改/新建 | registry 0005 | M | `Seat.user` 可空，新增 holder_owner/holder_unit_text/holder_name/bound_at/bind_conflict_at 与 `uniq_seat_active_per_owner` | DONE |
| 2 | MOD-140 | backend/apps/committee/binding.py | 新建 | MOD-140 模型 | H | `SeatBinding.try_bind`（永不抛异常、冲突审计）、`certified_user_of`（先 Membership.registry_owner，后手机号回退） | DONE |
| 2 | MOD-140 | backend/apps/committee/services.py | 修改 | binding | H | `grant` 支持 `registry_owner_id`；`change` 保留持有人记录；`active_*_ids` 排除空 user；`pending_bind_count`；`reconcile_registry_seats`；`expire_due` 开头调用 | DONE |
| 2 | MOD-140 | backend/apps/committee/views.py、urls.py | 修改 | services | M | POST 席位 `registry_owner_id`；`seat_view` 增 holder/bind_state 且防 user 为空；新增 `AdminOwnerCandidatesView`；`config_view` 增 `half_majority_hint` | DONE |
| 2 | MOD-140 | backend/apps/core/audit.py | 修改 | — | L | 登记 `SEAT_BOUND`、`SEAT_BIND_CONFLICT`（未登记会抛 ValueError） | DONE |
| 3 | MOD-141 | backend/apps/residency/models.py、migrations/0005_membership_registry_owner.py | 修改/新建 | registry 0005 | L | `Membership.registry_owner` | DONE |
| 3 | MOD-141 | backend/apps/registry/ownership.py、services.py | 修改 | — | L | `matched_owner`；`owner_matches` 改为其包装；`owner_id_by_phone` | DONE |
| 3 | MOD-141 | backend/apps/residency/services.py、views.py、auto_bind.py、phone_match.py | 修改 | MOD-140 | M | `certify_owner(verified_owner_id, via)`、`record_verified_owner`；手动认证/申诉通过/手机号匹配确认三触发点 | DONE |
| 4 | MOD-142 | backend/apps/registry/views.py、importing.py | 修改 | MOD-140 | L | 业主改动 PUT、专有部分删除、`apply_plan` 三处事务内调用 `reconcile_registry_seats` | DONE |
| 5 | MOD-143 | backend/apps/residency/housing.py、views.py | 修改 | MOD-141 | M | `/me/housing` 增 `real_names`（顶层）与 `co_owners`（每套）；一次查询取全部业主 | DONE |
| 6 | MOD-144 | backend/apps/resolutions/services.py、views.py、urls.py、apps.py | 修改 | MOD-140 | H | `is_publicly_visible`、`vote_stats`；公开范围；`participation`、`initiator.display_name`；删 `votes`；`ResolutionParticipantsView`；附件策略 | DONE |
| 7 | MOD-145 | backend/apps/registry/listing.py（新）、views.py、urls.py | 新建/修改 | — | M | 服务端自然顺序排序 + `OrderedUnitPage`；`sort/order` 白名单；`AdminUnitOptionsView` | DONE |
| 8 | MOD-147 | frontend/src/portal/parts/UnitCascader.vue、shared/unitSearch.js（新） | 修改/新建 | — | M | 四级 `filterable` + 前缀优先排序；`fetcher` 可注入 | DONE |
| 9 | MOD-146 | frontend/src/portal/units/UnitsAppeal.vue、shared/api.js | 修改 | MOD-139 | M | 页面内暂存、逐项校验、FormData 一次提交；`unitApi.submitAppeal` | DONE |
| 10 | MOD-148 | frontend/src/portal/units/UnitsIdentity.vue、stores/housing.js | 修改 | MOD-143 | L | 真实姓名与共有产权人 | DONE |
| 11 | MOD-149 | frontend/src/portal/Resolutions.vue、ResolutionDetail.vue、Polls.vue、parts/ParticipantList.vue（新）、shared/voteShare.js、shared/api.js、shared/style.css | 修改/新建 | MOD-144 | H | 四项标注、参与进度条、参与人列表、整卡可点 | DONE |
| 12 | MOD-150 | frontend/src/layout/SideNav.vue、shared/style.css | 修改 | — | M | `<Transition>` JS 钩子高度动画 + CSS 选中条/错峰淡入（均在 no-preference 内）；`SubNavBar.vue` 无需改动（共用 `.is-active` 样式类） | DONE |
| 13 | MOD-151 | frontend/src/admin/AdminRegistry.vue | 修改 | MOD-145 | L | 四列 `sortable="custom"`、两态、重置清排序 | DONE |
| 14 | MOD-152 | frontend/src/admin/AdminSeats.vue、admin/parts/SeatHolderPicker.vue（新）、shared/api.js | 修改/新建 | MOD-140/145/147 | M | 逐级选房 + 选业主；持有人/待绑定/冲突展示；顶部提示 | DONE |
| 15 | 时区缺陷 | backend/apps/jobs/views.py:49、jobs/management/commands/run_due_jobs.py:26 | 修改 | — | L | `timezone.now().date()` → `timezone.localdate()`；`git grep "now().date()"` 仅此一处，同类 `now.date()`（run_due_jobs，传给 `expire_due` 与 `generate_due`）一并改为 `timezone.localdate(now)` | DONE |

## 需求追溯（本次范围内全部 Must Have 故事的全部 AC）

> 前端文件均在 `frontend/src/`，后端均在 `backend/apps/`。"DONE" = 代码已实现并在本机经自验证（见 code_review_report §自验证）；新增用例由 test-engineer 补。

| US | AC | 实现位置（文件:行） | 状态 | 说明 |
|---|---|---|---|---|
| US-244 | AC-244-01 | portal/units/UnitsAppeal.vue:70 `onPick`（`:auto-upload="false"`，仅入 `staged`，不调任何上传 API）；列表 `:24` | DONE | 不再调用 `attachmentApi.upload` |
| US-244 | AC-244-02 | portal/units/UnitsAppeal.vue:84 `submitAppeal` → shared/api.js:52 `submitAppeal`；residency/views.py:177 `_post_multipart` | DONE | 成功提示文案沿用 |
| US-244 | AC-244-03 | portal/units/UnitsAppeal.vue `staged` 为页面内 `ref`（无任何网络请求，刷新即空） | DONE | 服务器因选择产生的文件数恒为 0 |
| US-244 | AC-244-04 | portal/units/UnitsAppeal.vue:80 `removeStaged` | DONE | |
| US-245 | AC-245-01 | portal/units/UnitsAppeal.vue:86（"请选择到具体户"，早退不发请求）；按钮无 disabled | DONE | |
| US-245 | AC-245-02 | portal/units/UnitsAppeal.vue:87-88（空/超 64 字提示）；后端 residency/views.py `_post_multipart` 同校验 | DONE | |
| US-245 | AC-245-03 | portal/units/UnitsAppeal.vue:89（"请至少选择 1 份产权证明"） | DONE | |
| US-245 | AC-245-04 | portal/units/UnitsAppeal.vue:70-78 `onPick`（10MB、仅 jpg/png/pdf、最多 5 份，不合格不入暂存） | DONE | 后端同规则兜底（`validate_upload`） |
| US-245 | AC-245-05 | portal/units/UnitsAppeal.vue `catch` 保留表单与暂存；后端 residency/views.py `_post_multipart`（`except` → `discard`，事务回滚） | DONE | 本机 scratch 验证：失败后 Attachment/Appeal/磁盘文件均无新增 |
| US-245 | AC-245-06 | residency/views.py `_post_multipart`：`APPEAL_PENDING` 409 在文件校验与落盘之前 | DONE | |
| US-246 | AC-246-01 | portal/parts/UnitCascader.vue:6-25（`filterable` + `filter-method`）；shared/unitSearch.js:4 `rankOptions` | DONE | label 仅取"（"之前的名称部分参与匹配（避免面积数字误命中） |
| US-246 | AC-246-02 | UnitCascader.vue `onVisible`（关闭下拉清空查询）；`rankOptions` 空查询返回原序全部 | DONE | |
| US-246 | AC-246-03 | UnitCascader.vue `no-data-text="无匹配项"` | DONE | |
| US-246 | AC-246-04 | 三页均使用同一组件，未传 `fetcher`（缺省 `unitApi.options`）；`loadOptions` 逐级逻辑未改 | DONE | |
| US-246 | AC-246-05 | UnitCascader.vue 四个 `el-select` 均 `filterable` | DONE | 方向键/回车由 Element Plus 提供 |
| US-247 | AC-247-01 | residency/housing.py:86-92 `real_names`；residency/views.py `MyHousingView`；portal/units/UnitsIdentity.vue:13 | DONE | |
| US-247 | AC-247-02 | residency/housing.py:91 去重保序 | DONE | |
| US-247 | AC-247-03 | housing.py（仅 OWNER_ROLES 房屋计算，其余 `[]`）；UnitsIdentity.vue:13 空显示"—" | DONE | |
| US-247 | AC-247-04 | housing_view 只作用于 `request.user` 自身 Membership，无入参 | DONE | |
| US-248 | AC-248-01 | housing.py `co_owner_names`（排除 `is_mine`）；UnitsIdentity.vue:28 | DONE | 仅姓名，无手机号 |
| US-248 | AC-248-02 | UnitsIdentity.vue:28（空则"无"） | DONE | |
| US-248 | AC-248-03 | housing.py `owners_by_unit` 只取本人全部 Membership（含同住人）的专有部分；游客 `units=[]` | DONE | 无任何按专有部分取姓名的接口 |
| US-248 | AC-248-04 | housing.py 不带注册状态 | DONE | |
| US-248 | AC-248-05 | housing.py `co_owner_names(m.unit_id)` 按房屋行计算 | DONE | |
| US-249 | AC-249-01 | resolutions/views.py:39 `resolution_view`（`initiator.display_name`）；portal/Resolutions.vue:21-27、:44-47 | DONE | 已结束同时显示"已结束"与结果标签 |
| US-249 | AC-249-02 | Resolutions.vue:47（"无截止时间"）；"指定负责人"标签保留 | DONE | |
| US-249 | AC-249-03 | resolutions/views.py `display_name = nickname or account_no`；Resolutions.vue:45 | DONE | |
| US-249 | AC-249-04 | resolutions/views.py `ResolutionListCreateView.get`（公开范围 Q）、`_ensure_can_view`；services.py:114 `is_publicly_visible` | DONE | 进行中显示"进行中"，详情 200 |
| US-249 | AC-249-05 | 三页共用 Resolutions.vue | DONE | |
| US-249 | AC-249-06 | `is_publicly_visible`（指定负责人审批中、已撤回不公开）；`_ensure_can_view` 403 | DONE | |
| US-250 | AC-250-01 | shared/voteShare.js:16 `participationShare`；Resolutions.vue:31-41 | DONE | 分母=应参与人数，余量留白 |
| US-250 | AC-250-02 | 同上（pct 取整，满条无留白） | DONE | |
| US-250 | AC-250-03 | participationShare（expected>0、voted=0 → 0%，无 NaN） | DONE | |
| US-250 | AC-250-04 | participationShare `empty` → Resolutions.vue:31 "暂无表决人"、不画条 | DONE | |
| US-250 | AC-250-05 | Resolutions.vue:`v-else` 分支 "由指定负责人审批" | DONE | 后端 `participation: None` |
| US-250 | AC-250-06 | Resolutions.vue:33 `aria-label`（"已参与 a / b，同意…，反对…，弃权…"） | DONE | |
| US-250 | AC-250-07 | resolutions/views.py `_Expected.current()` = `denominator_for_half_majority`（含待绑定）；`participation.expected` | DONE | |
| US-251 | AC-251-01 | resolutions/views.py:158 `ResolutionParticipantsView`；portal/parts/ParticipantList.vue；ResolutionDetail.vue:24 | DONE | 无头像显示默认占位 |
| US-251 | AC-251-02 | `ResolutionParticipantsView` 仅返回 display_name/avatar_url/voted_at；`resolution_view` 删 `votes` | DONE | 不列未参与者 |
| US-251 | AC-251-03 | ParticipantList.vue（"暂无人参与"） | DONE | |
| US-251 | AC-251-04 | participants 端点 DESIGNATED → `count 0`；ParticipantList.vue（"无表决参与人"） | DONE | |
| US-251 | AC-251-05 | `permission_classes=[IsMember]`（401/管理员 403） | DONE | 本机验证未登录 401 |
| US-251 | AC-251-06 | 进行中半数同意详情 200；响应无 `votes`、仅 `vote_counts` | DONE | |
| US-252 | AC-252-01 | shared/style.css:242 `.res-title::after`/`.poll-link::after` 拉伸；Resolutions.vue、Polls.vue:13 | DONE | 保留原生链接语义 |
| US-252 | AC-252-02 | shared/style.css:253-257（悬停抬升+阴影、按下 `scale(.985)`，≤180ms） | DONE | 三主题观感为人工验证项 |
| US-252 | AC-252-03 | shared/style.css:243（卡片内其他 a/button `z-index:1`） | DONE | |
| US-252 | AC-252-04 | 原生 `<a>` Tab/Enter；shared/style.css:244 `:focus-within` 焦点样式 | DONE | |
| US-252 | AC-252-05 | 所有新增动效规则在 `@media (prefers-reduced-motion: no-preference)` 内 | DONE | |
| US-252 | AC-252-06 | portal/Polls.vue:13 `.poll-link` | DONE | |
| US-253 | AC-253-01 | layout/SideNav.vue:27-41（`<Transition>`）、:90 `onEnter`/`onLeave`（280ms 高度动画） | DONE | 点击仅切换 `openKey`，不阻塞 |
| US-253 | AC-253-02 | shared/style.css:258-262（`.is-active::after` scaleY） | DONE | `.is-active` 逻辑未改 |
| US-253 | AC-253-03 | 动效只用 `var(--accent)` 等主题变量 | DONE | 三主题可见为人工验证项 |
| US-253 | AC-253-04 | no-preference 包裹 + SideNav `reducedMotion()` 直接完成 | DONE | |
| US-253 | AC-253-05 | SideNav.vue `@keydown.esc`/`collapse` 未改动 | DONE | |
| US-253 | AC-253-06 | `.sub-nav-item.is-active::after`（SubNavBar 沿用同一类名，无代码改动） | DONE | |
| US-254 | AC-254-01 | registry/listing.py:10 `ordered_unit_ids`（`unit_sort_key`）；registry/views.py:121 `AdminUnitListView.get` | DONE | 取代 `order_by("id")` |
| US-254 | AC-254-02 | `OrderedUnitPage` + `page_response`；id 为终极并列键 | DONE | scratch 验证 count 与顺序 |
| US-254 | AC-254-03 | 过滤在排序前（`_apply_unit_filters` 后取 id 序列） | DONE | |
| US-254 | AC-254-04 | 复用 `registry/ordering.py` 规则，不新增写法 | DONE | |
| US-255 | AC-255-01 | admin/AdminRegistry.vue:40-44 `sortable="custom"` 两态；:201 `onSort`；:168 请求参数；listing.py 稳定两次排序 | DONE | |
| US-255 | AC-255-02 | 服务端全量排序后分页 | DONE | |
| US-255 | AC-255-03 | AdminRegistry.vue:`sort` 状态跨 `load()`；`resetFilters` 清排序并 `clearSort` | DONE | |
| US-255 | AC-255-04 | 仅四列 `sortable`，其余列无 | DONE | |
| US-255 | AC-255-05 | `AdminUnitListView` `IsAdmin`；非法 sort/order → 400 `INVALID_QUERY`（registry/views.py:121-130） | DONE | |
| US-256 | AC-256-01 | committee/services.py:98 `grant(registry_owner_id)`；views.py `AdminSeatListCreateView.post`；admin/AdminSeats.vue `create`、parts/SeatHolderPicker.vue | DONE | 审计 `SEAT_GRANTED` 含 holder，不含手机号 |
| US-256 | AC-256-02 | committee/views.py:129 `AdminOwnerCandidatesView`（姓名 + 脱敏手机号） | DONE | |
| US-256 | AC-256-03 | `grant` 上限计数 `status="ACTIVE"` 含待绑定；`CAP_REACHED` 409 | DONE | |
| US-256 | AC-256-04 | `grant`：同一 `holder_owner` 有 ACTIVE 席位 → `ALREADY_SEATED` 409（并发由唯一约束兜底） | DONE | |
| US-256 | AC-256-05 | `grant` → `SeatBinding.certified_user_of`（binding.py:77）找到则 `user=该用户` | DONE | 含手机号回退 |
| US-256 | AC-256-06 | `grant` 校验顺序 TERM_NOT_CONFIGURED → CAP_NOT_CONFIGURED → INVALID_VALUE 未改 | DONE | |
| US-256 | AC-256-07 | `IsAdmin` | DONE | |
| US-257 | AC-257-01 | residency/views.py `CertificationView.post` → `certify_owner(verified_owner_id=…)` → `SeatBinding.try_bind`（residency/services.py:45-90、binding.py:28） | DONE | 审计 `SEAT_BOUND`，不通知 |
| US-257 | AC-257-02 | residency/views.py `AdminAppealDecisionView.post` → `record_verified_owner(via="APPEAL")` | DONE | 无产权人名字的历史申诉不绑定 |
| US-257 | AC-257-03 | residency/phone_match.py `confirm` → `certify_one(verified_owner_id=…)`（auto_bind.py） | DONE | 见"架构偏差" |
| US-257 | AC-257-04 | `try_bind` 按 `holder_owner_id` 精确匹配，且重新核验姓名 | DONE | |
| US-257 | AC-257-05 | `active_*_ids` 排除空 user；`CommitteeQuery.active_seat(user_id)` 以用户为键 | DONE | 待绑定无任何权限；分母含待绑定（IFC-367） |
| US-257 | AC-257-06 | binding.py:68 `_conflict`（`bind_conflict_at` + `SEAT_BIND_CONFLICT`）；committee/views.py `seat_view.bind_state=CONFLICT`；AdminSeats.vue:28 | DONE | |
| US-257 | AC-257-07 | `try_bind` 只取 `user IS NULL` 的席位 | DONE | |
| US-257 | AC-257-08 | `Seat.position` 沿用；`/me` 身份由 `identity_view` 按席位职位显示 | DONE | |
| US-257 | AC-257-09 | `try_bind` 过滤 `term_end>=今天`，不改 term_start/term_end | DONE | |
| US-259 | AC-259-01~04、08、09 | 代码不改 `denominator_for_half_majority`/`judge_if_due`（`seat.user` 为空仍被 `effective_q` 计入 N）；业主代表不在 `position__in` | DONE | scratch 验证 N=4（含待绑定）、同意 2 → 未通过 |
| US-259 | AC-259-05 | resolutions/views.py `participation.expected`（同函数同口径）；参与人端点不含待绑定 | DONE | |
| US-259 | AC-259-06 | `try_bind` 不改 `status/term`，N 不变 | DONE | |
| US-259 | AC-259-07 | `revoke` 不变（对空 user 有效），N 随之减 1 | DONE | |

Should Have 故事 US-258 亦已实现：持有人/待绑定/冲突列表（admin/AdminSeats.vue:24-28）、待绑定可变更/撤销（`change` 的待绑定分支）、清册变化失效（MOD-142）、手机号不出现在 `holder`。

## 预期失败的既有用例（有意的行为变更，M-PM-009）

自验证（HEAD c3a10ce + 本批改动，同一台机器）：后端 Ran 1025，失败 7（B1~B7，全部列于下表，无其它失败；基线中的时段相关失败 `test_tc_int_504` 在白天本就通过，其根因已修复）；前端 482 条中失败 9（全部列于下表）；小程序 135/135 通过。

| # | 文件::用例 | 设计条目 | 失败原因 | 建议新断言 |
|---|---|---|---|---|
| B1 | backend/tests/integration/test_frontend_contract.py::ProductReviewFieldContractTests::test_tc_int_487_request_field_names_match_backend（`:563`） | MOD-152 / IFC-348 | `AdminSeats.vue` 不再发送 `user_id`，改发 `registry_owner_id` | `assertIn("registry_owner_id", src("frontend/src/admin/AdminSeats.vue"))` |
| B2 | 同文件::test_tc_int_488_me_housing_response_fields_vs_web_and_miniprogram_reads（`:583` 起） | MOD-143 / IFC-357（module_design 已预告） | `/me/housing` 顶层增 `real_names`，每套增 `co_owners` | 顶层集合改为 `{"summary","units","pending_review_count","real_names"}`，单元集合加 `"co_owners"` |
| B3 | backend/tests/integration/test_owner_auth_v2_contract.py::AppealContractTests::test_tc_int_713_both_clients_send_owner_name_unit_id_proof_ids（`:131`） | MOD-146 / IFC-363 | Web 侧不再调用 `createAppeal({…})`，改为 `submitAppeal(FormData)` | Web 侧读取 `UnitsAppeal.vue` 的 `form.append('…')` 键集 `{unit_id, owner_name, files}`；小程序侧 `{unit_id, owner_name, proof_ids}` 不变 |
| B4 | backend/tests/integration/test_phone_match_api.py::HousingFieldsTests::test_tc_int_957_housing_units_have_type_and_area（`:368`） | MOD-143 / IFC-357 | 每套房屋字段增 `co_owners` | 字段集合加 `"co_owners"` |
| B5 | backend/tests/integration/test_product_review_ac.py::TemplatePreflightAndRegressionTests::test_tc_int_477_ac_178_03_existing_endpoints_keep_fields（`:915`） | MOD-143 / IFC-357 | `/me/housing` 顶层增 `real_names` | 集合加 `"real_names"` |
| B6 | backend/tests/integration/test_product_review_api.py::HousingTests::test_resident_and_guest_get_empty_aggregates（`:67`） | MOD-143 / IFC-357 | 游客/同住人响应多 `real_names: []` | 期望体加 `"real_names": []` |
| B7 | backend/tests/integration/test_registry_filters_contract.py::RegistryFilterContractTests::test_tc_int_585_page_query_params_all_accepted_and_effective（`:49`） | MOD-151 / IFC-361 | `AdminRegistry.vue` 的 `load()` 现在多传 `sort`、`order` 两个查询参数 | 参数集合加 `"sort","order"`；`hits` 外另断言 `sort`/`order` 被后端识别（非法值 400）且不属于"过滤条件" |
| F1 | frontend/tests/layout_contract.spec.js::TC-INT-921 | MOD-146 / IFC-363 | Web 页面不再引用 `unitApi.createAppeal`（保留导出供兼容） | "必须被覆盖到"清单中 `unitApi.createAppeal` 改为 `unitApi.submitAppeal`，并加入 `resolutionApi.participants`、`admin.unitOptions`、`admin.ownerCandidates` |
| F2 | 同文件::TC-INT-923 | IFC-363 | api.js 导出函数集合新增 4 个：`unitApi.submitAppeal`、`resolutionApi.participants`、`admin.unitOptions`、`admin.ownerCandidates` | 基线集合加这 4 项 |
| F3 | frontend/tests/layout_css.spec.js::TC-UNIT-865 | MOD-150 / ADR-144 | `style.css` 新增 `@media (prefers-reduced-motion: no-preference)`（设计要求新增动效全部包在其内） | 允许集合加 `(prefers-reduced-motion: no-preference)`，断点断言仍只含 768px 一对 |
| F4 | frontend/tests/owner_auth_v2.spec.js::TC-UNIT-669 | MOD-146（Q-B18-29=A） | 提交按钮不再因未选房屋而禁用，点击后提示"请选择到具体户" | 断言按钮可点；未选房屋点击提示"请选择到具体户"且不发 POST /appeals |
| F5 | 同文件::TC-UNIT-670 | MOD-146 | 提示文案由"请先上传产权证明"改为"请至少选择 1 份产权证明"；选择阶段不再上传 | 断言新文案；未发 POST /appeals |
| F6 | 同文件::TC-UNIT-671 | MOD-146 / REQ-FUNC-239 | 选文件只暂存（显示"已选 2 份"，无"已上传"）；提交为 `POST /appeals` 的 FormData（unit_id、owner_name、files×2）；成功后暂存清空 | 触发 `on-change` 选 2 文件→断言 `attachmentApi.upload` 调用数 0；提交断言 `http.post('/appeals', FormData)` 的键集与文件数 |
| F7 | 同文件::TC-UNIT-672 | MOD-146 | 第 6 份被拦的提示为"最多 5 份"，且选择阶段不发上传请求 | 断言暂存数 5、提示"最多 5 份" |
| F8 | frontend/tests/product_review_ui.spec.js::TC-UNIT-541 | MOD-152 | 赋予席位对话框由用户搜索（`UserPicker`、`user_id`）改为 `SeatHolderPicker`（逐级选房 + 业主单选，提交 `registry_owner_id`） | 对话框含 `UnitCascader` 与业主单选；提交体含 `registry_owner_id` 且不含 `user_id` |
| F9 | frontend/tests/ui_blocks.spec.js::决议卡片三段比例（AC-087-02） | MOD-149 / REQ-FUNC-245 | 进度条宽度分母由已投票数改为应参与人数（`participation.expected`），无 `participation` 时分母为 0 → "暂无表决人" | 夹具加 `participation: {voted, expected}`，按 `count/expected` 断言宽度；增加"已参与 a / b · pct%"与"进行中/已结束"断言 |

## 迁移

| 文件 | 内容摘要 | 可逆 |
|---|---|---|
| backend/apps/committee/migrations/0002_seat_registry_holder.py | 依赖 `committee 0001_initial`、`registry 0005_regenerate_specific_part`（`ls` 核实为最新）；`AlterField Seat.user`（可空）、`AddField` holder_owner/holder_unit_text/holder_name/bound_at/bind_conflict_at、`AddConstraint uniq_seat_active_per_owner` | 是（回滚前须撤销所有待绑定席位） |
| backend/apps/residency/migrations/0005_membership_registry_owner.py | 依赖 `residency 0004_phone_match_prompt`、`registry 0005`；`AddField Membership.registry_owner`（FK SET_NULL，可空） | 是 |

两个文件均为手写，文件头为手写说明（不含 "Generated by Django"）。`makemigrations --check --dry-run` 输出 "No changes detected"（仅检查，未提交产物）。不回填存量 `Membership.registry_owner`（ADR-138）。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| [DEVIATION] `SEAT_GRANTED` 审计 detail：用户 ID 授予路径不含 `holder` 键，仅清册业主授予路径含 `holder` | IFC-347 `grant`（"holder: … \| None"） | 既有用例 TC-INT-708 以 `assertEqual(detail, {"user_id", "position"})` 精确断言，NFUNC-050 要求零回归 | 无手机号泄露；审计读取方需容忍 `holder` 缺省 |
| [DEVIATION] 手机号匹配确认路径：`certify_one` 在 `certify_owner` 成功后同事务调用 `record_verified_owner(via="PHONE_MATCH")`，而非向 `certify_owner` 传 `verified_owner_id` | IFC-354（`certify_one` 透传） | 既有用例 TC-INT-308/TC-UNIT-916 用 `side_effect=flaky(user_id, unit_id, source, origin=None, detail_extra=None)` 替换 `certify_owner`，新增关键字参数会使其全部失败 | 功能等价（写 registry_owner 并绑定席位）；手机号匹配产生的 `CERTIFY_BY_REGISTRY` 审计 detail 不含 `registry_owner_id`（`SEAT_BOUND` 审计含 via 与 holder） |
| 新增 `frontend/src/shared/unitSearch.js`（`rankOptions`） | MOD-147 仅列 `UnitCascader.vue` | 检索排序逻辑抽成纯函数便于测试；`UnitCascader.vue` 内 `<script setup>` 无法导出 | 无 |
| `votes` 数组从 `resolution_view` 删除 | NFUNC-050"既有字段不变" | ADR-141 已记录的有意例外，用户答复 Q3=A | 前端与小程序均不读取 |

## 开放问题

- [ASSUMPTION] `seat_view.holder.kind`：`holder_owner_id` 或 `holder_name` 非空为 `REGISTRY_OWNER`，否则 `USER`；`unit_text`/`owner_name` 缺省为 `null`。
- [ASSUMPTION] 绑定冲突每次重试均更新 `bind_conflict_at` 并写一条 `SEAT_BIND_CONFLICT` 审计（同一席位重复触发会有多条）。
- [ASSUMPTION] 待绑定席位被"变更职位"时，新席位仍以同一清册业主重新走 `grant(registry_owner_id=…)`（若其间该业主已有认证用户，则直接绑定）。
- [ASSUMPTION] `AdminSeatListCreateView.post`：`user_id` 与 `registry_owner_id` 均缺失/均给出 → 400 `INVALID_VALUE`（消息改为"须恰好给一个"，原缺失 `user_id` 的 400 消息为"user_id 不合法"，错误码相同）。
- [ASSUMPTION] 提交申诉的 axios 超时放宽为 120 s（原默认 15 s，5×10 MB 上传不够）；nginx 60m 由部署阶段处理，本批未改任何服务器配置。
- 观察（未改）：`apps/claims/services.py:19,40` 的 `claim.decided_at.date()` 同样取 UTC 日期（`occurred_on` 回退值），不在 `now().date()` 同类范围内，建议 PM 视情况另立缺陷；`date.today()` 受 Django `TIME_ZONE` 影响为本地日期，无问题。
- 人工验证项（NOT_TESTABLE，随 module_design）：三主题下卡片悬停/导航选中动效；系统"减少动效"下无动画；50 MB 上传经 nginx 的真实通过性。
- 无 `TODO(IFC-NNN)` stub、无 `[UNSOURCED]`、无 `[UNRESOLVED-CRITICAL]`。
