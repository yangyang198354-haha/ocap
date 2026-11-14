<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-14T17:55:00+08:00</timestamp>
  <project_name>ocap_identity_display</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_display/development/implementation_plan.md</file>
    <file>project_workspace/ocap_identity_display/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：用户端身份显示与认证房屋信息

## 摘要

- 改动文件：6 个产品代码文件 + 7 个既有测试文件（仅口径断言/夹具）。
- 五维平均分：9.0。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 2。

## 文件 → MOD/IFC 映射

| 文件 | MOD/IFC |
|---|---|
| `backend/apps/committee/services.py` | MOD-101 / IFC-247 |
| `backend/apps/identity/services.py` | MOD-101 / IFC-248 |
| `frontend/src/portal/Home.vue` | MOD-102 / IFC-249、IFC-250 |
| `frontend/src/shared/style.css` | MOD-102 |
| `miniprogram/store/auth.js` | MOD-103（加载态） |
| `miniprogram/pages/index/index.vue` | MOD-103 / IFC-251 |
| `miniprogram/pages/me/index.vue` | MOD-103 / IFC-251 |
| `backend/tests/**` 7 个文件 | 既有测试口径调整 |

## 自验证结果

| 命令 | 输出尾部 |
|---|---|
| `python -m compileall -q backend` | `COMPILE_OK` |
| `python manage.py test --settings=config.test_settings`（backend） | `Ran 561 tests in 12.364s` / `OK (skipped=9)` |
| `npm test`（frontend） | `Test Files 19 passed (19)` / `Tests 181 passed (181)` |
| `npm test`（miniprogram） | `Test Files 11 passed (11)` / `Tests 75 passed (75)` |
| `npm run build`（frontend） | `✓ built in 8.43s` |
| `npm run build:mp-weixin`（miniprogram） | 失败：`Cannot read properties of undefined (reading 'vueOptions')`（uni-mp-vite 与本地依赖组合的既有问题）；`build:h5` 失败：缺少 `@dcloudio/vite-plugin-uni/lib/ssr/entry-server.js` |

未验证项：小程序 CLI 构建。原因：项目 P4 只定义 miniprogram 的 `npm test`，CI（`.github/workflows/ci.yml:83-102`）也只运行 vitest、不构建小程序；本地 CLI 构建失败与本次模板改动无关（改动前同样缺少构建入口配置）。小程序页面已由 vitest 挂载测试覆盖。

## 按模块评审

### MOD-101 后端身份与房屋聚合

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | `identity/services.py:_units` | 同一专有部分多条有效关系时按角色优先级取一条；现有唯一槽位约束下不会触发，属防御性逻辑 | OPEN |
| CR-002 | MINOR | `committee/services.py:identity_labels` | 有效职务但无房屋关系的异常数据会显示职务、`is_guest=false`；符合“职务持有者必然为产权业主”的业务前提 | OPEN |

### MOD-102 Web 主页

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

无 CRITICAL/MAJOR。

### MOD-103 小程序主页与“我的”

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

无 CRITICAL/MAJOR。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

不适用（首次实现）。

## 现有测试调整

| 文件 | 调整 | 原因 |
|---|---|---|
| `backend/tests/e2e/test_gap_journeys.py` | “户主”断言 → “产权业主” | C-34 变更后 `/me` 不再返回“户主” |
| `backend/tests/e2e/test_journeys.py` | 两处同上 | 同上 |
| `backend/tests/e2e/test_rework_journeys.py` | 同上 | 同上 |
| `backend/tests/integration/test_gap_must_have.py` | 四处同上 | 同上 |
| `backend/tests/integration/test_registry_import_enhancement.py` | 同上 | 同上 |
| `backend/tests/integration/test_frontend_contract.py` | 主任+产权业主用户断言 `labels == ["主任"]` | 职务优先（Q-ID-01） |
| `backend/tests/integration/test_specific_part_display_consistency.py` | `units[]` 字段集合增加 5 个展示字段 | IFC-248 契约扩展 |
