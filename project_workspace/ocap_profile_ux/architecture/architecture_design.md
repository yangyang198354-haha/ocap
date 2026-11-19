<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T23:31:48+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_profile_ux/requirements/user_stories.md</file>
    <file>backend/apps/accounts/models.py</file>
    <file>backend/apps/committee/views.py</file>
    <file>backend/apps/identity/views.py</file>
    <file>backend/apps/identity/services.py</file>
    <file>backend/apps/approval/views.py</file>
    <file>frontend/src/admin/AdminSeats.vue</file>
    <file>frontend/src/admin/AdminFlows.vue</file>
    <file>frontend/src/admin/AdminMemberships.vue</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计 — ocap_profile_ux

## 架构概览

INCREMENTAL：在既有 Django 5.2 + DRF 后端与 Vue 3 + Vite + Element Plus Web 前端上做增量改动，不新增技术栈、不新增第三方依赖、不引入容器（画像 P8）。

本次改动落在四个既有边界内：

| 边界 | 本次职责 | 关联需求 |
|---|---|---|
| 账号与资料（apps/accounts） | 新增签名档与实名展示开关字段、默认头像展示契约 | REQ-FUNC-256/263、REQ-NFUNC-052 |
| 身份与房屋关系（apps/identity、apps/residency） | 公开 profile 聚合、房屋关系多维过滤与搜索 | REQ-FUNC-260/261/262 |
| 业委会（apps/committee） | 席位列表持有人分列字段、楼栋/单元过滤与非 ACTIVE 折叠 | REQ-FUNC-258 |
| 审批（apps/approval） | 流程详情与编辑（后端 PUT 已具备，前端补入口） | REQ-FUNC-259 |
| Web 前端（frontend/） | 布局修正、默认头像组件、列表与表单改造、profile 页面 | REQ-FUNC-255～263 |

关键质量属性：隐私最小披露（REQ-NFUNC-052）、列表过滤响应 ≤ 2 s（REQ-NFUNC-053）、默认头像零外部依赖且 ≤ 100 KB（REQ-NFUNC-054）。

小程序端本批次不修改（用户已确认 I-1）。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| 后端 API | gunicorn `127.0.0.1:9000`（systemd `ocap-backend`），由 nginx `^~ /ocap/` 反代 | 测试环境 192.168.31.51；数据库 MySQL 192.168.31.98:3306 库 `ocap` |
| Web 前端 | Vite 构建产物（base `/ocap/`）部署到 nginx `8090` 静态目录 | 同上，外网 https://ai-freeark.xin/ocap/ |
| 定时任务 | `manage.py run_due_jobs` timer | 同上 |
| 迁移 | `python manage.py migrate`，accounts 单 app 迁移 | 同上 |

无新增运行单元；小程序产物不变。

## ADR

### ADR-147: 公开 profile 采用独立只读端点与字段白名单
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-261/262、REQ-NFUNC-052 要求他人可查看昵称、头像、身份、签名与可选实名，且绝不暴露手机号/邮箱/生日/证件。现有 `/me`（`apps/identity/services.py:53-81`）返回本人敏感字段，不能直接复用。
- Options:
  - A. 复用 `/me` 并按调用者裁剪字段：改动小，但同一端点两套语义，易误放敏感字段，权限分支复杂（优：少一个路由；缺：隐私风险高、测试面大）。
  - B. 新增 `GET /api/v1/users/{user_id}/profile`，独立白名单序列化（优：字段白名单可审计、与 `/me` 解耦；缺：多一个端点与契约测试）。
- Decision: 选 B。隐私是第一质量属性，白名单序列化把"返回什么"固定在单一函数里，便于契约测试逐字段断言。
- Consequences: 正向——profile 页与 `/me` 解耦，未来加字段必须显式进白名单；负向——新增端点需要登录鉴权与契约测试维护。

### ADR-148: 签名档与实名开关存放在 User 表
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-262/263 需要每用户两字段：签名（≤100 字纯文本）、是否展示实名（默认关闭）。
- Options:
  - A. 扩展 `accounts.User` 两个字段（优：与 nickname/gender/birthday 同表，读写沿用现有 `update_profile` 白名单；缺：User 表继续增宽）。
  - B. 新建 `UserProfile` 一对一表（优：职责分离；缺：新增 join、迁移与序列化改动更多，现网无此模式）。
- Decision: 选 A。字段少、强 1:1、与现有资料字段同生命周期；遵守最小改动。
- Consequences: 正向——`editable` 白名单加两项即可；负向——User 表字段增多，后续若出现大量资料字段需再评估拆表。

### ADR-149: 默认头像由前端内置资源 + 加载失败回退，后端仍返回 null
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-256/REQ-NFUNC-054；现状 `avatar_url` 为空时各页面显示占位文本（`MeProfile.vue:16`、`AuthImage`）。
- Options:
  - A. 后端在 `avatar_url` 为空时返回固定 URL（优：各端零改动；缺：后端承担静态资源、小程序也需可访问，且缓存/主题控制差）。
  - B. 前端统一头像组件，src 为空或加载失败时回退内置 SVG（优：资源随构建产物、零外网依赖、可控制大小与主题；缺：Web 各调用点需替换为组件）。
- Decision: 选 B。内置 SVG 满足 ≤100 KB 与离线性；组件同时解决"上传头像 404"回退（AC-261-02）。
- Consequences: 正向——头像展示规则单点收敛；负向——需替换 MeProfile、右上角菜单、参与人列表等调用点。

### ADR-150: 头像大小限制以后端策略为唯一最终防线，前端常量与文案镜像
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-257、REQ-NFUNC-051、C-84。约束来源：现有 `SPECS["AVATAR"]`（`backend/apps/core/attachments.py:25`）与 `ValidatedUpload` 校验链（同文件 95 行 413 FILE_TOO_LARGE）；前端预校验仅为体验优化。
- 被排除方案：仅改前端、后端维持 2 MB（会在服务端拒绝，产生前后端不一致）；仅改后端、前端维持 2 MB（用户无法上传 2–5 MB 文件）。
- Decision: 后端 `AVATAR.single/total` 改为 5 MB，前端常量同步为 5 MB 并更新提示文案；格式仍为 jpg/jpeg/png。
- Consequences: 正向——阈值单处权威；负向——已存的 2 MB 以上文件不受影响，无历史数据风险。

### ADR-151: 席位列表在现有接口上扩展持有人明细与过滤参数
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-258、C-81/C-82；现状 `seat_view` 只返回持有人 kind/unit_text/owner_name（`apps/committee/views.py:25-42`），前端拼一行（`AdminSeats.vue:23-30`）。
- Options:
  - A. 扩展现有 `/admin/committee/seats`：响应增加 `holder_detail` 结构（昵称、姓名、脱敏电话、坐落、类型、楼栋/单元/楼层），查询参数增加 `building/unit_no/floor/bucket`（优：一个端点、复用分页与权限；缺：序列化与查询变复杂）。
  - B. 新建"持有人聚合"端点（优：职责单一；缺：同一屏两次分页、状态一致性差）。
- Decision: 选 A。列表是同一数据源的分页视图，拆端点会引入跨端点分页不一致。
- Consequences: 正向——前端一次请求拿到全部列；负向——涉及跨表过滤（清册业主房产、绑定用户认证房产），需用 `Exists` 子查询避免 `distinct` 放大与 N+1（M-SA-010）。

### ADR-152: 席位默认主表仅显示 ACTIVE，非 ACTIVE 走独立折叠分桶
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-258/AC-265-01/02、I-3 已确认折叠范围=所有非 ACTIVE 状态。
- Options:
  - A. `bucket=active|ended` 两个分页请求，前端主表 + 默认折叠区（优：分页与计数天然正确；缺：两个请求）。
  - B. 单请求返回全部并在前端分组（优：一次请求；缺：跨状态分页失真、折叠区计数不准）。
- Decision: 选 A。主表 `bucket=active`（status=ACTIVE，含"待生效"标签），折叠区 `bucket=ended`（status∈REVOKED/EXPIRED/INVALIDATED/REPLACED/MERGED）。
- Consequences: 正向——两组计数与分页独立准确；负向——前端需并行请求并各自维护分页。

### ADR-153: 房屋关系搜索在后端完成，电话仅后 4 位匹配且响应保持脱敏
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-260、C-82、Q4 决策（后 4 位模糊匹配、展示脱敏）。
- Options:
  - A. 后端过滤：building/unit_no/floor/name 直连 Membership→RegistryUnit/RegistryOwner，phone 用 `user.phone__endswith` 或 `icontains` 后 4 位（优：一次分页、数据不出服务端；缺：多参数组合的查询复杂度）。
  - B. 前端拉全量再过滤（优：实现快；缺：5000 条规模不可接受、泄漏风险）。
- Decision: 选 A；电话入参校验为 4–11 位数字，匹配仅用于筛选，响应中的电话仍走 `mask_phone`。
- Consequences: 正向——隐私与性能兼得；负向——需要为 `building/unit_no/floor` 建查询路径并写性能用例。

### ADR-154: 审批流程编辑复用现有 PUT，前端补详情与编辑对话框
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-259；约束来源：`PUT /admin/approval/flows/{id}` 已实现完整更新与审计（`apps/approval/views.py:79-104`），`admin.updateFlow` 已在 `frontend/src/shared/api.js:184`。
- 被排除方案：新增专用 PATCH 端点（重复能力）；仅展示详情不编辑（不满足需求）。
- Decision: 前端增加"查看详情/编辑"对话框，复用 PUT；改变适用范围或方式时二次确认（Q6 决策）。
- Consequences: 正向——零后端改动、审计沿用；负向——PUT 为全量覆盖，前端必须回传完整审批人列表。

### ADR-155: 个人资料页布局修正使用 Element Plus 原生属性，不自定义控件
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-255；约束来源：现有页面使用 `el-input/el-select/el-date-picker`（`MeProfile.vue:6-13`），生日控件高度不一致源于 `el-date-picker` 默认宽度与行内对齐。
- 被排除方案：换成自定义日期控件（引入新依赖、违反最小改动）。
- Decision: 行容器统一 `align-items: center`，四个控件统一高度变量与 `flex-wrap`，日期选择器宽度与输入框同高（通过 `size` 与样式覆盖）。
- Consequences: 正向——无新依赖、与 Element Plus 主题一致；负向——依赖组件默认样式，需回归窄屏换行。

## 开放问题 / ASSUMPTION

- [ASSUMPTION] 实名取值：取该用户最近一条有效产权认证（Membership.registry_owner）对应清册姓名；若多条不同姓名，取最近认证且不额外提示（Q3 决策）。实现时若 `registry_owner` 为空，则实名开关不展示。
- [ASSUMPTION] profile 页入口按 Q2 建议：决议参与人列表、投票人列表、房屋关系列表、用户菜单"我的主页"。
- [ASSUMPTION] 默认头像采用内置 SVG（中性灰底 + 白色人形），不随主题变色，保证深浅背景均可见。
- 性能口径：REQ-NFUNC-053 的 5000 条规模按当前测试库量级假设，测试阶段用生成的批量数据验证。
