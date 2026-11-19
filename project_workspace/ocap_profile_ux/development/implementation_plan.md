<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-19T00:08:21+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/architecture/module_design.md</file>
    <file>project_workspace/ocap_profile_ux/requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划 — ocap_profile_ux

## 实现概览

11 个 MOD 全部完成（MOD-153～163），后端 9 个文件（含 1 个新建迁移）、前端 9 个文件（含 2 个新建资源/页面）、测试调整 6 个文件。实现顺序按依赖拓扑：MOD-153（字段）→ MOD-156（上限）→ MOD-154（公开 profile）→ MOD-157（席位接口）→ MOD-159（房屋关系接口）→ MOD-155（头像展示）→ MOD-163（资料页）→ MOD-160（席位页）→ MOD-161（房屋关系页）→ MOD-158（审批流程）→ MOD-162（profile 页与入口）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-153 | `backend/apps/accounts/models.py` | 修改 | — | L | 新增 signature、real_name_visible | DONE |
| 2 | MOD-153 | `backend/apps/accounts/migrations/0004_user_profile_fields.py` | 新建 | 1 | L | 手写迁移，两字段，可逆 | DONE |
| 3 | MOD-153 | `backend/apps/accounts/services.py` | 修改 | 1 | L | update_profile 增加两字段校验与实名权限 | DONE |
| 4 | MOD-153 | `backend/apps/accounts/views.py` | 修改 | 1 | L | profile_view 增加 id/signature/real_name_visible/real_name | DONE |
| 5 | MOD-156 | `backend/apps/core/attachments.py` | 修改 | — | L | AVATAR 上限 5 MB | DONE |
| 6 | MOD-154 | `backend/apps/identity/services.py` | 修改 | 1 | M | public_profile 白名单聚合与实名解析 | DONE |
| 7 | MOD-154 | `backend/apps/identity/views.py` | 修改 | 6 | M | UserProfileView + 房屋关系过滤扩展 | DONE |
| 8 | MOD-154 | `backend/apps/identity/urls.py` | 修改 | 6 | L | `users/<id>/profile` 路由 | DONE |
| 9 | MOD-157 | `backend/apps/committee/views.py` | 修改 | — | H | holder_detail 批量构造、bucket、楼栋/单元/楼层过滤、end_reason | DONE |
| 10 | MOD-158 | `backend/apps/approval/views.py` | 修改 | — | L | 审批人摘要增补 identity_label | DONE |
| 11 | MOD-155 | `frontend/src/assets/avatar-default.svg` | 新建 | — | L | 内置默认头像（<2 KB） | DONE |
| 12 | MOD-155 | `frontend/src/portal/parts/AuthImage.vue` | 修改 | 11 | L | 空/失败回退默认头像 | DONE |
| 13 | MOD-155 | `frontend/src/portal/PortalUserMenu.vue` | 修改 | 12 | L | 昵称左侧 28px 头像 | DONE |
| 14 | MOD-163 | `frontend/src/portal/me/MeProfile.vue` | 修改 | 4,5,12 | M | 行对齐、签名档、实名开关、5 MB、我的主页入口 | DONE |
| 15 | MOD-163 | `frontend/src/portal/me/useProfile.js` | 修改 | 4 | L | 新字段默认值 | DONE |
| 16 | MOD-162 | `frontend/src/portal/UserProfile.vue` | 新建 | 6 | M | 他人 profile 页 | DONE |
| 17 | MOD-162 | `frontend/src/router/index.js` | 修改 | 16 | L | `/users/:id/profile` | DONE |
| 18 | MOD-162 | `frontend/src/shared/api.js` | 修改 | 7 | L | meApi.userProfile | DONE |
| 19 | MOD-160 | `frontend/src/admin/AdminSeats.vue` | 修改 | 9,12 | H | 10 列表格、过滤、折叠区、昵称链接 | DONE |
| 20 | MOD-161 | `frontend/src/admin/AdminMemberships.vue` | 修改 | 7 | M | 楼栋/单元/楼层过滤、搜索、用户链接 | DONE |
| 21 | MOD-158 | `frontend/src/admin/AdminFlows.vue` | 修改 | 10 | M | 详情/编辑对话框 | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件） | 状态 | 说明 |
|---|---|---|---|---|
| US-260 | AC-260-01 | `MeProfile.vue` `.profile-row` + `.row` 全局 flex | DONE | jsdom 不度量像素，真实对齐列入人工验证 |
| US-260 | AC-260-02 | `MeProfile.vue` `flex-wrap: wrap` | DONE | 窄屏换行 |
| US-261 | AC-261-01 | `AuthImage.vue` 默认分支 + `assets/avatar-default.svg` | DONE | alt 默认"默认头像" |
| US-261 | AC-261-02 | `AuthImage.vue` `@error="release"` | DONE | 加载失败回退 |
| US-262 | AC-262-01 | `PortalUserMenu.vue` AuthImage :size="28" | DONE | 触发器 flex 居中 |
| US-262 | AC-262-02 | `PortalUserMenu.vue` 头像在 button 内 | DONE | 点击头像与昵称同一触发器 |
| US-263 | AC-263-01 | `MeProfile.vue` AVATAR_MAX_BYTES=5MB；`attachments.py` | DONE | 4.9 MB 可上传 |
| US-263 | AC-263-02 | `MeProfile.vue` checkAvatar；`attachments.py:26` | DONE | 超限 413 FILE_TOO_LARGE |
| US-263 | AC-263-03 | `MeProfile.vue` checkAvatar 类型判断 | DONE | gif/exe 前端拦截 |
| US-264 | AC-264-01 | `AdminSeats.vue` 主表 10 列 | DONE | 原 5 列保留 |
| US-264 | AC-264-02 | `AdminSeats.vue` nicknameText/nameText/unitText；`committee/views.py` `_build_holder_detail` | DONE | 未注册持有人昵称"-"，电话脱敏 |
| US-264 | AC-264-03 | `_build_holder_detail` 绑定用户取有效 Membership | DONE | 昵称空回退账号 |
| US-265 | AC-265-01 | `committee/views.py` bucket=active；`AdminSeats.vue` 折叠区 | DONE | 待生效保留主表（GR-B-001-F02） |
| US-265 | AC-265-02 | `seat_view` end_reason；折叠表"结束原因"列 | DONE | 状态文案走 statusLabel |
| US-265 | AC-265-03 | `AdminSeatListCreateView.get` building/unit_no/floor/position | DONE | 过滤变化重置页码 |
| US-265 | AC-265-04 | `IsAdmin` 权限 | DONE | 403 既有行为 |
| US-266 | AC-266-01 | `AdminFlows.vue` 详情对话框；`flow_view` approvers.identity_label | DONE | 半数同意显示"无需设置审批人" |
| US-266 | AC-266-02 | `IsAdmin`（后端 admin 路由） | DONE | 403 |
| US-267 | AC-267-01 | `AdminFlows.saveEdit` → `admin.updateFlow` | DONE | 审计沿用后端 PUT |
| US-267 | AC-267-02 | `saveEdit` 半数同意传 `approver_ids: []` | DONE | 后端清空审批人 |
| US-267 | AC-267-03 | `apps/approval/views.py:106-112`（既有） | DONE | 有待审实例仅停用 |
| US-268 | AC-268-01 | `identity/views.py` building/unit_no/floor 过滤 | DONE | |
| US-268 | AC-268-02 | `AdminMemberships.vue` 级联选项 + `RegistryService.options` | DONE | 楼层后端按数值排序 |
| US-268 | AC-268-03 | `AdminMemberships.resetAndLoad` | DONE | 清空回第 1 页 |
| US-269 | AC-269-01 | `identity/views.py` q 增加 `registry_owner__name` | DONE | 含同住人记录 |
| US-269 | AC-269-02 | `identity/views.py` phone 4–11 位 | DONE | 响应仍 mask_phone |
| US-269 | AC-269-03 | `q` 匹配 `unit__specific_part` | DONE | |
| US-269 | AC-269-04 | `AdminMemberships.vue` 空状态"暂无匹配记录" | DONE | |
| US-270 | AC-270-01 | `UserProfile.vue`；入口：`AdminMemberships`、`AdminSeats`、`MeProfile` | PARTIAL | 决议参与人列表受既有隐私契约（禁止 user_id）限制，见架构偏差 D-03 |
| US-270 | AC-270-02 | `IdentityService.public_profile` 白名单 | DONE | 无 phone/email/birthday/account_no |
| US-270 | AC-270-03 | `router/index.js` 全局守卫 | DONE | 未登录跳 /login?redirect= |
| US-270 | AC-270-04 | `UserProfile.vue` `is_self` → 编辑资料 | DONE | |
| US-271 | AC-271-01 | `models.py` real_name_visible 默认 False | DONE | |
| US-271 | AC-271-02 | `public_profile` 返回 real_name | DONE | 仅开关开启时 |
| US-271 | AC-271-03 | `MeProfile.vue` canShowRealName；`services.py` 403 | DONE | 非业主隐藏/拒绝 |
| US-271 | AC-271-04 | `public_profile` 实时读取 | DONE | 关闭立即生效 |
| US-272 | AC-272-01 | `MeProfile.vue` textarea maxlength=100；`services.py` 校验 | DONE | 超长 400 |
| US-272 | AC-272-02 | `UserProfile.vue` 空态文案 | DONE | |
| US-272 | AC-272-03 | `UserProfile.vue` `{{ }}` 插值 | DONE | Vue 自动转义 |

## 迁移

`backend/apps/accounts/migrations/0004_user_profile_fields.py`：新增 `signature`（CharField 100，默认空串）与 `real_name_visible`（BooleanField 默认 False）；可逆（RemoveField）；无索引与回填；风险低。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| D-01 默认头像能力并入既有 `AuthImage.vue`，未新建 `UserAvatar.vue` | ADR-149 / MOD-155 | AuthImage 已统一处理带令牌取图与卸载释放，新增包装组件会重复逻辑；测试契约亦依赖 AuthImage 组件名 | 有利：单点维护；无需求影响 |
| D-02 管理端右上角未加头像 | MOD-155 | `AdminAccount` 无 avatar 字段，管理员无头像数据源 | 需求“用户”侧已满足 |
| D-03 决议参与人列表不提供 profile 入口 | MOD-162 / AC-270-01 | 既有隐私契约 TC-INT-1071 明确禁止 participants 响应含 user_id（REQ-FUNC-246）；改契约需另立需求 | AC-270-01 覆盖范围缩小为房屋关系/席位/个人资料页入口 |
| D-04 审批人摘要增补 identity_label | MOD-158（原文"如需"） | 满足 AC-266-01“昵称与身份” | 仅新增字段，不改既有字段 |

## 开放问题

- [ASSUMPTION] 楼层选项排序依赖 `RegistryService.options` 的 `sorted_values`（既有数值自然排序约定），未新增排序代码。
- [ASSUMPTION] 席位列表 `bucket` 默认 active；前端折叠区一次最多加载 50 条（超出提示后续可加分页）。
- [ASSUMPTION] 签名档去首尾空格后保存。
