<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T09:09:30+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>testing/unit_test_report.md</file><file>development/implementation_plan.md（2.0.0）</file><file>architecture/module_design.md（1.0.0）</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告：品牌更名 + 左侧导航布局（INCREMENTAL，GROUP_D-003，缺陷回流 1/2 后重跑）

## 摘要

- 执行时间：2026-11-17T09:01:45+08:00 起（DEF-001/002 修复后重跑，45.7s）；环境：Node + vitest（jsdom + @vue/test-utils + Element Plus + Pinia），无外网，HTTP 全部 mock。
- 命令：`(cd frontend && npx vitest run --passWithNoTests tests/layout_nav.spec.js tests/layout_router.spec.js tests/user_menu.spec.js tests/auth_shell.spec.js tests/layout_pages.spec.js tests/layout_contract.spec.js tests/qa_int_theme.spec.js)`
- INT 层范围：新写 101 条 + 既有 qa_int_theme 15 条（含已同步的 TC-INT-103/105 共 4 条）。
- total = pass + fail + skip + blocked + not_testable = 116 + 0 + 0 + 0 + 0 = 116（新写 101：pass 101；既有 15：pass 15）。
- 通过率 = pass/(pass+fail+blocked) = 116/116 = 100%；新写用例通过 101/101。
- 判定模式 baseline：既有用例零新增失败（0），新写用例全部通过。**本层门控：PASSED**（0.1.0 为 FAILED：TC-INT-874/914，现均已转绿，见下）。
- 契约（规则 17）：TC-INT-921~926 全部 PASS；`git diff --stat HEAD -- frontend/src/shared/api.js miniprogram/utils/api.js backend` 输出 0 行（09:07 复核）。既有后端契约测试 `backend/tests/integration/test_frontend_contract.py` **未运行**（本机无 Django，且其读取的两份 api.js 零改动），不标 PASS，不计入以上数字。

## 执行输出

```
Test Files  7 passed (7)
     Tests  116 passed (116)
exit=0
```

按文件：layout_nav 19、layout_router 14、user_menu 14、layout_contract 6、qa_int_theme 15、auth_shell 14、layout_pages 34，全部通过。

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
| 既有集成（风格/布局，已同步） | qa_int_theme 15 条（含 TC-INT-103/105 同步 4 条） | AC-074~086 等 | 15/15 PASS | — |

## 与基线对比（baseline 模式）

- 基线 281/281；既有用例失败 0 条，新增失败（既有用例）0 条；39 条同步用例中本层 4 条全部 PASS。
- 新写用例失败 0 条。

## 失败汇总（需路由给开发）

无（本层 0 失败；DEF-001、DEF-002 已修复并回归通过）。
