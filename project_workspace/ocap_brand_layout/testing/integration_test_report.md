<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T14:30:24+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>testing/unit_test_report.md</file><file>development/implementation_plan.md（2.0.0）</file><file>architecture/module_design.md（1.0.0）</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告：品牌更名 + 左侧导航布局（INCREMENTAL，GROUP_D-003，缺陷回流 1/2 后重跑；1.1.0：GR-D-003 更正，补后端层）

## 摘要

- 执行时间：2026-11-17T09:01:45+08:00 起（DEF-001/002 修复后重跑，45.7s）；环境：Node + vitest（jsdom + @vue/test-utils + Element Plus + Pinia），无外网，HTTP 全部 mock。
- 命令：`(cd frontend && npx vitest run --passWithNoTests tests/layout_nav.spec.js tests/layout_router.spec.js tests/user_menu.spec.js tests/auth_shell.spec.js tests/layout_pages.spec.js tests/layout_contract.spec.js tests/qa_int_theme.spec.js)`
- INT 层范围：前端新写 101 条 + 既有 qa_int_theme 15 条（含已同步的 TC-INT-103/105 共 4 条）+ 后端 `tests.integration` 既有 687 条（含本次同步的 6 条契约用例）。
- 后端命令：`(cd backend && <PM venv>/bin/python manage.py test tests.integration --settings=config.test_settings)`，2026-11-17T14:21 起，Ran 687 tests，OK。
- total = pass + fail + skip + blocked + not_testable = 803 + 0 + 0 + 0 + 0 = 803（前端 116 + 后端 687；新写 101、既有 702，其中 6 条后端契约用例为 1.1.0 修改）。
- 通过率 = pass/(pass+fail+blocked) = 803/803 = 100%；新写用例通过 101/101。
- 判定模式 baseline：既有用例零新增失败（0），新写用例全部通过。**本层门控：PASSED**（0.1.0 为 FAILED：TC-INT-874/914，现均已转绿，见下）。
- 契约（规则 17）：TC-INT-921~926 全部 PASS；`git diff --stat HEAD -- frontend/src/shared/api.js miniprogram/utils/api.js backend` 输出 0 行（09:07 复核）。既有后端契约测试 1.0.0 称"未运行"属误判（GR-D-003-F01）：这些用例还静态读取页面源码，页面拆分令 6 条失败；1.1.0 已修复并实跑，见下节。

## 执行输出

```
(frontend, 7 files)   Test Files  7 passed (7)
                           Tests  116 passed (116)
                      exit=0
(backend tests.integration, 14:21，1.1.0 修复后)
                      Ran 687 tests in 50.528s
                      OK
```
修复前（同环境、HEAD 1133794 未改测试的本地复现）：`Ran 957 tests ... FAILED (failures=6)`，与 CI run 44026380990 一致；修复后全量 `Ran 957 tests in 72.082s  OK`。

按文件：layout_nav 19、layout_router 14、user_menu 14、layout_contract 6、qa_int_theme 15、auth_shell 14、layout_pages 34，全部通过。

## GR-D-003 更正：后端 6 条契约用例同步页面拆分（1.1.0）

**根因**：用例静态读取 `frontend/src/portal/Units.vue`、`Me.vue`；MOD-122/123 把页面逻辑拆到 `portal/units/*.vue`（6 个）、`portal/me/*`（6 个 vue + `useProfile.js`），宿主文件只剩分区路由/总览，字段名、调用、错误码不再在宿主中。产品行为无误（字段在拆分文件中；前端 layout_contract 6/6 与线上验证通过），属**测试问题**、非产品缺陷，无 DEF。

**改法**：不降低任何断言，只扩大"读取源码"范围：新增 `src_split(host, split_dir)`（`test_frontend_contract.py`：宿主 + 拆分目录全部 `*.vue`/`*.js` 拼接，目录为空即断言失败）与 `web_units_bundle()`（`test_owner_auth_v2_contract.py`：Units.vue + `portal/units/*.vue`）。否定断言作用于拼接后的全文 = 对每个拆分文件都成立。

| 用例（TC） | 原意 | 新写法 |
|---|---|---|
| `FieldContractTests.test_phone_bind_change_contract` | Web 改密提交 `password_confirm` | `assertIn("password_confirm", src_split(Me.vue, portal/me))`；实际位于 `me/MePassword.vue:23` |
| `ProductReviewFieldContractTests.test_tc_int_487` | Web 申请同住人时 `createResidentApplication({ unit_id` 正则 | 同一正则作用于 `src_split(Units.vue, portal/units)`；位于 `units/UnitsPick.vue:57` |
| `…test_tc_int_488` | /me/housing 字段 ⊇ Web 我的房屋/我的页读取字段（`reads(...)` 子集断言、`housing.summary.label`、`role_label/specific_part/residents/joined_at`） | `web_units`、`web_me` 改为 `src_split`；全部断言原样保留；`housing.summary.label` 位于 `units/UnitsIdentity.vue:6` |
| `…test_tc_int_490` | 三个列表响应字段 ⊇ 页面读取字段，且页面读取 `reject_reason/submitted_at/created_at/decided_at` | Web 侧文本改为 `src_split(Units.vue, portal/units)`；子集断言与"必须读取"断言原样；`reject_reason` 位于 `units/UnitsMyAppeals.vue:13` |
| `AppealContractTests.test_tc_int_713` | Web/小程序调 `createAppeal` 发送的键恰为 `{unit_id, owner_name, proof_ids}` | `appeal_keys_from` 对 Web units 用 `web_units_bundle()`；键集合断言不变；位于 `units/UnitsAppeal.vue:55` |
| `LevelLabelAndSeatContractTests.test_tc_int_719` | 两端页面含 `OWNER_NOT_MATCHED`，且不含 `PHONE_NOT_IN_REGISTRY`、`PHONE_REQUIRED` | Web 侧用 `web_units_bundle()`（宿主 + 6 个拆分文件）；肯定与否定断言均不变；`OWNER_NOT_MATCHED` 位于 `units/UnitsPick.vue:44` |
| 逐级选房字段检查（`test_frontend_contract.py:450` 附近，原本经 UnitCascader.vue 仍通过） | Web 页面含 level/skipped/has_empty/label | 预防性同步为 `src_split`，不再依赖宿主文件内容 |

**其他引用扫描**：对 backend/tests 中 `frontend/…`、`miniprogram/…` 路径字面量逐一 `os.path.exists` 校验，**无缺失文件**；被拆分的仅 `Units.vue`、`Me.vue`，上表已覆盖其全部引用点；`AdminThemeSwitcher.vue` 在 backend/tests 无任何引用（前端 `qa_unit_theme.spec.js:264` 只断言其不存在，通过）。`FieldContractTests.setUp` 的 `web_sources` 用 `rglob("*.vue")`，已含拆分文件，无需改。

## 缺陷回归（0.1.0 失败用例，未改动测试，修复后重跑）

| DEF | 级别 | 回归用例 | 修复位置 | 0.1.0（修复前） | 0.2.0（修复后） |
|---|---|---|---|---|---|
| DEF-001 | MINOR | TC-INT-874（`auth_shell.spec.js`，`artFor('__proto__'/'constructor'/'toString'/'hasOwnProperty')` → BentoArt，AC-209-02、IFC-327） | `frontend/src/brand/art/index.js:10`（`Object.hasOwn(ARTS, themeKey)`） | FAIL | **PASS** |
| DEF-002 | MAJOR | TC-INT-914（`layout_pages.spec.js`，真实登录链路：`setAuth` 简要对象 → `fetchMe` 补全 → 展开"我的房屋"，角标 2，AC-214-03） | `frontend/src/portal/PortalLayout.vue:49`（`!auth.me \|\| !auth.me.identities` 时先 `fetchMe()`） | FAIL | **PASS** |

- 修复前失败证据：0.1.0 实跑与 PM 的 GR-D-001 复跑均为 `2 failed | 436 passed (438)`，失败即这两条；用例未改动，故修复后转绿可归因于产品修复。
- 复核修复与契约一致：IFC-327（其他/缺失 → BentoArt）、AC-214-03（角标 2）。复核读码：`art/index.js:8-11`、`PortalLayout.vue:46-50`。

## 分项结果（集成边界）

| 集成边界 | TC | AC | 结果 | 根因分类 |
|---|---|---|---|---|
| MOD-120 SideNav ↔ 路由/菜单配置 | TC-INT-801~819 | AC-210-02/03、211-01、213、214-02/03、215-04、216-01~04、217-01/02、224-01/02、225-01/02/04、229-02、230-01/02/04 | 19/19 PASS | — |
| MOD-127 路由表 ↔ 守卫/布局 | TC-INT-821~834 | AC-207-03、210-03/04、213-01、214-02、215-01/02/04、220-05、221-01~03、223-03、224-04、225-02/03 | 14/14 PASS | — |
| MOD-121/125 用户菜单 ↔ Pinia/路由/adminHttp | TC-INT-841~854 | AC-212-01~05、213-01、226-01~05 | 14/14 PASS | — |
| MOD-128 AuthShell ↔ 主题仓库/登录页 | TC-INT-861~873 | AC-207-01/02、209-01/02/05/06、226-01、227-01~03 | 13/13 PASS | — |
| MOD-119/128 配图注册表（DEF-001 回归） | TC-INT-874 | AC-209-02、IFC-327 | PASS（0.1.0 FAIL） | 已修复 |
| MOD-121~126 布局+页面+仓库 | TC-INT-881~913（含 885~887、890~913） | AC-210-01、211-01/03/04、212-05、213-01~04/06、214-02/03、215-01~03、220-01~05、222-02/03、223-01、224-01、225-01~03/05、229-03、230-01/02/04、231-03/04 | 33/33 PASS | — |
| MOD-121/123 PortalLayout ↔ housing 仓库 ↔ auth（DEF-002 回归） | TC-INT-914 | AC-214-03 | PASS（0.1.0 FAIL） | 已修复 |
| 前后端契约（api.js ↔ 页面 ↔ urls.py） | TC-INT-921~926 | REQ-NFUNC-040、AC-209-06、213-02、214-05、225-02 | 6/6 PASS | — |
| 后端契约 ↔ 前端源码（GR-D-003 同步的 6 条） | test_phone_bind_change_contract、TC-INT-487/488/490、TC-INT-713、TC-INT-719 | AC-178-02、157-01、151-01、152-01、156-02、199-01 等 | 6/6 PASS（修复前 6 FAIL，根因：测试问题） | 已修复（测试同步） |
| 后端 tests.integration 其余（既有） | 681 条 | 既有 | 681/681 PASS | — |
| 既有集成（风格/布局，已同步） | qa_int_theme 15 条（含 TC-INT-103/105 同步 4 条） | AC-074~086 等 | 15/15 PASS | — |

## 与基线对比（baseline 模式）

- 基线 前端 281/281、后端 CI 3df752b `Ran 957, OK`；既有用例失败 0 条（后端 6 条曾因测试读取已拆分页面而失败，已同步转绿，属测试问题、非既有失败），新增失败（既有用例）0 条；39 条同步用例中本层 4 条全部 PASS。
- 新写用例失败 0 条。

## 失败汇总（需路由给开发）

无（本层 0 失败；DEF-001、DEF-002 已修复并回归通过；后端 6 条为测试代码问题，已由 GROUP_D 修复）。
