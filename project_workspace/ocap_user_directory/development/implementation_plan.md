<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T22:37:00.8286889+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file></input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 实现计划

## 实现概览

- 模块数：2（MOD-062 后端聚合、MOD-063 Web 后台展示）；文件数：5（3 个后端、2 个前端）。
- 实现顺序：MOD-062 → MOD-063（前端依赖后端响应字段）。
- 无数据库迁移、无新增依赖。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-062 | `backend/apps/accounts/directory.py` | 新建 | 既有 residency/committee/registry 模型 | M | 身份优先级、认证套数、清册实名、实名搜索 Q 条件 | DONE |
| 2 | MOD-062 | `backend/apps/accounts/serializers.py` | 修改 | 1 | L | `AdminUserSerializer` 增加 identity_code/identity_label/certified_units/real_names/last_login_at | DONE |
| 3 | MOD-062 | `backend/apps/accounts/views.py` | 修改 | 1、2 | M | `AdminUserListView` 固定预取、搜索 OR 实名条件 | DONE |
| 4 | MOD-063 | `frontend/src/shared/format.js` | 修改 | — | L | 新增 `formatDateTime(value)` → `YYYY-MM-DD HH:mm`，空值空串 | DONE |
| 5 | MOD-063 | `frontend/src/admin/AdminUsers.vue` | 修改 | 4 | L | 新增身份/认证/实名/上次登录四列；搜索占位追加“实名” | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件） | 状态 | 说明 |
|---|---|---|---|---|
| US-132 | AC-132-01 身份与认证基础展示 | `backend/apps/accounts/directory.py:identity_view`、`certified_units`；`frontend/src/admin/AdminUsers.vue` 身份/认证列 | DONE | |
| US-132 | AC-132-02 主任优先于户主 | 同上 `identity_view` 的 POSITION_RANK 分支 | DONE | |
| US-132 | AC-132-03 副主任优先于产权业主 | 同上 | DONE | |
| US-132 | AC-132-04 过期席位不计 | `backend/apps/accounts/views.py` 预取 Seat 过滤 + `identity_view` 二次过滤 | DONE | |
| US-132 | AC-132-05 多套认证计数 | `directory.py:certified_units`（unit_id 去重） | DONE | |
| US-132 | AC-132-06 非管理员拒绝 | 沿用 `AdminUserListView.permission_classes=[IsAdmin]` | DONE | 未改权限 |
| US-133 | AC-133-01 单套实名 | `directory.py:real_names` + `serializers.py:to_representation` | DONE | |
| US-133 | AC-133-02 多套姓名并列 | `real_names` 去重保序，前端 `join('、')` | DONE | |
| US-133 | AC-133-03 同名去重 | `real_names` 列表去重 | DONE | |
| US-133 | AC-133-04 非业主/无手机号/未匹配显示“—” | `real_names` 返回空列表；`AdminUsers.vue` 空值“—” | DONE | |
| US-133 | AC-133-05 撤销后不显示实名 | `views.py` 预取 `ended_at__isnull=True`；`real_names` 只取有效 HEAD/OWNER | DONE | |
| US-134 | AC-134-01 时间格式 | `frontend/src/shared/format.js:formatDateTime` | DONE | |
| US-134 | AC-134-02 从未登录 | `AdminUsers.vue` 空值“从未登录” | DONE | |
| US-134 | AC-134-03 取最近一次登录 | `User.last_login_at`（既有字段，登录时更新） | DONE | |
| US-134 | AC-134-04 绝对时间 | `formatDateTime` 截取到分钟 | DONE | |
| US-135 | AC-135-01 原列/脱敏保留 | `serializers.py` 保留 phone=MaskedPhoneField；`AdminUsers.vue` 原列不动 | DONE | |
| US-135 | AC-135-02 实名搜索命中 | `views.py` 搜索条件 OR `real_name_q(q)` | DONE | |
| US-135 | AC-135-03 原搜索不变 | `views.py` 保留原条件分支 | DONE | |
| US-135 | AC-135-04 未命中空列表 | 既有分页逻辑 | DONE | |
| US-135 | AC-135-05 分页/排序不变 | `page_response` 与 `order_by("id")` 不变 | DONE | |
| US-136 | AC-136-01 撤销后回游客 | 预取过滤 + `directory.py` 有效记录计算 | DONE | |
| US-136 | AC-136-02 部分撤销计数与实名 | `certified_units`、`real_names` 按有效 Membership | DONE | |
| US-136 | AC-136-03 户主撤销后同住人身份 | `identity_view` ROLE_RANK 回退 | DONE | |
| US-136 | AC-136-04 席位到期回退 | Seat 预取 `term_end >= today` + `identity_view` 过滤 | DONE | |

## 迁移

无。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| IFC-246 以返回 `Q` 的 `real_name_q()` 实现，而不是直接返回过滤后的 QuerySet | IFC-246 `filter_by_real_name` | 现有搜索条件是 OR 组合，返回 Q 才能与账号/昵称/手机号条件并集 | 语义不变；调用方在 `views.py` 统一 `qs.filter(condition | real_name_q(q))` |

## 开放问题

- [ASSUMPTION] 前端时间格式化为字符串截取（后端 DRF 按 `Asia/Shanghai` 输出带偏移的 ISO8601），不依赖浏览器时区；若未来客户端需要本地时区，再统一改造。
