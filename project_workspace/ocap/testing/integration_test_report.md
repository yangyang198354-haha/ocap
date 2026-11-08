<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T22:59:07+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.4.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>DRAFT</status>
</file_header>

> 复跑说明（ocap-GROUP_D-7）：GROUP_C-5 返工后重跑。REWORK_AUTHORIZED: project_workspace/ocap/testing/。

## 摘要

- 执行时间：2026-11-08 22:55 ~ 22:56（Asia/Shanghai）。
- 环境：同单元层报告。
- 命令：
  - `(cd backend && python manage.py test tests.integration --settings=config.test_settings)`
  - `(cd frontend && npx vitest run)`（pages.spec.js 归入本层）
  - `(cd miniprogram && npx vitest run)`（pages.spec.js 归入本层）
- 本层用例：后端 99（71 既有 + 28 新写）+ Web 页面挂载 14 + 小程序页面挂载 14 = 127。
- total = pass + fail + skip + blocked + not_testable = 127 = 126 + 1 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 126/(126+1+0) = 99.21%。
- 判定模式与阈值：FULL_FLOW threshold，integration_pass = 0.90。
- **本层门控：PASSED**（99.21% ≥ 90%）。唯一失败是产品缺陷 DEF-005，须回流 GROUP_C，见下。

## 执行输出

```
$ (cd backend && python manage.py test tests.integration --settings=config.test_settings)
AssertionError: ... frontend/src/shared/api.js:132 GET /admin/registry/units/${id}: 视图 AdminUnitDetailView 不支持该方法
Ran 99 tests in 4.424s
FAILED (failures=1)

$ (cd frontend && npx vitest run)
 ✓ tests/api.spec.js (11 tests)
 ✓ tests/auth.store.spec.js (8 tests)
 Test Files  3 passed (3)
      Tests  33 passed (33)

$ (cd miniprogram && npx vitest run)
 ✓ tests/pages.spec.js (14 tests)
 ✓ tests/api.spec.js (11 tests)
 ✓ tests/store.spec.js (2 tests)
 Test Files  3 passed (3)
      Tests  27 passed (27)
```

Web 33 = 单元层 19 + 本层 14；小程序 27 = 单元层 13 + 本层 14。

## 分项结果

| 集成边界 | TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| 既有 API 集成（auth / residency / approval / finance / polls） | TC-INT-001~072（不含 071 作废） | 见 test_plan | 既有 71 个用例（含已更新的 TC-INT-057） | PASS（71） | — | — |
| 收入导入 ↔ 视图 | TC-INT-073 | AC-059-05 | 全部行错误：200、sheet=None、不建表 | PASS | — | — |
| 前端 api.js ↔ 后端路由/视图（契约） | TC-INT-083、084 | 画像 P5 | 小程序 api.js 全部调用可解析且方法受支持；GR-C-004 错误路径不再出现 | PASS（2） | — | — |
| Web api.js ↔ 后端路由/视图（契约） | TC-INT-082 | 画像 P5 | Web api.js 每个调用可解析路由且视图支持该 HTTP 方法 | **FAIL** | `frontend/src/shared/api.js:132 GET /admin/registry/units/${id}: 视图 AdminUnitDetailView 不支持该方法` | 产品缺陷（DEF-005） |
| 前端字段 ↔ 后端响应（契约） | TC-INT-074~081 | US-001/003/036/040/041/049~059/012/014/028/070 | identities 对象与键、职位枚举、claims 载荷与旧结构拒绝、polls 创建与 responses、income sheets、手机号绑定/换绑响应、登录 is_new | PASS（8） | — | — |
| identity ↔ polls/resolutions（账号合并） | TC-INT-085~089 | AC-012-01/02/03、AC-014-01、AC-072-01/02 | 绑定/换绑合并、答卷冲突保留主账号并审计、仅副账号作答并入、未占用号仅绑定、错码不合并 | PASS（5） | — | — |
| claims ↔ ledger（核销） | TC-INT-090~094 | AC-051-01~06 | 预借通过计入；补差 1200；多退 800；恰好相等 1000；缺报销单与重复核销被拒 | PASS（5） | — | — |
| jobs ↔ ledger | TC-INT-095 | AC-061-01/02 | run_due_jobs 生成上季/上年报表且幂等 | PASS | — | — |
| income 逐条录入与导入 | TC-INT-096~099 | AC-058-01/02/03/08、AC-059-02/05 | 逐条录入；非法金额与非成员；文件内重复；与 PENDING 表重复 | PASS（4） | — | — |
| attachments ↔ residency（管理员下载） | TC-INT-100 | US-026 | 管理员可下载申诉证明；无关用户 404；未登录 401 | PASS | — | — |
| Web 页面 ↔ api/store（HTTP 层 mock） | TC-WEB-017~030 | US-041、049~057、012、014、017 | 首页身份、Claims 表单与核销、PollDetail、Me 手机号/改密/注销 | PASS（14） | — | — |
| 小程序页面 ↔ api/store（uni 桩） | TC-MP-014~027 | US-003、012、014、041、045、049~057 | 首页与待办、claims、投票、手机号页、登录 | PASS（14） | — | — |

计数核对：后端 71+1+2+1+8+5+5+1+4+1 = 99（通过 98，失败 1）；Web 14；小程序 14；合计 127（126 通过，1 失败）。契约三条路由用例的编号：Web = TC-INT-082（失败）、小程序 = TC-INT-083、已知错误路径 = TC-INT-084。

## GR-C-005 condition 核对（本层相关）

| 条件 | 结果 |
|---|---|
| ① AC-059-03/05 两条旧用例更新 | 已更新并通过：`IncomeTests::test_import_row_error_ratio`（201，imported=40、failed=3）、单元 `test_row_error_ratio_over_2_percent`；并新增 `test_import_all_rows_skipped_creates_nothing` |
| ② 前后端契约测试（路由、方法、关键字段） | 已有 `tests/integration/test_frontend_contract.py` 11 个用例；覆盖 identities、claims、polls responses、income sheets、手机号绑定/换绑、登录响应；已发现 DEF-005 |
| ③ Web/小程序 vitest（store、api 路径、页面挂载） | 已有：Web 33、小程序 27，全部通过 |
| ④ §9 建议用例 | 合并冲突、核销补差/退款/恰好相等、generate_due 幂等、逐条录入与重复导入、管理员下载附件、缺 SECRET_KEY 拒绝启动均已覆盖 |
| mock 层次 | 仅 http 层（Web `vi.mock('@/shared/http')`；小程序 `uni.request/uploadFile` 桩）；未 mock api.js、store 或页面自身（`git grep "vi.mock\|spyOn" frontend/tests miniprogram/tests` 仅见 http 层） |

## 与基线对比

基线（画像 P4）：后端集成 71/71 通过。本次既有 71 个用例全部通过（TC-INT-057 按 AC-059-03 更新断言）。新写 28 个后端用例中 27 通过、1 失败（TC-INT-082，契约测试，产品缺陷）。新增失败 1 条：`RouteContractTests.test_web_api_routes_exist_and_support_method`（新增用例首次暴露，非既有失败，依据：基线中无该用例；根因为前端调用不存在的 GET 详情方法）。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| TC-INT-082（`test_web_api_routes_exist_and_support_method`） | Web `registryUnit(id)` 发 `GET /admin/registry/units/${id}`，后端 `AdminUnitDetailView` 只实现 patch/delete，GET 返回 405 | `frontend/src/shared/api.js:132`；`backend/apps/registry/views.py:62` | DEF-005 |
