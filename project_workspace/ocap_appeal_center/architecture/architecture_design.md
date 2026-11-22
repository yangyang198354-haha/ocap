<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T09:43:33+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — 申诉与同住人申请记录中心（Web 用户端）

## 架构概览

本次为 INCREMENTAL 增量：在既有 Django 5.2 + DRF 后端（`backend/apps/residency/`）与 Vue 3 + Vite + Element Plus Web 前端（`frontend/src/`）上，为申诉与同住人申请补充“记录查询、撤回、重新提交、处理备注、同住人实名”能力，并把两个并列二级菜单合并为页内双 Tab。小程序端不改，后端新增字段全部可空或有默认值，旧响应字段不变。

改动在现有系统中的位置：

| 层 | 现有位置 | 本次增量 |
|---|---|---|
| 数据模型 | `backend/apps/residency/models.py:34-68`（`Appeal`、`ResidentApplication`） | 两个模型新增撤回状态、处理备注、原记录关联；`ResidentApplication` 新增本人实名与驳回原因 |
| API | `backend/apps/residency/views.py:128-134`（我的申诉）、`:271-311`（申诉决定）、`:345-428`（同住申请） | 新增撤回端点、重新提交关联参数、备注与实名参数、列表返回字段扩展 |
| 聚合 | `backend/apps/residency/housing.py:59-104`（同住人列表） | 同住人记录补充实名；本人作为同住人时汇总实名包含本人实名 |
| 导航 | `frontend/src/layout/menus.js:10-15`、`frontend/src/router/index.js:46-48` | 合并为单一“认证申诉”入口；旧地址保留并定位到“我的申诉”Tab |
| 页面 | `frontend/src/portal/units/UnitsAppeal.vue`、`UnitsMyAppeals.vue`、`UnitsApplications.vue`、`UnitsIdentity.vue` | 申诉双 Tab 宿主、同住申请双 Tab 宿主、记录列表扩充、身份页实名展示 |
| 管理端 | `frontend/src/admin/AdminAppeals.vue:150-164` | 通过与驳回均可填写备注 |

关键质量属性（引需求）：

- REQ-NFUNC-059：撤回、重新提交、处理备注均留痕（审计），备注长度上限 500 字，超长拒绝且不落库。
- REQ-NFUNC-060：历史数据无备注/无实名时以“—”展示且不报错；两类记录列表沿用最近 100 条上限（`views.py:30` 的 `MINE_LIMIT`）；空列表显示明确空状态。

## 部署视图

仅使用画像 P7 中存在的环境与方式，不引入新运行单元：

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Web 后端（含本次模型与接口变更） | gunicorn `127.0.0.1:9000`，systemd 服务 `ocap-backend` | 测试（内网）树莓派 192.168.31.51；数据库 MySQL 192.168.31.98:3306 库 `ocap` |
| Web 前端（Vite 静态产物） | nginx `8090` 下的 `/ocap/` 静态目录 | 同上（外网经 frp 反代） |
| 数据库迁移 | `python manage.py migrate`（residency 单 app，手写迁移） | 同上 |
| 微信小程序 | 不重新发布；仅共享后端，新增字段不破坏旧解析 | 不变 |

生产环境在画像 P7 中不存在，本设计不假设生产部署。

## ADR

### ADR-160: 申诉入口合并为单入口 + 页内双 Tab

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-289、US-291、AC-291-01/02/03；D-01 要求入口文案沿用“认证申诉”、默认“认证申诉”Tab；现有两个并列菜单与两个独立分区（`menus.js:12,14`、`router/index.js:46-48`、`portal/Units.vue:18-24`）。
- Options:
  - A. 新增页面宿主组件（申诉中心）承载两个 Tab，内部复用现有表单与记录列表组件；`/units/appeal` 与旧 `/units/appeals` 都指向该宿主，后者以“我的申诉”为初始 Tab。
    - 优：表单状态在 Tab 切换间保留（Element Plus tab-pane 默认保留已渲染内容）；旧地址与页面组件均可继续复用；改动集中在导航与宿主层。
    - 缺：多一层容器组件，需新增路由 props 约定。
  - B. 直接把“我的申诉”内容并入 `UnitsAppeal.vue` 单文件。
    - 优：文件数少。
    - 缺：单文件同时承担表单与列表，难以保持记录列表与同住申请记录的一致性；旧 `/units/appeals` 仍需额外分支。
  - C. 仅合并菜单，两个页面之间用查询参数切换。
    - 优：不改组件结构。
    - 缺：切换会重新挂载页面，违反 AC-291-02（已选房屋、姓名、证明不得丢失）。
- Decision: 选择 A。用宿主组件保证 Tab 切换不丢状态，同时保留旧地址兼容（AC-291-03），菜单仅保留一个“认证申诉”入口（D-01）。
- Consequences:
  - 正向：导航与页面结构清晰；记录列表组件可同时服务于申诉与同住申请，字段口径统一。
  - 负向：新增宿主组件与路由 props（初始 Tab），需前端测试覆盖两个入口的默认 Tab 行为。

### ADR-161: 撤回采用显式状态 WITHDRAWN 并释放待审槽位

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-292、REQ-FUNC-294、C-359、D-04；现有模型只有 `PENDING/APPROVED/REJECTED/CLOSED`（`models.py:35,52`），待审唯一约束依赖 `pending_slot`（`models.py:48,66`）。
- Options:
  - A. 新增状态 `WITHDRAWN`（“已撤回”），撤回时把 `pending_slot` 置空并记录 `withdrawn_at`。
    - 优：记录可查、可审计，满足 D-04“默认展示”；置空槽位即释放 C-360 限制（唯一约束对 NULL 不生效，MySQL/SQLite 行为一致，ADR-017）。
    - 缺：需扩展状态字典与前后端标签映射。
  - B. 撤回即物理删除记录。
    - 优：无需新增状态。
    - 缺：违反 D-04“保留可查”，丢失审计与重新提交关联依据。
  - C. 复用现有 `CLOSED` 状态表示撤回。
    - 优：不改状态枚举。
    - 缺：`CLOSED` 已用于“已关闭”语义，混用会让处理结果与用户操作不可区分，AC-294-01 的状态标签无法表达“已撤回”。
- Decision: 选择 A。状态字段长度由 8 扩为 12 以容纳 `WITHDRAWN`（ADR-165）；撤回仅允许记录本人且状态为 `PENDING`（C-359），审计动作新增 `APPEAL_WITHDRAWN` 与 `RESIDENT_APPLICATION_WITHDRAWN`。
- Consequences:
  - 正向：满足 D-04 与 C-360；撤回行为完全留痕。
  - 负向：历史统计若按状态枚举硬编码，需要把 `WITHDRAWN` 归入“非待审、非通过”分支；前后端标签映射需同步。

### ADR-162: 重新提交生成新记录并关联原记录

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-292、US-294 AC-294-03、US-296 AC-296-03、D-02；现有创建接口不接受来源记录（`views.py:136-222`、`:345-364`）。
- Options:
  - A. 新建记录，并用自关联外键 `previous_appeal_id` / `previous_application_id` 指向被撤回记录；列表返回该字段供前端显示“重新提交自 #编号”。
    - 优：完全符合 D-02“原记录保留为已撤回”；新记录独立走完整待审流程；历史与审计链完整。
    - 缺：新增自关联字段与提交参数校验。
  - B. 直接把已撤回记录改回 `PENDING` 并更新字段。
    - 优：不新增记录与关联字段。
    - 缺：违反 D-02（原记录不再保留为已撤回），且丢失两次提交的时间线。
  - C. 新建记录但不保留关联。
    - 优：实现最简单。
    - 缺：AC-294-03/AC-296-03 明确要求标注来源记录，无法满足。
- Decision: 选择 A。重新提交时允许修改房屋、产权人姓名/本人实名与证明（D-02、Q3 结论）；来源记录必须属于当前用户且状态为 `WITHDRAWN`，否则 400 `INVALID_PREVIOUS_RECORD`。
- Consequences:
  - 正向：需求与决策一致；可以追溯“哪次提交替代了哪次”。
  - 负向：同一用户可产生较多记录，列表仍以最近 100 条为上限（REQ-NFUNC-060）。

### ADR-163: 处理备注与驳回原因分离建模

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-291、US-293、D-03；现有 `Appeal.reject_reason`（`models.py:43`）只在驳回时写入（`views.py:295-301`），同住申请决定接口只有 `decision`（`views.py:407-412`）。
- Options:
  - A. 两端统一新增 `decision_note` 字段（处理备注），通过与驳回都可写；申诉驳回原因继续使用现有 `reject_reason` 且必填；同住申请新增可选 `reject_reason`。
    - 优：不改变现有申诉驳回语义；备注与驳回原因在页面可分别展示（AC-293-02）；同住审批保持向后兼容（旧客户端不传原因仍可驳回）。
    - 缺：两类记录各有两个文本字段，前端需分栏展示。
  - B. 复用 `reject_reason` 作为通用备注。
    - 优：不新增字段。
    - 缺：通过时无字段可写；驳回原因与备注混为一谈，无法同时展示两条信息。
  - C. 只有一个 `comment` 字段，驳回时必填。
    - 优：字段最少。
    - 缺：通过时也要区分“备注”与“驳回原因”，且会改变现有申诉接口契约。
- Decision: 选择 A。备注长度 ≤500（超长 400 `INVALID_VALUE`，不落库）；申诉驳回原因仍必填；同住申请驳回原因选填（≤500），为空时前端显示“—”。该口径的理由是对既有小程序审批调用保持兼容（小程序不传原因时不因新增必填而失败），记为开放问题 A-01。
- Consequences:
  - 正向：完全覆盖 D-03 的“通过与驳回均可备注”；申诉现有行为不变。
  - 负向：同住审批若后续要求“驳回必须写原因”，需要一次契约变更（本批不做）。

### ADR-164: 同住人实名采用申请快照，不改身份模型

- Status: Proposed
- Type: decision
- Context: REQ-FUNC-295、REQ-FUNC-296、C-361；现有同住人展示只有昵称与账号（`housing.py:59-63,96-103`、`UnitsIdentity.vue:31-35`）；身份汇总实名只来自产权清册姓名（`housing.py:83,123-124`）。
- Options:
  - A. 在 `ResidentApplication` 上保存提交时的本人实名快照（`applicant_name`），审批与身份页均读该快照。
    - 优：符合 C-361（实名只作为申请信息，不参与认证/清册匹配/身份升级）；历史申请无值可空并显示“—”；一次批量查询即可展示，无 N+1。
    - 缺：用户改名后历史申请仍显示旧实名。
  - B. 在 `accounts.User` 上新增全局“真实姓名”并由用户维护。
    - 优：一次维护处处生效。
    - 缺：改变账号与身份模型，超出本批范围；与 C-361 的“仅申请信息”边界冲突，且需要额外权限与审核规则。
  - C. 同住人实名读清册业主姓名。
    - 优：无需新字段。
    - 缺：同住人未必在清册中，且会被误当作产权认证依据，违反 C-361。
- Decision: 选择 A。`applicant_name` 必填、去首尾空白后非空、≤64 字（REQ-FUNC-295）；身份页同住人列表按 `(unit_id, applicant_id)` 取最近一条 `APPROVED` 申请的实名；本人为同住人时把本人实名并入 `real_names`（去重保序），缺失时以“—”展示（REQ-NFUNC-060）。
- Consequences:
  - 正向：不触碰认证体系，满足 C-361；身份页展示与申请记录数据同源。
  - 负向：历史同住人无实名，只能显示“—”；撤销/移除后历史实名仍保留在申请记录中（符合留痕）。

### ADR-165: 状态字段长度扩展为 12

- Status: Proposed
- Type: constraint-driven
- Context: ADR-161 需要存储 `WITHDRAWN`（9 字符），现有 `status` 字段 `max_length=8`（`models.py:39,57`）。
- 被排除方案与约束来源:
  - 排除“用 8 字符缩写（如 `WDRAWN`）”：需在前后端维护非自解释缩写，且与现有 `PENDING/APPROVED/REJECTED/CLOSED` 命名风格不一致；约束来源为 ADR-161 的状态语义。
  - 排除“新增独立 `is_withdrawn` 布尔字段”：状态与布尔并存会产生 `APPROVED + is_withdrawn` 等非法组合；约束来源为单一状态源原则。
- Decision: 两个模型的 `status` 扩为 `max_length=12`，仅新增枚举值，不改变既有值。
- Consequences:
  - 正向：状态语义单一、可读；MySQL `varchar` 扩容为原地变更，风险低。
  - 负向：需一次 `AlterField` 迁移；旧客户端若把未知状态当异常处理需确认（小程序不展示撤回状态，见“受影响的运行单元”）。

## 开放问题 / ASSUMPTION

- A-01（ASSUMPTION）：同住申请的驳回原因按选填实现（≤500 字），理由见 ADR-163。若用户要求与申诉一致地强制必填，需在下游阶段变更契约。
- A-02（ASSUMPTION）：撤回后的“重新提交”入口只出现在已撤回记录上；提交新记录时允许更换房屋（D-02 / Q3 结论），来源记录与目标房屋可以不同。
- A-03（ASSUMPTION）：已撤回记录参与“最近 100 条”截断，与其它状态同等对待（REQ-NFUNC-060）。
- A-04（ASSUMPTION）：同住申请记录列表的“状态”沿用现有 `statusLabel('application', …)` 映射；新增 `WITHDRAWN` 标签统一为“已撤回”。
- A-05：管理端 `AdminAppeals.vue` 的表格列是否展示处理备注，仅要求“审核时可填写、用户端可查看”；管理端列表展示备注为可选改进，不纳入本批验收。
