<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-27T09:01:31.6049532+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录模块设计

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-228 | 通用审批已处理查询 | 修改 `backend/apps/approval/views.py` | 在现有待办列表中增加 handled 查询、本人最近动作摘要、状态与分页 | REQ-FUNC-385、386；US-370、371 | 现有 ApprovalInstance、ApprovalAction、ApprovalStepState |
| MOD-229 | Web 通用审批历史视图 | 修改 `frontend/src/portal/Tasks.vue` | 提供待办/已处理切换、历史字段、筛选分页和只读时间线入口 | REQ-FUNC-385～387；US-370、371 | MOD-228（IFC-454）、既有详情（IFC-456） |
| MOD-230 | 同住人已通过查询 | 修改 `backend/apps/residency/views.py`、`backend/apps/residency/urls.py` | 按当前有效产权返回固定 APPROVED 状态记录 | REQ-FUNC-388；US-372 | 现有 ResidentApplication、Membership |
| MOD-231 | Web 同住人已通过视图 | 修改 `frontend/src/portal/units/UnitsReview.vue`、`frontend/src/shared/api.js` | 提供已通过记录区域并在处理后同步刷新 | REQ-FUNC-388；US-372 | MOD-230（IFC-455、IFC-457） |
| MOD-232 | 申请人记录回归保护 | 沿用 `backend/apps/residency/views.py` 的 `ResidentApplicationMineView`、`frontend/src/portal/units/UnitsApplicationRecords.vue`；不修改 | 保持申请人仅查看本人记录及通过结果 | REQ-FUNC-389；US-373 | 既有 IFC-392c |

## 模块详情

### MOD-228 通用审批已处理查询（修改现有）

- 职责：在 `TaskListView` 内增加 handled 分支；缺省与 `view=todo` 完全沿用原待办查询。handled 不按整单状态过滤，只按本人实际 `APPROVE`/`REJECT` 动作收录。
- 接口 IFC-454（HTTP）：`TaskListView.get(self, request) -> rest_framework.response.Response`。
  - 方法与路径：`GET /approval/tasks`。
  - 鉴权：沿用现有登录认证与 `IsCommitteeMember`；离任后不扩大列表权限。
  - 查询参数：`view: "todo" | "handled" = "todo"`；`scope?: "RESOLUTION" | "EXPENSE" | "INCOME"`；`page: int >= 1 = 1`；`page_size: int = 20，范围 1～100`。
  - 输入校验：非法 `view`、`scope`、非整数/越界分页参数返回 HTTP 400 `INVALID_QUERY`；`page_size>100` 按现有上限归为 100，小于 1 归为 1。空 `scope` 等价未传。
  - 待办响应：保持 `backend/apps/approval/views.py:239-253` 的字段和排序，不增加本人动作字段。
  - 已处理响应：`{count: int, page: int, page_size: int, results: HandledApprovalTask[]}`。
  - `HandledApprovalTask`：`instance_id: int`、`scope: str`、`subject_type: str`、`subject_id: int`、`subject_title: str`、`submitter: PersonRef | null`、`submitter_label: str`、`submitted_at: datetime`、`status: "PENDING" | "APPROVED" | "REJECTED" | "WITHDRAWN"`、`step_order: int | null`、`step_name: str | null`、`step_strategy: "ANY" | "ALL" | null`、`my_action: "APPROVE" | "REJECT"`、`my_acted_at: datetime`、`my_comment: str`、`my_step_order: int | null`、`my_step_name: str | null`。
  - 字段口径：`my_*` 取当前用户在该实例最近一次通过/拒绝动作；`step_*` 仅在整单 `PENDING` 时表示当前步骤，终局/撤回时为 `null`；同一 `instance_id` 只出现一次。结果按 `my_acted_at` 降序、同刻按 `instance_id` 降序，scope 过滤后的 `count` 为去重实例总数。
  - 查询约束：使用实例动作关系去重，并预取当前用户动作与步骤状态；不得在 Python 中把“曾被指定”当作已处理。
  - 错误：未认证/非现任委员沿用权限组件的 401/403；实例不存在不属于列表请求错误。

### MOD-229 Web 通用审批历史视图（修改现有）

- 职责：在 `Tasks.vue` 增加 `view: "todo" | "handled"` 状态与两个视图入口；切换视图或 scope 时回到第 1 页，复用 `usePaging`。
- 调用契约：`approvalApi.tasks(scope, {...params, view})`；现有函数已透传额外 params，无需为本接口新增 API 方法。
- 展示：handled 行显示业务类型、单据标题、提交人、提交时间、本人动作、本人处理时间、本人意见和整单状态；整单 `PENDING` 时另显示当前步骤。todo 行保持现有字段与操作。
- 空态：todo 为“暂无待办”，handled 为“暂无已处理记录”。两种视图均显示“审批过程”入口；只有 todo 显示“同意”“拒绝”。
- 依赖：MOD-228 与既有 `ApprovalTimeline`；不新增路由、状态仓库或写操作。

### MOD-230 同住人已通过查询（修改现有）

- 职责：新增 `ResidentApplicationApprovedView`，每次请求实时计算当前用户有效 `HEAD`/`OWNER` 专有部分集合，再固定过滤 `ResidentApplication.status="APPROVED"`。
- 接口 IFC-455（HTTP）：`ResidentApplicationApprovedView.get(self, request) -> rest_framework.response.Response`。
  - 方法与路径：`GET /resident-applications/approved`，在 `backend/apps/residency/urls.py` 注册，且置于 `resident-applications/<int:application_id>/...` 等动态路径之外，避免标识冲突。
  - 鉴权：沿用现有登录认证与 `IsMember`；数据权限由当前有效产权关系约束，不能仅按 `decided_by` 放宽。
  - 请求：无请求体、无状态筛选参数；意外查询参数不改变固定的 APPROVED 过滤。
  - 响应：HTTP 200，数组 `ApprovedResidentApplication[]`，按 `decided_at` 降序、同刻按 `id` 降序。
  - `ApprovedResidentApplication`：`id: int`、`unit: {unit_id: int, specific_part: str}`、`status: "APPROVED"`、`applicant_name: str`、`created_at: datetime`、`decided_at: datetime | null`、`decision_note: str | null`、`reject_reason: null`、`withdrawn_at: datetime | null`、`previous_application_id: int | null`、`applicant: {id: int, account_no: str, nickname: str, phone: str | null}`。
  - 序列化：复用 `application_view`（`backend/apps/residency/views.py:462-469`）与 to-review 的申请人摘要/手机号脱敏方式（同文件 513-518）；`applicant_name` 为申请人实名快照，`decision_note` 为处理备注。
  - 空结果：无当前产权或无通过记录均返回 `[]`；不返回其他专有部分或其他状态数据。

### MOD-231 Web 同住人已通过视图（修改现有）

- 职责：在 `UnitsReview.vue` 的现有审批区域增加“已通过记录”视图/分区，与“待我审批”入口同页可达；通过处理后同时刷新待办和已通过记录。
- 接口 IFC-457（前端函数，JSDoc 等价契约）：`unitApi.approvedResidentApplications(): Promise<ApprovedResidentApplication[]>`，实现为 `GET /resident-applications/approved`，无参数、无写副作用。
- 展示：每条记录显示专有部分、申请人昵称/账号、申请人实名、提交时间、处理时间、状态“通过”和处理备注；空态为“暂无已通过的同住人申请”。不显示通过、拒绝、撤回或关闭操作。
- 依赖：MOD-230；沿用 `useHousingStore.refresh()` 更新待审角标，不修改 `myApplications` 的数据来源。

### MOD-232 申请人记录回归保护（沿用现有，不改代码）

- 职责：保留 `ResidentApplicationMineView.get` 的 `applicant=request.user` 查询与 `UnitsApplicationRecords.vue` 的通过状态、处理时间、处理备注展示。
- 接口：继续复用既有 IFC-392c 与 `unitApi.myResidentApplications()`；不得改成 MOD-230 的产权查询，也不得拼接他人记录。
- 验收：申请人无该专有部分产权仍可见本人通过记录；其他申请人的通过记录不出现。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-385 | US-370 | MOD-228、MOD-229 |
| REQ-FUNC-386 | US-370、US-371 | MOD-228、MOD-229 |
| REQ-FUNC-387 | US-371 | MOD-229、IFC-456（既有详情复用） |
| REQ-FUNC-388 | US-372 | MOD-230、MOD-231 |
| REQ-FUNC-389 | US-373 | MOD-232 |

## 依赖关系

- MOD-229 → MOD-228（IFC-454）。
- MOD-229 → 既有 `ApprovalTimeline` / `InstanceDetailView`（IFC-456：`GET /approval/instances/{instance_id}`，响应为 `ApprovalEngine.timeline(...) -> dict`；沿用登录认证、`IsMemberOrAdmin` 与 `ApprovalEngine.can_view`，无权返回 HTTP 403 `FORBIDDEN`；路径参数必须为正整数，不匹配现有路由时返回 404）。
- MOD-231 → MOD-230（IFC-455、IFC-457）。
- MOD-232 仅依赖既有本人申请接口，不依赖 MOD-230/231。
- 已检查：无循环依赖；所有新增调用均为 Web → 后端单向依赖。

## 数据迁移

无。现有 `ApprovalAction`、`ApprovalStepState`、`ApprovalInstance` 与 `ResidentApplication` 已包含所需动作、步骤、状态、处理时间与备注字段（`backend/apps/approval/models.py:49-102`、`backend/apps/residency/models.py:58-85`）。不新增表、字段、索引或数据回填；最新现有迁移分别为 approval `0003_approval_steps.py`、residency `0006_appeal_center.py`。

## 受影响的运行单元 / 构建

- 后端 `ocap-backend`（gunicorn）：代码发布后需重启；无数据库迁移。
- Web 前端：需运行画像 P4 的测试和 `VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/`，再按既有 tar/nginx 静态发布流程更新。
- CI：沿用 GitHub Actions，仅执行测试与构建，不自动部署。
- 小程序、定时任务、Freeark 服务与数据库结构：不受影响。

## 领域与外部依赖出处

本批不调用画像 P11-3 的微信、短信或邮件 API，不涉及 P11-1 硬件或 P11-2 算法；上述接口均为本仓库内部 HTTP 契约。

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| 不适用 | 无专用硬件、算法或闭源 API 契约事实 | 不适用 |
