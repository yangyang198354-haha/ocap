<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-19T00:15:00+08:00</timestamp>
  <project_name>ocap_profile_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_ux/development/implementation_plan.md</file>
    <file>project_workspace/ocap_profile_ux/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — ocap_profile_ux

## 摘要

`git diff --stat`：24 个已跟踪文件，+645 / -61；另有 4 个新建未跟踪文件（`backend/apps/accounts/migrations/0004_user_profile_fields.py`、`frontend/src/portal/UserProfile.vue`、`frontend/src/assets/avatar-default.svg`、`project_workspace/ocap_profile_ux/**`）。

五维平均分：8.2 / 10。问题统计：CRITICAL 0；MAJOR 0；MINOR 5（已修复 2，遗留 3）。

## 文件 → MOD/IFC 映射

| 文件 | MOD | IFC |
|---|---|---|
| `backend/apps/accounts/models.py`、`migrations/0004_user_profile_fields.py`、`services.py`、`views.py` | MOD-153 | IFC-368、IFC-369 |
| `backend/apps/core/attachments.py` | MOD-156 | IFC-376 |
| `backend/apps/identity/services.py` | MOD-154 | IFC-370 |
| `backend/apps/identity/views.py`、`urls.py` | MOD-154、MOD-159 | IFC-370、IFC-374 |
| `backend/apps/committee/views.py` | MOD-157 | IFC-372 |
| `backend/apps/approval/views.py` | MOD-158 | IFC-373（复用） |
| `frontend/src/assets/avatar-default.svg`、`portal/parts/AuthImage.vue`、`portal/PortalUserMenu.vue` | MOD-155 | IFC-371 |
| `frontend/src/portal/me/MeProfile.vue`、`useProfile.js` | MOD-163 | IFC-368/369 |
| `frontend/src/portal/UserProfile.vue`、`router/index.js`、`shared/api.js` | MOD-162 | IFC-370、IFC-375 |
| `frontend/src/admin/AdminSeats.vue` | MOD-160 | IFC-372 |
| `frontend/src/admin/AdminMemberships.vue` | MOD-161 | IFC-374 |
| `frontend/src/admin/AdminFlows.vue` | MOD-158 | IFC-373 |

## 自验证结果

| 命令 | 输出尾部 | 结论 |
|---|---|---|
| `python -m compileall -q backend` | `COMPILE_OK` | 通过 |
| `python manage.py test --settings=config.test_settings`（backend/） | `Ran 1131 tests in 51.979s` / `FAILED (failures=6, skipped=1)` | 新增失败 0；6 个失败均在既有导出/搬迁/备份用例（Windows 下 chmod 0600 断言），相关文件本次未改动（见"遗留 MAJOR"说明） |
| `python manage.py test tests.integration.test_batch1118_seats tests.integration.test_half_majority_flow_approvers` | `Ran 27 tests` / `OK` | 通过 |
| `python manage.py test ...ParticipantsEndpointTests.test_tc_int_1071 ...test_tc_int_1040` | `OK`（2 tests） | 通过（修复 N+1 后） |
| `cd frontend && npx vitest run tests/batch1118_admin.spec.js` | `Test Files 1 passed` | 通过 |
| `cd frontend && npx vitest run tests/layout_css.spec.js tests/batch1118_admin.spec.js tests/batch1118_resolution_nav.spec.js tests/layout_contract.spec.js` | 3 passed / 1 failed（仅 TC-UNIT-873 Login.vue 预存失败） | 通过（除预存项） |
| `cd frontend && npx vitest run tests/layout_e2e.spec.js tests/identity_property_e2e.spec.js` | 2 passed | 通过 |
| `cd frontend && npm test`（全量） | `Test Files 5 failed | 40 passed (45)` | 失败 5 个文件：3 个预存（TC-UNIT-873、qa TC-103、theme_build）+ 2 个路由 spec 在满载并行下超时，单跑均通过 |
| `cd frontend && npm run build` | `✓ built in 15.65s` | 通过 |

未验证项：jsdom 不计算像素对齐（AC-260-01/02 需真实浏览器/人工走查）；REQ-NFUNC-053 的 5000 条响应时间为推断指标，未做压测。

## 按模块评审

### MOD-153 / 154 / 156（账号资料、公开 profile、上传上限）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `backend/apps/identity/services.py:83-116` | public_profile 直接复用 identity_view，身份聚合口径与 `/me` 一致；无敏感字段 | OPEN（设计符合） |
| CR-002 | MINOR | `backend/apps/accounts/services.py:395-410` | `real_name_visible=True` 时校验有效产权认证，避免未认证用户开启 | FIXED |

### MOD-157 / 160（席位接口与页面）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 7/10 | 8/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MINOR | `backend/apps/committee/views.py:62-83` | 初版 `owner.phones.first()` 导致逐行查询（12 vs 8），TC-INT-1040 失败 | FIXED（改为批量预取 RegistryPhone） |
| CR-004 | MINOR | `frontend/src/admin/AdminSeats.vue` | 折叠区一次加载 50 条、无分页；超大数据需后续补分页 | OPEN（记录于 implementation_plan） |
| CR-005 | MINOR | `frontend/src/admin/AdminSeats.vue` | 操作列 220px 在窄屏可能换行，为保证 ADR-121 宽度预算（≤1090） | OPEN（人工走查项） |

### MOD-158 / 161 / 162 / 163 / 155（审批流程、房屋关系、profile、资料页、头像展示）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 9/10 | 8/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MINOR | `frontend/src/portal/parts/ParticipantList.vue` | 初版为参与人加 profile 链接需要后端返回 user_id，与既有隐私契约（TC-INT-1071 禁止 user_id）冲突 | FIXED（回退改动，入口限定于房屋关系/席位/个人资料页，见偏差 D-03） |
| CR-007 | MINOR | `frontend/src/admin/AdminFlows.vue` | 编辑保存时 scope/mode 变化有二次确认；PUT 为全量覆盖，依据行内 approvers 预填 | OPEN（符合 ADR-154） |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。说明：后端 6 个失败用例（`test_owner_auth_v2_*`、`test_registry_export_cmd`、`test_underground_relocation_cmd`）断言文件权限 `0o600` 与仓库根写入行为，Windows 上语义不同；对应产品代码与测试本次均未改动，判定为环境预存失败，交 GROUP_D 以基线口径复核。

## 缺陷修复

本批次非缺陷修复模式。

## 现有测试调整

| 文件 | 调整 | 原因 |
|---|---|---|
| `frontend/tests/batch1118_admin.spec.js` | 待绑定/冲突行断言拆为"坐落/姓名/标签"独立断言 | 持有人信息已由一行拼接改为分列（REQ-FUNC-258） |
| `frontend/tests/layout_css.spec.js` | AdminSeats 表格基线 6 列 1040 → 10 列 1070 | 新增 4 列且总宽仍在 1090 预算内 |
| `frontend/tests/layout_contract.spec.js` | meApi 基线加入 `userProfile` | 新增 IFC-370 客户端函数 |
| `frontend/tests/layout_pages.spec.js` | 头像超限用例 3MB/2MB → 6MB/5MB 文案 | REQ-FUNC-257 阈值变更 |
| `frontend/tests/product_review_ui.spec.js` | 同上（2MB → 5MB） | 同上 |
| `frontend/tests/qa_unit_theme.spec.js` | 路由页面组件计数 17 → 18 | 新增 UserProfile 页面 |

后端测试未做修改（参与者 `user_id` 的临时改动已回退）。
