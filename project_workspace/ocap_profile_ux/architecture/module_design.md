<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T23:31:48+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_profile_ux/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_profile_ux/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计 — ocap_profile_ux

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-153 | 资料字段与资料接口扩展 | 修改 `backend/apps/accounts/models.py`、`services.py`、`views.py`；新建 `backend/apps/accounts/migrations/0004_user_profile_fields.py` | 新增签名档与实名展示开关，扩展本人资料读写契约 | REQ-FUNC-262/263；US-271/272 | — |
| MOD-154 | 公开 profile 聚合接口 | 修改 `backend/apps/identity/views.py`、`urls.py`、`services.py` | 只读聚合他人昵称/头像/身份/签名/可选实名 | REQ-FUNC-261/262；US-270/271 | MOD-153 |
| MOD-155 | 默认头像组件与右上角展示 | 新建 `frontend/src/portal/parts/UserAvatar.vue`；新建 `frontend/src/assets/avatar-default.svg`；修改 `frontend/src/portal/PortalUserMenu.vue`、`frontend/src/admin/AdminUserMenu.vue` | 统一头像展示与失败回退；右上角昵称旁头像 | REQ-FUNC-256；US-261/262 | — |
| MOD-156 | 头像上传上限调整 | 修改 `backend/apps/core/attachments.py`、`frontend/src/portal/me/MeProfile.vue` | AVATAR 上限 2 MB → 5 MB，前后端一致 | REQ-FUNC-257、REQ-NFUNC-051；US-263 | — |
| MOD-157 | 席位接口持有人明细与过滤 | 修改 `backend/apps/committee/views.py` | 扩展持有人分列字段、楼栋/单元/楼层过滤、active/ended 分桶 | REQ-FUNC-258；US-264/265 | — |
| MOD-158 | 审批流程详情与编辑（前端） | 修改 `frontend/src/admin/AdminFlows.vue`、`frontend/src/shared/api.js`（如缺） | 详情对话框与编辑表单，复用既有 PUT | REQ-FUNC-259；US-266/267 | 既有 `apps/approval` |
| MOD-159 | 房屋关系过滤与搜索接口 | 修改 `backend/apps/identity/views.py` | building/unit_no/floor/name/phone 过滤与搜索 | REQ-FUNC-260；US-268/269 | — |
| MOD-160 | 席位页表格改造 | 修改 `frontend/src/admin/AdminSeats.vue` | 分列表格、过滤条、折叠区 | REQ-FUNC-258、C-81；US-264/265 | MOD-157 |
| MOD-161 | 房屋关系页过滤 UI | 修改 `frontend/src/admin/AdminMemberships.vue` | 过滤条与搜索框、空状态 | REQ-FUNC-260；US-268/269 | MOD-159 |
| MOD-162 | 他人 profile 页与入口 | 新建 `frontend/src/portal/UserProfile.vue`；修改 `frontend/src/router/index.js`、`frontend/src/portal/parts/ParticipantList.vue`、`frontend/src/portal/PortalUserMenu.vue`、`frontend/src/admin/AdminMemberships.vue` | profile 页面、路由与点击昵称/头像入口 | REQ-FUNC-261/262；US-270/271 | MOD-154、MOD-155 |
| MOD-163 | 个人资料页布局与新增表单 | 修改 `frontend/src/portal/me/MeProfile.vue`、`frontend/src/portal/me/useProfile.js` | 控件对齐、签名档编辑、实名开关 | REQ-FUNC-255/262/263；US-260/271/272 | MOD-153、MOD-156 |

## 模块详情

### MOD-153 资料字段与资料接口扩展

字段（`accounts/models.py`）：

```python
signature = models.CharField(max_length=100, blank=True, default="")      # 纯文本签名档
real_name_visible = models.BooleanField(default=False)                    # 实名展示开关
```

`AccountService.update_profile` 的 `editable` 集合加入 `signature`、`real_name_visible`（`backend/apps/accounts/services.py:352`）。校验：`signature` 转 `str` 后截断/拒绝超过 100 字 → `ApiError("INVALID_VALUE", "签名档不能超过 100 字")`；`real_name_visible` 仅接受 bool。仅 `OWNER/HEAD` 有效产权成员可置 true，否则 `ApiError("FORBIDDEN", "仅已验证产权业主可开启实名展示", 403)`。

**IFC-368：`PATCH /api/v1/me/profile`（扩展）**

- 鉴权：`IsMember`（沿用现有 ProfileView）。
- 请求：`{"nickname"?: str(≤30), "gender"?: 0|1|2|null, "birthday"?: "YYYY-MM-DD"|null, "signature"?: str(≤100), "real_name_visible"?: bool}`
- 响应 200：`profile_view` 增补 `"signature": str`、`"real_name_visible": bool`、`"real_name": str | null`（本人可见；取最近有效产权认证清册姓名，无则 null）。
- 错误：`INVALID_VALUE`(400)、`FORBIDDEN`(403)、`UNAUTHORIZED`(401)。

**IFC-369：`GET /api/v1/me/profile`（扩展）** — 同上响应结构，鉴权 `IsMember`。

### MOD-154 公开 profile 聚合接口

服务：`IdentityService.public_profile(user_id: int) -> dict`。实名解析：取 `Membership.filter(user_id=..., ended_at__isnull=True, role__in=("HEAD","OWNER"), registry_owner__isnull=False).order_by("-id").first()`，实名 = `membership.registry_owner.name`；`real_name_visible` 为 false 或实名缺失时返回 null。身份文案沿用 `identity_view`/`CommitteeQuery.identity_labels` 的聚合口径（只取汇总 label）。

**IFC-370：`GET /api/v1/users/{user_id}/profile`**

- 鉴权：`IsMember`（登录用户；未登录 401，前端跳登录）。
- 响应 200：

```json
{
  "id": 2, "nickname": "张三" | null, "avatar_url": "/api/v1/attachments/{uuid}/download" | null,
  "identity": {"code": "HEAD", "label": "产权业主"},
  "labels": ["产权业主"],
  "real_name": "张三" | null,
  "signature": "" ,
  "is_self": false
}
```

- 白名单：禁止出现 phone、email、birthday、gender、account_no、证件、地址。
- 错误：`NOT_FOUND`(404 用户不存在或已注销)、`UNAUTHORIZED`(401)。
- 校验：`user_id` 必须为正整数；非法 → 404。

### MOD-155 默认头像组件与右上角展示

`UserAvatar.vue`（新建）：

```ts
props: { src?: string | null; size?: number /* px, 默认 32 */; alt?: string /* 默认 "头像" */; round?: boolean }
// 内部：src 为空或 img onerror → 使用 import avatarDefault from '@/assets/avatar-default.svg'
```

`avatar-default.svg`：256×256，中性 `#E5E7EB` 底 + `#9CA3AF` 人形，体积 < 2 KB。

`PortalUserMenu.vue`：昵称左侧插入 `<UserAvatar :src="auth.me?.profile?.avatar_url" :size="28" :round="true" />`，触发器改为 `display:flex; align-items:center; gap:8px`。`AdminUserMenu.vue` 同样处理。

### MOD-156 头像上传上限调整

`backend/apps/core/attachments.py:25`：`"AVATAR"` 的 `single`/`total` 改为 `5 * 1024 * 1024`。
`MeProfile.vue`：`AVATAR_MAX_BYTES = 5 * 1024 * 1024`，提示文案改"jpg/png，不超过 5 MB"，超限提示"头像不能超过 5 MB"。
**IFC-376：上传策略**：`POST /api/v1/attachments`（file_type=AVATAR）——鉴权沿用现有上传视图；超限 413 `FILE_TOO_LARGE`；类型不符 400 `FILE_TYPE_NOT_ALLOWED`（沿用现有错误码）。

### MOD-157 席位接口持有人明细与过滤

**IFC-372：`GET /api/v1/admin/committee/seats`（扩展）**

- 鉴权：`IsAdmin`（沿用）。
- 查询参数：`position?`、`status?`（沿用）、`bucket? ∈ {active, ended}`（默认 active）、`building?`、`unit_no?`、`floor?`、`page`、`page_size`。
- 响应行增补（保留现有字段）：

```json
"holder_detail": {
  "nickname": "张三" | null,
  "name": "张某某" | null,
  "phone_masked": "138****1234" | null,
  "unit_text": "1栋1单元9层902" | null,
  "unit_type": "住宅" | null,
  "building": "1栋" | null,
  "unit_no": "1单元" | null,
  "floor": "9层" | null
}
```

- 数据来源：`holder_owner`（清册业主及其 unit）优先；已绑定用户取该用户有效 `Membership`（HEAD/OWNER 优先、最近认证）。
- 过滤：building/unit_no/floor 同时对清册业主房产与绑定用户认证房产生效；实现用 `Exists` 子查询避免 `distinct`（M-SA-010）。
- 分桶：`bucket=active` → `status="ACTIVE"`；`bucket=ended` → `status__in=("REVOKED","EXPIRED","INVALIDATED","REPLACED","MERGED")`。
- 错误：`INVALID_QUERY`(400，非法 bucket/分页参数)、`FORBIDDEN`(403)。

### MOD-158 审批流程详情与编辑（前端）

复用 **IFC-373：`PUT /api/v1/admin/approval/flows/{flow_id}`**（已存在，`apps/approval/views.py:79-104`）：请求 `{name?: str(≤60), scope?: "RESOLUTION"|"EXPENSE"|"INCOME", mode?: "DESIGNATED"|"HALF_MAJORITY", approver_ids?: int[], is_active?: bool}`；鉴权 `IsAdmin`；错误 `NOT_FOUND`(404)、`INVALID_VALUE`(400)。前端 "查看详情" 展示名称/适用/方式/启用/审批人；"编辑" 对话框预填并在 scope 或 mode 变化时 `ElMessageBox.confirm` 二次确认。

列表接口已返回 `approvers` 摘要（`[{id, nickname}]`，`apps/approval/views.py:16-22`），详情可直接复用；如需身份标签，仅在 `flow_view` 的 approvers 项增补 `identity_label`，不改变既有字段。

### MOD-159 房屋关系过滤与搜索接口

**IFC-374：`GET /api/v1/admin/memberships`（扩展）**

- 鉴权：`IsAdmin`（沿用）。
- 查询参数：`role?`（沿用）、`q?`（沿用：账号/昵称/专有部分）、`building?`、`unit_no?`、`floor?`、`name?`（≤32，匹配 `membership.registry_owner.name__icontains`）、`phone?`（4–11 位数字，`user.phone__endswith` 后 4 位或 `icontains` 子串）。
- 响应：沿用现有 `MembershipSerializer`，电话保持 `mask_phone`。
- 错误：`INVALID_QUERY`(400，phone 非 4–11 位数字)、`FORBIDDEN`(403)。

### MOD-160 席位页表格改造（前端）

- 过滤条：楼栋/单元/职位下拉（选项来源：席位数据中出现的 building/unit_no 去重，或复用 `/admin/registry/unit-options`）。
- 主表列：昵称、姓名、联系电话、专有部分坐落、专有部分类型、职位、状态、任期开始、任期结束、操作（C-81 保留原列）。
- 折叠区：`el-collapse` + 第二张表（`bucket=ended`），标题含计数；展开时加载。
- 交互：过滤变化重置页码；空状态"暂无席位记录"。

### MOD-161 房屋关系页过滤 UI（前端）

- 过滤条：楼栋/单元/楼层级联 + 搜索框（姓名/电话/专有部分共用一个输入框，按纯数字 4–11 位判定 phone，否则作为 `name`/`q` 提交）。
- 楼层选项数值升序（I-5）。
- 空状态"暂无匹配记录"。

### MOD-162 他人 profile 页与入口（前端）

**IFC-375：前端路由** `GET /users/:user_id(\\d+)/profile` → `portal/UserProfile.vue`（需登录，沿用 `router.beforeEach`）。
页面展示：`UserAvatar`（默认头像回退）、昵称、身份标签、签名档（空态"这个人很懒，什么都没写"）；`real_name` 非空时在身份区显示"实名：xxx"；`is_self` 为 true 时展示"编辑资料"按钮。
入口：`ParticipantList.vue` 的参与人昵称/头像、`AdminMemberships.vue` 用户列、`PortalUserMenu.vue` 新增"我的主页"菜单项（同一页面，`user_id` 取 `me.profile.id`）。

### MOD-163 个人资料页布局与新增表单（前端）

- 行容器：`display:flex; flex-wrap:wrap; align-items:center; gap:8px`；四个控件统一 `size="default"`，`el-date-picker` 显式 `style="width:180px"`，行内在 ≥768px 不换行、<768px 换行且同基线（AC-260-01/02）。
- 新增："签名档" textarea（maxlength=100，show-word-limit）与保存按钮；"实名展示" `el-switch`（仅 `identities.summary.code ∈ {HEAD, OWNER}` 时展示，否则置灰并提示）。
- 读取：`useProfile.js` 的 `loadProfile` 增加 `signature/real_name_visible/real_name` 字段透传。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-255 | US-260 | MOD-163 |
| REQ-FUNC-256 | US-261、US-262 | MOD-155 |
| REQ-FUNC-257 | US-263 | MOD-156 |
| REQ-FUNC-258 | US-264、US-265 | MOD-157、MOD-160 |
| REQ-FUNC-259 | US-266、US-267 | MOD-158 |
| REQ-FUNC-260 | US-268、US-269 | MOD-159、MOD-161 |
| REQ-FUNC-261 | US-270 | MOD-154、MOD-162 |
| REQ-FUNC-262 | US-271 | MOD-153、MOD-162、MOD-163 |
| REQ-FUNC-263 | US-272 | MOD-153、MOD-162、MOD-163 |
| REQ-NFUNC-051 | US-263 | MOD-156 |
| REQ-NFUNC-052 | US-270 | MOD-154、MOD-162 |
| REQ-NFUNC-053 | US-264/268 | MOD-157、MOD-159 |
| REQ-NFUNC-054 | US-261 | MOD-155 |

## 依赖关系

- MOD-154 → MOD-153（读取 `signature` / `real_name_visible`）
- MOD-160 → MOD-157（消费 `holder_detail` 与 bucket 参数）
- MOD-161 → MOD-159（消费新查询参数）
- MOD-162 → MOD-154（IFC-370）、MOD-155（UserAvatar）
- MOD-163 → MOD-153（IFC-368/369）、MOD-156（5 MB 文案与常量）
- MOD-158 无新增后端依赖（复用 IFC-373）

已检查：无循环依赖。

## 数据迁移

新建 `backend/apps/accounts/migrations/0004_user_profile_fields.py`（单 app、手写，画像 P6）：

- `User.signature`：`CharField(max_length=100, blank=True, default="")`，非空默认空串，无需回填。
- `User.real_name_visible`：`BooleanField(default=False)`，默认关闭满足 C-83。

可逆：`migrations.RemoveField` 可完整回滚；无索引变更；MySQL 小表 `ALTER`，风险低。回滚后签名与开关数据丢失（可接受，新功能数据非关键）。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| Django 后端（gunicorn `ocap-backend`） | 新增字段与接口扩展 | `migrate` 后重启服务 |
| Web 前端（nginx 静态站点） | 页面与组件改动 | `npm run build` 后发布 dist |
| 定时任务 `run_due_jobs` | 无 | 不重启 |
| 微信小程序 | 无（I-1） | 不构建 |

## 领域与外部依赖出处

画像 P11 不为"无"，但本次 IFC 均不涉及微信/短信/邮件外部 API 的调用契约：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-376（MOD-156） | AVATAR 现有上限 2 MB、允许扩展名、413 `FILE_TOO_LARGE` | [CODE: backend/apps/core/attachments.py:25,95] |
| IFC-372（MOD-157） | 现有席位响应字段与 position/status 过滤 | [CODE: backend/apps/committee/views.py:25-62] |
| IFC-373（MOD-158） | 流程更新请求字段与审计行为 | [CODE: backend/apps/approval/views.py:79-104] |
| IFC-374（MOD-159） | 现有房屋关系过滤与序列化字段 | [CODE: backend/apps/identity/views.py:82-109] |
| IFC-370（MOD-154） | 身份文案聚合口径 | [CODE: backend/apps/accounts/directory.py:21-34]；[CODE: backend/apps/identity/services.py:63-81] |
