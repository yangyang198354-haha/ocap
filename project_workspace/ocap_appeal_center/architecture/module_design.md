<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T09:43:33+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
    <file>project_workspace/ocap/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — 申诉与同住人申请记录中心（Web 用户端）

## 模块总览

| MOD | 名称 | 文件（新建/修改，路径相对仓库根） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-168 | residency 申诉生命周期与记录（后端） | 修改 `backend/apps/residency/models.py`、`views.py`、`urls.py`、`services.py`；新建 `backend/apps/residency/migrations/0006_appeal_center.py` | 申诉撤回、重新提交关联、管理员备注、我的申诉返回字段扩展；审计留痕 | REQ-FUNC-290/291/292、REQ-NFUNC-059/060；US-292/293/294 | MOD-001（审计）、MOD-005（既有 residency） |
| MOD-169 | residency 同住申请生命周期、实名与房屋聚合 | 修改 `backend/apps/residency/models.py`、`views.py`、`urls.py`、`services.py`、`housing.py`；共用 `migrations/0006_appeal_center.py` | 同住申请撤回、重新提交关联、本人实名、审批备注与驳回原因；身份页同住人实名数据 | REQ-FUNC-294/295/296、REQ-NFUNC-059/060；US-296/297/298 | MOD-001、MOD-005、MOD-168（同一迁移文件） |
| MOD-170 | Web 申诉中心（双 Tab 与记录） | 新建 `frontend/src/portal/units/AppealCenter.vue`；修改 `UnitsAppeal.vue`、`UnitsMyAppeals.vue`、`frontend/src/portal/Units.vue`、`frontend/src/layout/menus.js`、`frontend/src/router/index.js` | 单入口双 Tab、旧地址兼容、记录列表展示结果/备注/驳回原因、撤回与重新提交交互 | REQ-FUNC-289/290/291/292；US-291/292/293/294 | MOD-173（API/状态）、MOD-168（后端契约） |
| MOD-171 | Web 同住申请中心（双 Tab、实名表单与记录） | 新建 `frontend/src/portal/units/UnitsApplicationForm.vue`、`UnitsApplicationRecords.vue`；修改 `frontend/src/portal/units/UnitsApplications.vue`、`frontend/src/portal/Units.vue` | 发起申请/申请记录双 Tab、本人实名输入与校验、提交后切到记录 Tab、记录撤回与重新提交 | REQ-FUNC-293/294/295；US-295/296/297 | MOD-173、MOD-169 |
| MOD-172 | Web 身份与房屋页同住人实名 | 修改 `frontend/src/portal/units/UnitsIdentity.vue` | 同住人列表展示实名；本人同住人实名并入汇总真实姓名；缺失显示“—” | REQ-FUNC-296；US-298 | MOD-173、MOD-169（IFC-389） |
| MOD-173 | Web 共享契约与状态（API、store、标签、路由参数） | 修改 `frontend/src/shared/api.js`、`frontend/src/stores/housing.js`、`frontend/src/shared/labels.js`；`frontend/src/router/index.js` 的 props 约定由 MOD-170 落地 | 新增撤回/重新提交/实名/备注的 API 函数、审计状态字段、`WITHDRAWN` 标签、初始 Tab 的 props 契约 | REQ-FUNC-289~296（前端契约侧） | 无（仅调用既有 HTTP 客户端） |

## 模块详情

### MOD-168 residency 申诉生命周期与记录

**职责**：申诉状态的唯一事实来源扩展；撤回、重新提交关联、管理员备注与记录展示字段。

**数据表变更**（`residency_appeal`）：

- `status`: `varchar(12)`，枚举新增 `WITHDRAWN`（“已撤回”）；既有 `PENDING/APPROVED/REJECTED/CLOSED` 不变。
- `decision_note`: `varchar(500) null`，管理员处理备注（通过/驳回均可填）。
- `withdrawn_at`: `datetime null`，撤回时间。
- `previous_appeal_id`: 自关联外键 `residency_appeal(id)`，`null`、`on_delete=SET_NULL`、`related_name="resubmitted_appeals"`。
- 既有 `reject_reason`（`varchar(500) null`）语义不变：驳回时必填。
- 待审唯一约束 `(user, unit, pending_slot)`（`models.py:48`）保持不变；撤回时把 `pending_slot` 置 `NULL` 以释放 C-360 限制。

**接口**：

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-381 | `POST /api/v1/appeals/{appeal_id}/withdraw`（无请求体）→ 200 `AppealView` | `M`（`IsMember`）+ 对象级：记录 `user_id` 必须等于 `request.user.id` | 不存在 → 404 `NOT_FOUND`；非本人 → 403 `FORBIDDEN`；状态非 `PENDING`（含已通过/已驳回/已关闭/已撤回）→ 409 `NOT_PENDING`（C-359）；成功写审计 `APPEAL_WITHDRAWN`，`withdrawn_at=now()`、`pending_slot=NULL` |
| IFC-382 | `POST /api/v1/appeals`（JSON 或 multipart，沿用 `views.py:136-222`）请求体新增可选 `previous_appeal_id: int \| null` → 201 `AppealView` | `M` | 沿用既有校验（`unit_id`、`owner_name≤64`、1~5 份证明、`APPEAL_PENDING`）。`previous_appeal_id` 存在时：必须属于当前用户且 `status="WITHDRAWN"`，否则 400 `INVALID_PREVIOUS_RECORD`；来源记录与目标房屋可不同（D-02/A-02）。成功新建记录并保存关联；审计 `APPEAL_SUBMITTED.detail.previous_appeal_id` |
| IFC-383 | `GET /api/v1/appeals/mine` → `list[AppealView]`（最近 100 条，按 `submitted_at` 倒序） | `M` | 沿用 `MINE_LIMIT`（`views.py:30,132-134`）。响应新增 `decision_note: str \| null`、`withdrawn_at: datetime \| null`、`previous_appeal_id: int \| null`；`status` 可能为 `WITHDRAWN` |
| IFC-384 | `POST /api/v1/admin/appeals/{appeal_id}/decision` 请求体 `{decision: "APPROVE" \| "REJECT", reject_reason?: str, note?: str}` → 200 `AppealView` | `A`（`IsAdmin`） | 沿用“已处理 → 409 `ALREADY_DECIDED`、已关闭 → 409 `ALREADY_CLOSED`”；`REJECT` 仍要求 `reject_reason` 非空且 ≤500；`note` 可选、≤500，超长 → 400 `INVALID_VALUE` 且不落库；成功写入 `decision_note`，审计 `APPEAL_DECIDED.detail.note`（已脱敏） |
| IFC-390a | 内部：`class AppealLifecycle:`<br>`def withdraw(self, *, user_id: int, appeal_id: int) -> Appeal`（在调用方事务内；不满足 C-359 抛 `ApiError`）<br>`def validate_previous(self, *, user_id: int, previous_id: int \| None) -> Appeal \| None`（返回来源记录或 `None`；非法抛 `ApiError("INVALID_PREVIOUS_RECORD", …, 400)`）<br>`def view(self, appeal: Appeal) -> AppealView` | 内部 | 所有写方法要求调用方已开启事务；`withdraw` 使用条件更新 `WHERE id=? AND user_id=? AND status='PENDING'` 防并发重复撤回 |

**类型定义**：

```python
AppealStatus = Literal["PENDING", "APPROVED", "REJECTED", "CLOSED", "WITHDRAWN"]

class AppealView(TypedDict):
    id: int
    unit: UnitBrief                 # 沿用 views._unit_view
    status: AppealStatus
    submitted_at: datetime
    decided_at: datetime | None
    reject_reason: str | None       # 驳回原因；仅 REJECTED 有值
    decision_note: str | None       # 处理备注；空为 None，前端显示 "—"
    withdrawn_at: datetime | None
    previous_appeal_id: int | None  # 重新提交来源；首提为 None
```

**依赖**：MOD-001（`AuditService`）、既有 MOD-005 模块内其它组件。**外部依赖**：无新增。

### MOD-169 residency 同住申请生命周期、实名与房屋聚合

**职责**：同住申请的撤回/重新提交、本人实名快照、审批备注与驳回原因；“我的身份与房屋”聚合中的同住人实名。

**数据表变更**（`residency_resident_application`）：

- `status`: `varchar(12)`，枚举新增 `WITHDRAWN`。
- `applicant_name`: `varchar(64) not null default ""`，提交时的本人实名快照（C-361：不参与认证/清册匹配）。
- `reject_reason`: `varchar(500) null`，驳回原因（选填，见 ADR-163/A-01）。
- `decision_note`: `varchar(500) null`，产权业主处理备注。
- `withdrawn_at`: `datetime null`。
- `previous_application_id`: 自关联外键，`null`、`on_delete=SET_NULL`、`related_name="resubmitted_applications"`。
- 待审唯一约束 `(applicant, unit, pending_slot)`（`models.py:66`）不变；撤回置 `pending_slot=NULL`。

**接口**：

| IFC | 签名 / 路由 | 鉴权 | 输入校验与错误 |
|---|---|---|---|
| IFC-385 | `POST /api/v1/resident-applications` 请求体 `{unit_id: int, applicant_name: str, previous_application_id?: int \| null}` → 201 `ApplicationView` | `M` | 沿用 `unit_id` 校验（不存在 404 `NOT_FOUND`、无有效产权业主 409 `UNIT_HAS_NO_OWNER`、已是业主 409 `ALREADY_CERTIFIED`、重复待审 409 `APPLICATION_PENDING`）。`applicant_name`：`str.strip()` 后非空，否则 400 `NAME_REQUIRED`；长度 ≤64，否则 400 `INVALID_VALUE`。`previous_application_id` 必须属于当前用户且 `WITHDRAWN`，否则 400 `INVALID_PREVIOUS_RECORD` |
| IFC-386 | `POST /api/v1/resident-applications/{application_id}/withdraw` → 200 `ApplicationView` | `M` + 对象级本人校验 | 不存在 404；非本人 403 `FORBIDDEN`；非 `PENDING` → 409 `NOT_PENDING`；成功写 `withdrawn_at`、`pending_slot=NULL`、审计 `RESIDENT_APPLICATION_WITHDRAWN` |
| IFC-387 | `GET /api/v1/resident-applications/mine` → `list[ApplicationView]`（最近 100 条，按 `created_at` 倒序） | `M` | 响应新增 `applicant_name`、`reject_reason`、`decision_note`、`withdrawn_at`、`previous_application_id`；`status` 可能为 `WITHDRAWN` |
| IFC-388 | `POST /api/v1/resident-applications/{id}/decision` 请求体 `{decision: "APPROVE" \| "REJECT", reject_reason?: str, note?: str}` → 200 `ApplicationView`；`GET /api/v1/resident-applications/to-review` 响应新增 `applicant_name` | `M` + 对象级：审批人须为该专有部分有效 `OWNER/HEAD` | 非本房产权业主 403 `FORBIDDEN`；已处理 409 `ALREADY_DECIDED`、已关闭 409 `ALREADY_CLOSED`；`reject_reason`、`note` 均 ≤500，超长 400 `INVALID_VALUE`；通过后建立 `RESIDENT` 成员关系（沿用 `views.py:419-423`）；审计 `RESIDENT_APPLICATION_DECIDED.detail.{decision, reject_reason, note}` |
| IFC-389 | `GET /api/v1/me/housing` → `HousingPayload`（扩展） | `M` | `units[].residents[].real_name: str \| null`；`real_names` 并入本人作为同住人的实名（去重保序）。批量查询：按业主房屋与同住人 id 一次取最近 `APPROVED` 申请，查询数不随行数增长；无实名返回 `None`，前端显示“—” |
| IFC-390b | 内部：`class ResidentApplicationLifecycle:`<br>`def create(self, *, applicant: User, unit_id: int, applicant_name: str, previous_id: int \| None) -> ResidentApplication`<br>`def withdraw(self, *, applicant_id: int, application_id: int) -> ResidentApplication`<br>`def decide(self, *, reviewer: User, application_id: int, decision: str, reject_reason: str \| None, note: str \| None) -> ResidentApplication` | 内部 | 写方法在调用方事务内；`decide` 使用条件更新 `WHERE status='PENDING'`（沿用 `views.py:410-418`）；`reject_reason` 为选填（A-01） |

**类型定义**：

```python
ApplicationStatus = Literal["PENDING", "APPROVED", "REJECTED", "CLOSED", "WITHDRAWN"]

class ApplicationView(TypedDict):
    id: int
    unit: UnitBrief
    status: ApplicationStatus
    applicant_name: str              # 历史数据为 ""，前端显示 "—"
    created_at: datetime
    decided_at: datetime | None
    reject_reason: str | None
    decision_note: str | None
    withdrawn_at: datetime | None
    previous_application_id: int | None

class HousingResident(TypedDict):
    user_id: int
    nickname: str | None
    account_no: str
    real_name: str | None            # 新增：来自最近一条 APPROVED 申请的 applicant_name
    joined_at: datetime
```

**依赖**：MOD-001、MOD-168（共用迁移文件，迁移顺序先申诉后同住申请）、既有 `housing.py` 聚合。**外部依赖**：无新增。

### MOD-170 Web 申诉中心（双 Tab 与记录）

**职责**：把“认证申诉”与“我的申诉”合并为一个二级菜单入口，页内 Tab 承载；记录列表展示处理结果、备注、驳回原因，提供撤回与重新提交。

**文件**：

- 新建 `frontend/src/portal/units/AppealCenter.vue`：宿主组件，`el-tabs` 两个 Tab（`appeal` / `mine`），默认按 props `initialTab` 决定；Tab 内容用已渲染即保留的方式承载子组件（切换不销毁）。
- 修改 `frontend/src/portal/units/UnitsAppeal.vue`：保留现有表单逻辑，作为“认证申诉”Tab 内容；接收 `prefillFrom`（可选，用于从已撤回记录带入房屋/姓名）。
- 修改 `frontend/src/portal/units/UnitsMyAppeals.vue`：记录列表增加“处理结果、处理备注、驳回原因、已撤回标签、撤回/重新提交操作”，空状态沿用“暂无申诉”。
- 修改 `frontend/src/portal/Units.vue`：`appeal` 与 `appeals` 两个 section 都渲染 `AppealCenter`，后者初始 Tab 为 `mine`。
- 修改 `frontend/src/layout/menus.js`：删除 `units.appeals` 节点，仅保留 `units.appeal`（label“认证申诉”）。
- 修改 `frontend/src/router/index.js`：`units/appeal` 传 `{section:'appeal', initialTab:'appeal'}`；旧 `units/appeals` 传 `{section:'appeal', initialTab:'mine'}`（AC-291-03）。

**接口**：

| IFC | 签名 | 鉴权 | 说明 |
|---|---|---|---|
| IFC-392a | `AppealCenter` props：`{ initialTab: "appeal" \| "mine", prefill?: { unitId: number \| null, ownerName: string } }`；事件：`submitted()`（表单提交成功后切换到 `mine` 并刷新列表）、`changed()`（撤回/重新提交成功后刷新） | 前端组件（登录态由父级路由保证） | Tab 切换用 `v-model:activeName`；两个子组件保持挂载，满足 AC-291-02 |
| IFC-392b | `UnitsMyAppeals` 触发 `withdraw(appealId: number)` → 调用 MOD-173 的 `withdrawAppeal`；`resubmit(appeal: AppealView)` → 切换到“认证申诉”Tab 并带入 `unit_id`/`owner_name`，提交时携带 `previous_appeal_id` | 前端组件 | 撤回需二次确认；失败保留当前状态并提示 |

**依赖**：MOD-173（API 与标签）、MOD-168（后端 IFC-381/382/383/384）。

### MOD-171 Web 同住申请中心（双 Tab、实名表单与记录）

**职责**：把同住申请页拆为“发起申请 / 申请记录”两个 Tab；发起时填写本人实名；记录列表与申诉记录同口径并支持撤回/重新提交。

**文件**：

- 修改 `frontend/src/portal/units/UnitsApplications.vue`：改为双 Tab 宿主，默认“发起申请”；提交成功后自动切到“申请记录”并刷新。
- 新建 `frontend/src/portal/units/UnitsApplicationForm.vue`：房屋选择 + 本人实名输入 + 提交；接收 `prefill`（重新提交时带入房屋与实名）。
- 新建 `frontend/src/portal/units/UnitsApplicationRecords.vue`：记录列表（专有部分、状态、提交/处理时间、驳回原因、审批人备注、撤回/重新提交），空状态“暂无同住人申请”。
- 修改 `frontend/src/portal/Units.vue`：`applications` section 渲染新的宿主。

**接口**：

| IFC | 签名 | 鉴权 | 说明 |
|---|---|---|---|
| IFC-392c | `UnitsApplications` props：`{ initialTab?: "form" \| "records", prefill?: { unitId: number \| null, applicantName: string } }`；事件 `submitted()`、`changed()` | 前端组件 | 提交成功后 `activeName='records'`（AC-295-03） |
| IFC-392d | `UnitsApplicationForm` 校验：实名 `trim()` 非空、长度 ≤64；提交体 `{unit_id, applicant_name, previous_application_id?}`；错误码 `NAME_REQUIRED`/`INVALID_VALUE` 映射为页面提示（AC-297-01/02） | 前端组件 | 房屋未选时按钮禁用；失败保留已填内容 |

**依赖**：MOD-173、MOD-169（IFC-385/386/387/388）。

### MOD-172 Web 身份与房屋页同住人实名

**职责**：业主视角的同住人列表显示实名；本人为同住人时汇总“真实姓名”包含本人实名；缺失显示“—”。

**文件**：修改 `frontend/src/portal/units/UnitsIdentity.vue`：同住人行增加 `real_name || '—'`；`housing.real_names` 已由后端扩展，无需额外分支。

**接口**：

| IFC | 签名 | 鉴权 | 说明 |
|---|---|---|---|
| IFC-392e | 展示契约：`resident.real_name: string \| null`；渲染顺序“实名 · 昵称（账号） · 加入于 时间”；`real_names` 为空时显示“—”（沿用 `UnitsIdentity.vue:13`） | 前端组件 | 不新增按钮或操作 |

**依赖**：MOD-173、MOD-169（IFC-389）。

### MOD-173 Web 共享契约与状态

**职责**：集中新增前端 API 函数、store 字段与状态标签，避免各页面重复拼装契约。

**文件**：修改 `frontend/src/shared/api.js`、`frontend/src/stores/housing.js`、`frontend/src/shared/labels.js`。

**接口**：

| IFC | 签名（JavaScript，含类型注释） | 鉴权 | 说明 |
|---|---|---|---|
| IFC-391a | `unitApi.withdrawAppeal(appealId: number): Promise<AppealView>`；`unitApi.withdrawResidentApplication(applicationId: number): Promise<ApplicationView>` | 令牌由 `http` 拦截器注入（沿用 `api.js`） | 分别 POST 到 IFC-381 / IFC-386 |
| IFC-391b | `unitApi.createAppeal(data: { unit_id: number, owner_name: string, proof_ids?: string[], previous_appeal_id?: number } \| FormData): Promise<AppealView>`（沿用现有 `submitAppeal(form)` 处理 multipart；JSON 分支补 `previous_appeal_id`） | 同上 | 兼容旧调用 |
| IFC-391c | `unitApi.createResidentApplication(data: { unit_id: number, applicant_name: string, previous_application_id?: number }): Promise<ApplicationView>`；`unitApi.decideResidentApplication(id: number, decision: "APPROVE" \| "REJECT", options?: { reject_reason?: string, note?: string }): Promise<ApplicationView>` | 同上 | 旧两参调用保持可用 |
| IFC-391d | `admin.decideAppeal(id: number, decision: "APPROVE" \| "REJECT", rejectReason?: string, note?: string): Promise<AppealView>` | 管理员令牌（沿用 `adminHttp`） | 与 IFC-384 对应 |
| IFC-391e | `statusLabel('appeal' \| 'application', status: "PENDING" \| "APPROVED" \| "REJECTED" \| "CLOSED" \| "WITHDRAWN"): string`（`WITHDRAWN` → “已撤回”） | — | 纯函数，未知状态回退原值 |
| IFC-391f | `useHousingStore().myAppeals: AppealView[]`、`.myApplications: ApplicationView[]`（沿用 `loadLists()` 同时加载） | — | 撤回/重新提交后调用 `loadLists()` |

**依赖**：无（仅复用既有 `http`/`adminHttp`）。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-289 | US-291 | MOD-170、MOD-173 |
| REQ-FUNC-290 | US-292 | MOD-168（IFC-383）、MOD-170 |
| REQ-FUNC-291 | US-293 | MOD-168（IFC-383/384）、MOD-170 |
| REQ-FUNC-292 | US-294 | MOD-168（IFC-381/382/383）、MOD-170 |
| REQ-FUNC-293 | US-295 | MOD-171 |
| REQ-FUNC-294 | US-296 | MOD-169（IFC-386/387/388）、MOD-171 |
| REQ-FUNC-295 | US-297 | MOD-169（IFC-385）、MOD-171 |
| REQ-FUNC-296 | US-298 | MOD-169（IFC-389）、MOD-172 |
| REQ-NFUNC-059 | US-293/294/296 | MOD-168、MOD-169（审计与长度校验） |
| REQ-NFUNC-060 | US-292/293/296/297/298 | MOD-168、MOD-169（空态与 100 条上限）、MOD-170、MOD-171、MOD-172（占位展示） |

## 依赖关系

- MOD-170 → MOD-173（IFC-391a/b/e/f）、MOD-168（IFC-381/382/383/384）
- MOD-171 → MOD-173（IFC-391a/c/e/f）、MOD-169（IFC-385/386/387/388）
- MOD-172 → MOD-173（store 类型）、MOD-169（IFC-389）
- MOD-169 → MOD-168（同一迁移文件 `0006_appeal_center.py` 内的操作顺序；无 Python 循环导入）
- MOD-168 / MOD-169 → MOD-001（审计）、既有 `accounts`/`registry` 模型

已检查：无循环依赖（前端三个页面模块互不引用；后端两个模块只共享同 app 的 models 与迁移文件）。

## 数据迁移

**迁移文件**：`backend/apps/residency/migrations/0006_appeal_center.py`（手写 scoped 迁移，仅 residency app；不使用 `makemigrations` 全量产物，符合画像 P6/P8）。

操作顺序与内容：

1. `AlterField` `residency_appeal.status` → `CharField(max_length=12, choices=[...新增 WITHDRAWN])`；`default="PENDING"` 不变。
2. `AddField` `residency_appeal.decision_note` = `CharField(max_length=500, null=True, blank=True)`。
3. `AddField` `residency_appeal.withdrawn_at` = `DateTimeField(null=True, blank=True)`。
4. `AddField` `residency_appeal.previous_appeal_id` = `ForeignKey("self", null=True, blank=True, on_delete=SET_NULL, related_name="resubmitted_appeals")`。
5. `AlterField` `residency_resident_application.status` → `CharField(max_length=12, ...)`。
6. `AddField` `residency_resident_application.applicant_name` = `CharField(max_length=64, blank=True, default="")`。
7. `AddField` `residency_resident_application.reject_reason` = `CharField(max_length=500, null=True, blank=True)`。
8. `AddField` `residency_resident_application.decision_note` = `CharField(max_length=500, null=True, blank=True)`。
9. `AddField` `residency_resident_application.withdrawn_at` = `DateTimeField(null=True, blank=True)`。
10. `AddField` `residency_resident_application.previous_application_id` = `ForeignKey("self", null=True, blank=True, on_delete=SET_NULL, related_name="resubmitted_applications")`。

历史数据策略：

- 新增字段全部可空或有默认值；既有行 `decision_note=NULL`、`withdrawn_at=NULL`、`previous_*=NULL`、`applicant_name=""`，页面按 REQ-NFUNC-060 显示“—”，无需数据回填。
- 既有 `status` 值均在 12 字符内，无截断；反向迁移把长度改回 8 时，若已存在 `WITHDRAWN`（9 字符）记录，MySQL 可能截断 → 反向执行前必须先清理或改写这些记录，标注 `[MANUAL_ROLLBACK_REQUIRED]`。
- 待审唯一约束与 `pending_slot` 语义不变；迁移不修改索引。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| 后端 `ocap-backend`（gunicorn，systemd） | 模型、视图、URL 变更 | 重新加载代码 + `python manage.py migrate` + 重启服务（E1 规划具体命令） |
| MySQL 库 `ocap`（192.168.31.98:3306） | 两个表各新增/修改字段 | 执行 `0006_appeal_center` 迁移；无新表、无索引变更 |
| Web 前端静态产物 | 新增/修改 6 个 Vue 组件与 3 个共享文件 | `npm --prefix frontend run build` 后替换 nginx `/ocap/` 静态目录 |
| 小程序 | 不发布 | 不改代码；后端只新增字段与状态值，旧响应字段不变，旧审批调用不传新参数仍可用（ADR-163） |
| 定时任务 | 无 | 本次不新增任务 |

## 领域与外部依赖出处

不适用：本次不新增硬件访问、领域算法或闭源 API 调用。既有微信登录/短信接口未改动；新增字段不涉及外部 API 契约，`[P11]` 无对应项。
