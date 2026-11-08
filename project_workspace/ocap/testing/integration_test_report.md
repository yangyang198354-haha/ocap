<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-08T23:38:30+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-9，续 -8）：GR-C-007 已批准 DEF-006 / OBS-001 修复；本次复跑 TC-INT-106 PASS，DEF-006 标 CLOSED，OBS-001 标已修复；按 GR-C-007 condition 将匿名请求断言收紧为只接受 401（TC-INT-125、130、146，见下）。以下为 -8 的历史说明：GR-D-006 FAIL 修正。(1) 按 GR-D-006-F01 为 US-006/010/013/025/028/035/042/068/070/071/073 逐 AC 补映射并补写用例（另顺带补 US-002 可测部分）：后端 TC-INT-101~149（49 个，`tests/integration/test_gap_must_have.py`）、Web TC-WEB-031~033（`frontend/tests/login.spec.js`）、小程序 TC-MP-028~030。(2) DEF-005 复跑：TC-INT-082 PASS，标 CLOSED。(3) 新用例 TC-INT-106 暴露产品缺陷 DEF-006。REWORK_AUTHORIZED: testing/ 下 4 份文件与三处测试代码目录。

## 摘要

- 执行时间：2026-11-08 23:36 ~ 23:38（Asia/Shanghai，ocap-GROUP_D-9 最后一次执行）。
- 环境：同单元层报告。
- 命令：
  - `(cd backend && python manage.py test tests.integration --settings=config.test_settings)`
  - `(cd frontend && npx vitest run)`（pages.spec.js、login.spec.js 归入本层）
  - `(cd miniprogram && npx vitest run)`（pages.spec.js 归入本层）
- 本层用例：后端 148（71 既有 + 77 新写）+ Web 页面挂载与登录 17 + 小程序页面挂载 17 = 182。
- total = pass + fail + skip + blocked + not_testable = 182 = 182 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 182/(182+0+0) = 100.00%。
- 判定模式与阈值：FULL_FLOW threshold，integration_pass = 0.90。
- **本层门控：PASSED**（100.00% ≥ 90%）。TC-INT-106 在 DEF-006 修复后 PASS，**DEF-006 标 CLOSED**；OBS-001（匿名访问管理端返回 403）已修复为 401。
- DEF-005：TC-INT-082（`RouteContractTests.test_web_api_routes_exist_and_support_method`）本次 PASS，`git grep registryUnit\( -- frontend/src` 无命中（GR-C-006 已删除 `registryUnit`），**DEF-005 标 CLOSED**。

## 执行输出

```
$ (cd backend && python manage.py test tests.integration --settings=config.test_settings)
Ran 148 tests in 5.203s
OK

$ (cd backend && python manage.py test tests.integration.test_gap_must_have --settings=config.test_settings)
Ran 49 tests in 1.884s
OK

$ (cd backend && python manage.py test tests.integration.test_frontend_contract -v 2 --settings=config.test_settings)
test_known_bad_paths_from_gr_c_004_are_gone ... ok
test_miniprogram_api_routes_exist_and_support_method ... ok
test_web_api_routes_exist_and_support_method ... ok
Ran 11 tests in 0.477s
OK

$ (cd frontend && npx vitest run)
 ✓ tests/pages.spec.js (14 tests)
 ✓ tests/api.spec.js (11 tests)
 ✓ tests/login.spec.js (3 tests)
 ✓ tests/auth.store.spec.js (8 tests)
 Test Files  4 passed (4)
      Tests  36 passed (36)

$ (cd miniprogram && npx vitest run)
 ✓ tests/pages.spec.js (17 tests)
 ✓ tests/api.spec.js (11 tests)
 ✓ tests/store.spec.js (2 tests)
 Test Files  3 passed (3)
      Tests  30 passed (30)
```

Web 36 = 单元层 19 + 本层 17；小程序 30 = 单元层 13 + 本层 17。

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
| auth ↔ 验证码/限流（US-006） | TC-INT-101~105、107 | AC-006-01/02/03/04 | 验证码登录、手机号 + 密码登录、三种失败情形文案一致、错码、过期码、密码 5 次错锁定 900 秒 | PASS（6） | — | — |
| auth ↔ 验证码（US-006） | TC-INT-106 | AC-006-04 | 同一验证码输错 5 次作废；第 5 次 429 后，输入**正确**验证码仍被拒（400/429） | PASS（DEF-006 已修复，CLOSED） | — | — |
| accounts ↔ integrations/wechat ↔ residency（三入口同一账号，US-010/070/002） | TC-INT-108~113、147~149 | AC-010-01/02/03、AC-070-01/02/03/04、AC-002-02/03/04 | Web / 小程序 / 密码登录同一 id；微信绑定手机号后三种登录同一账号；is_new 与昵称保持；Web 扫码取微信昵称；再次扫码同账号；state 失效与微信失败不建号；未绑手机号认证 409 | PASS（9） | — | — |
| identity ↔ accounts ↔ residency（US-013） | TC-INT-114~116 | AC-013-01/02/03 | 注销后同号再注册为全新游客；需重新认证；未注销拒绝 | PASS（3） | — | — |
| residency ↔ identity（US-025） | TC-INT-117~118 | AC-025-02/03 | 游客可申请；游客不可审批 / 移除同住人 | PASS（2） | — | — |
| accounts ↔ identity（换号，US-028） | TC-INT-119~121 | AC-028-01/02/04 | 空闲号换绑保留身份；错码不变；旧号不可登录 | PASS（3） | — | — |
| registry ↔ residency（US-035） | TC-INT-122~125 | AC-035-01/02/03/04 | 清册号修改 / 删除后身份保留；按新清册比对；非管理员 403、匿名 401（已收紧） | PASS（4） | — | — |
| committee ↔ polls ↔ audit（US-042） | TC-INT-126~130 | AC-042-01~06 | 赋予业主代表、仅产权业主、人数上限、不可兼任、非管理员 403、匿名 401（已收紧）、审计 | PASS（5） | — | — |
| approval/resolutions/claims/polls ↔ committee（US-068） | TC-INT-131~137 | AC-068-01~07 | 身份失效后在途事项保持；失效审批人被拒；撤回重提；代表到期作答被拒且分母不变；公开决议保留发起人；失效者操作被拒；撤回权限 | PASS（7） | — | — |
| approval ↔ claims/income/resolutions（US-071） | TC-INT-138~143 | AC-071-01~06 | 多审批人任一通过、再审批 409、仅自己在流程中被拒、自批 403、主任自指定可批、非指定不可批 | PASS（6） | — | — |
| accounts ↔ audit（US-073） | TC-INT-144~146 | AC-073-01/02/03 | 重置其他管理员密码；普通用户 403；未登录 401（已收紧）；无自助入口 | PASS（3） | — | — |
| Web 页面 ↔ api/store（HTTP 层 mock） | TC-WEB-017~030 | US-041、049~057、012、014、017 | 首页身份、Claims 表单与核销、PollDetail、Me 手机号/改密/注销 | PASS（14） | — | — |
| Web 登录页 ↔ api/store（US-006） | TC-WEB-031~033 | AC-006-01/02/03/04 | 发码与验证码登录、密码登录、失败提示统一文案与 retry_after | PASS（3） | — | — |
| 小程序页面 ↔ api/store（uni 桩） | TC-MP-014~027 | US-003、012、014、041、045、049~057 | 首页与待办、claims、投票、手机号页、登录 | PASS（14） | — | — |
| 小程序头像昵称设置页（US-070） | TC-MP-028~030 | AC-070-01/03 | 选择头像回填；保存 PATCH /me/profile；失败不跳转、稍后再说；is_new=false 不进设置页 | PASS（3） | — | — |

计数核对：后端 71（既有）+1（TC-INT-073）+2+1+8+5+5+1+4+1 = 99（0.4.0）；0.5.0 新增 6（TC-INT-101~105、107）+1（TC-INT-106，现 PASS）+9+3+2+3+4+5+7+6+3 = 49，合计 148（全部通过）；Web 14 + 3 = 17；小程序 14 + 3 = 17；合计 182（182 通过，0 失败）。契约三条路由用例：Web = TC-INT-082（本次 PASS）、小程序 = TC-INT-083、已知错误路径 = TC-INT-084。

## GR-C-005 condition 核对（本层相关）

| 条件 | 结果 |
|---|---|
| ① AC-059-03/05 两条旧用例更新 | 已更新并通过：`IncomeTests::test_import_row_error_ratio`（201，imported=40、failed=3）、单元 `test_row_error_ratio_over_2_percent`；并新增 `test_import_all_rows_skipped_creates_nothing` |
| ② 前后端契约测试（路由、方法、关键字段） | 已有 `tests/integration/test_frontend_contract.py` 11 个用例；覆盖 identities、claims、polls responses、income sheets、手机号绑定/换绑、登录响应；已发现 DEF-005 |
| ③ Web/小程序 vitest（store、api 路径、页面挂载） | 已有：Web 36、小程序 30，全部通过（0.5.0 含新增 6 个） |
| ④ §9 建议用例 | 合并冲突、核销补差/退款/恰好相等、generate_due 幂等、逐条录入与重复导入、管理员下载附件、缺 SECRET_KEY 拒绝启动均已覆盖 |
| mock 层次 | 仅 http 层（Web `vi.mock('@/shared/http')`；小程序 `uni.request/uploadFile` 桩）；未 mock api.js、store 或页面自身（`git grep "vi.mock\|spyOn" frontend/tests miniprogram/tests` 仅见 http 层） |

## 与基线对比

基线（画像 P4）：后端集成 71/71 通过；本次改动前实跑后端全量 160/160 通过（含 TC-INT-082）。本次既有 71 个用例全部通过，0.4.0 新写的 28 个也全部通过（TC-INT-082 现已 PASS）。0.5.0 新写 49 个后端用例本次全部通过（含 TC-INT-106）。**相对基线新增失败 0 条**。

## 失败汇总（需路由给开发）

无。

## 缺陷状态

| DEF | 状态 | 说明 |
|---|---|---|
| DEF-005 | **CLOSED** | `registryUnit` 已由 GR-C-006 删除；TC-INT-082 本次 PASS（契约三条 11 个用例全部 OK） |
| DEF-006 | **CLOSED** | `verify_code` 已使达到上限的验证码作废（GR-C-007）；TC-INT-106 本次 PASS |
| OBS-001 | **已修复** | `IsAdmin`：匿名 401、已登录普通会员 403；TC-INT-125/130/146 断言收紧为 401 后 PASS |

## 匿名断言收紧（GR-C-007 condition）

`grep -rnE "401.{0,6}403" backend/tests`：收紧前 `test_gap_must_have.py` 438、512（`(None, (401, 403))`）、672、828 与 `test_frontend_contract.py` 320。收紧后匿名请求只接受 401：AC-035-04（TC-INT-125）、AC-042-05（TC-INT-130）、AC-073-03（TC-INT-146，`assertEqual(…, 401)`）；TC-INT-145 无匿名分支（仅登录用户 403），无需改动。第 672 行（AC-068-07，管理员令牌，非匿名）收紧为 403 并通过；`test_frontend_contract.py:320`（管理员令牌访问委员接口，非匿名，实测返回 401）保持 `(401, 403)` 未改——它不属于匿名断言。收紧后 0 失败，说明除 IsAdmin 外无其他路径对匿名返回 403。
