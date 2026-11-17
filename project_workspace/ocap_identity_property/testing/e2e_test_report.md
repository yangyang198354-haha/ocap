<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T22:20:56+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>requirements/user_stories.md（1.0.0）</file>
    <file>architecture/module_design.md（1.0.0）</file>
    <file>development/implementation_plan.md（1.0.0）</file>
    <file>development/code_review_report.md（1.0.0）</file>
    <file>phase_status.md（GR-C-001）</file>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>testing/integration_test_report.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（PHASE_09，ocap_identity_property）

## 摘要

critical path 口径：替代（后端：多步 HTTP API 旅程，真实路由+ORM；Web：vitest+jsdom 挂载真实 App+真实路由+真实页面+真实 api.js，HTTP 层为带状态假服务端；小程序：真实页面脚本/模板编译挂载+真实 api.js，`uni.request` 为带状态假服务端。无浏览器 E2E 框架/微信开发者工具，画像 P4）

- 执行时间：同单元报告（最后一次执行：后端 21:59:46~22:02:20；小程序约 22:03；前端 22:11~22:19）；环境同前两层。
- **total = pass + fail + skip + blocked + not_testable = 94 = 94 + 0 + 0 + 0 + 0**（后端 e2e 66 + smoke 6 = 72；前端 16；小程序 6）；其中本次新写 11（后端 5、前端 4、小程序 2），改写既有 7（后端 5、前端 2）。
- 通过率 = pass/(pass+fail+blocked) = 94/(94+0+0) = **1.00**
- critical path 覆盖率 = 有 E2E 级用例的 Must Have 故事 / Must Have 故事总数 = **10/10 = 1.00**；critical path 通过率 = 本批 Must Have 故事的 E2E 级已执行用例 **全部通过 = 1.00**（US-232/233/234/236/237/238/239/240/241/243 的 E2E 用例：TC-E2E-900~904、910~913、920~921、801〔改〕、802〔改〕、014〔改〕、101〔改〕、102〔改〕、304〔改〕、501〔改〕，共 18 条参与，18 PASS）。
- 前后端契约覆盖：集成层 TC-INT-960~965 + 前端 TC-INT-923/924/925（含新增三函数）+ 既有 `test_frontend_contract.py`/`test_owner_auth_v2_contract.py` 全部通过。
- 判定模式 baseline：基线 E2E 层 83（后端 61 + smoke 6 + 前端 12 + 小程序 4）→ 本次 94 = 83 + 11；零新增失败。前置层（unit、integration）门控均 PASSED。
- **本层门控：PASSED**

## 全量回归

```
$ (cd backend && $PY manage.py test tests.e2e --settings=config.test_settings)
Ran 66 tests in 20.925s
OK
$ (cd backend && $PY manage.py test tests.smoke --settings=config.test_settings)
Ran 6 tests in 0.281s
OK
$ (cd backend && $PY manage.py test --settings=config.test_settings)       # 全量（unit+integration+e2e+smoke）
Ran 1025 tests in 71.723s
OK
$ (cd frontend && npx vitest run --passWithNoTests)
 Test Files  41 passed (41)
      Tests  482 passed (482)
   Duration  254.99s (transform 10.46s, setup 0ms, collect 74.04s, tests 115.67s, environment 44.38s, prepare 6.75s)
$ (cd miniprogram && npx vitest run --passWithNoTests)
Test Files  18 passed (18)
      Tests  135 passed (135)
   Duration  46.39s (transform 2.31s, setup 1.54s, collect 11.11s, tests 8.02s, environment 16.66s, prepare 2.90s)
```

| 范围 | 基线（PM 实跑 HEAD c5ed0ab） | 本次 | 新增用例 | 相对基线新增失败 |
|---|---|---|---|---|
| 后端全量 | 957 OK（203/687/61/6） | 1025 OK（228/725/66/6） | +68 | **0** |
| 前端 vitest | 37 文件 438/438 | 41 文件 482/482 | +44（4 个新 spec 文件） | **0** |
| 小程序 vitest | 16 文件 119/119 | 18 文件 135/135 | +16（2 个新 spec 文件） | **0** |

- 合计 1642 = 1025 + 482 + 135；相对基线新增失败逐条列出：**无**。GROUP_C 登记的 44 条既有失败与 2 个无法加载的前端文件，经改写/删除失效 import 后全部通过（见各层"既有用例改写"，共 51 条改写：后端 16、前端 30、小程序 5）。
- 同一代码状态下还单独运行了 `makemigrations --check --dry-run`（No changes detected）、`manage.py check`（no issues）、`compileall`（exit 0）。
- **GR-C-001 条件 (b)**：前端 TC-E2E-803（文件内 `vi.setConfig({ testTimeout: 60000 })`）与小程序 TC-E2E-202（默认 5000 ms）在多次全量运行中稳定：前端 803 为 3556 ms / 3730 ms（60 s 上限），小程序 202 为 1974 ms / 1782 ms（5 s 上限）；改动前的偶发超时来自 801/802 失败后共享状态未复位与并发，801/802 改写通过后恢复。**未加超时余量**。

## 用户旅程

### TC-E2E-900（后端）: 注册 → 引导列出 → 部分确认 → 房屋明细 → 同住人申请与审批
- 关联：US-239、US-240、US-241、US-232、US-234、US-235 / AC-239-01、AC-240-01/02、AC-241-01/02、AC-232-01、AC-234-01/02、AC-235-01；环境：真实路由 + SQLite 内存库
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 用清册手机号注册（匹配 2 套） | 201；auto_bound=[]；registry_match={pending:true,count:2}；身份为游客 | 同期望 | PASS |
| 2 | GET /me/registry-matches | 2 套，类型为"住宅""公寓"，仅 3 个键 | 同期望 | PASS |
| 3 | POST confirm 仅第 1 套 | 200，succeeded=1/failed=0；Membership 仅 1 套 | 同期望 | PASS |
| 4 | GET /me/housing | 汇总产权业主；单项含 unit_type_label=住宅、area_display=89.50 ㎡、role_label=产权业主 | 同期望 | PASS |
| 5 | 另一用户申请同住人 → 业主 GET to-review 与 pending_review_count | 1 条；角标 1 | 同期望 | PASS |
| 6 | 业主通过 | 同住人出现在房屋名下，pending 0，to-review 空；未勾选的那套无关系 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-901（后端）: 非产权业主看不到待审批且审批被拒；两位产权业主均可审批
- 关联：US-234 / AC-234-04、AC-234-05、REQ-NFUNC-042
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 游客、同住人 GET to-review 与 /me/housing | 空列表、pending_review_count 0 | 同期望 | PASS |
| 2 | 游客、同住人 POST 审批他人申请 | 403 FORBIDDEN | 同期望 | PASS |
| 3 | 业主 1 GET to-review；对 2 号房申请审批 | 仅含自己房的申请；审批 403，状态仍 PENDING，无 Membership | 同期望 | PASS |
| 4 | 同一专有部分第二位业主 GET to-review | 同样可见该申请 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-902（后端）: 产权业主两套房各 1 条待审批
- 关联：US-234、US-235 / AC-234-06、AC-235-01
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 两位申请人分别申请业主的两套房 | 201 ×2 | 同期望 | PASS |
| 2 | 业主 GET to-review 与 /me/housing | 恰 2 条，涉及两套房；pending_review_count=2 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-903（后端）: 微信用户绑定清册手机号 → 选"不是" → 再登录不再引导 → 姓名手动认证
- 关联：US-239、US-241、US-238 / AC-239-05、AC-239-06、AC-241-03
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 微信登录 → 绑定清册手机号 | registry_match={pending:true,count:1} | 同期望 | PASS |
| 2 | POST dismiss | 204；无 Membership；/me/housing units=[] | 同期望 | PASS |
| 3 | 验证码重新登录 → GET registry-matches | pending=false | 同期望 | PASS |
| 4 | POST /certifications（姓名+手机号核对） | 201；汇总身份产权业主（规则不变，C-71） | 同期望 | PASS |
- 结论：PASS

### TC-E2E-904（后端）: 同住人申请规则与可见性
- 关联：US-243 / AC-243-01、AC-243-04、AC-243-05、AC-243-06
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 对无产权业主的专有部分申请 | 409 UNIT_HAS_NO_OWNER | 同期望 | PASS |
| 2 | 产权业主对自己的专有部分申请 | 409 ALREADY_CERTIFIED | 同期望 | PASS |
| 3 | 申请（无姓名字段）→ 重复申请 | 201 PENDING；再次 409 APPLICATION_PENDING | 同期望 | PASS |
| 4 | 我的申请与业主待审批 | 申请者 1 条 PENDING；业主 to-review 含该条 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-910（Web）: 注册 → 引导 → 展开更多/取消 2 套 → 确认 10 套 → 两个地址同页
- 关联：US-232、US-233、US-236、US-239、US-240、US-241 / AC-239-01/10、AC-240-01/02、AC-233-02/05、AC-236-01、AC-232-01；环境：jsdom + 真实 App/路由
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 注册页提交 | 提示"注册成功"（无"自动认证"），自动进入 /units/pick | 同期望 | PASS |
| 2 | 查看引导 | 标题"发现您名下的专有部分"+"认证产权"；先显示 10 套，"展开更多（还有 2 套）"，"已选 12 套"；服务端尚无绑定 | 同期望 | PASS |
| 3 | 展开、取消 2 套、确认 | 共 12 行；"已选 10 套"；confirm 请求只含 10 个 unit_ids；引导消失 | 同期望 | PASS |
| 4 | 展开"我的房屋" | 5 个二级项，无"选择房屋""待我审批" | 同期望 | PASS |
| 5 | 访问 /me/identity 与 /units | 地址不变；标题"我的身份与房屋"+底部"待我审批的同住人申请"；10 行含车位类型与面积；仅"我的身份与房屋"二级项高亮 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-911（Web）: 选"不是"后不再强制弹出
- 关联：US-237、US-239、US-241 / AC-239-06、AC-241-03、AC-237-02/05
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 注册进入引导（1 套） | 询问文案含坐落与类型 | 同期望 | PASS |
| 2 | 点"不是" | dismiss 调用 1 次；无绑定；引导消失 | 同期望 | PASS |
| 3 | 进入 /units | 提醒"您还没有认证任何专有部分…"；0 行；无待审批卡 | 同期望 | PASS |
| 4 | 再进 /units/pick；回主页 | 无引导；主页"去认证产权"链接→/units/pick | 同期望 | PASS |
- 结论：PASS

### TC-E2E-912（Web）: 游客：提醒 → 认证产权页 → 同住人申请页发起申请
- 关联：US-236、US-237、US-238、US-243 / AC-237-02、AC-236-02、AC-238-01/02、AC-243-01
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | /me/identity 点提醒内"认证产权" | 进入 /units/pick，标题"认证产权" | 同期望 | PASS |
| 2 | 查看认证产权页 | 本人姓名框与占位；无"申请成为同住人"按钮 | 同期望 | PASS |
| 3 | 点提示链接 | 进入 /units/applications，标题"我的同住人申请" | 同期望 | PASS |
| 4 | 选房 → 申请 | POST /resident-applications 请求体仅 {unit_id}；列表出现该专有部分与"待审批" | 同期望 | PASS |
- 结论：PASS

### TC-E2E-913（Web）: 待审批：产权业主在身份页底部处理；同住人看不到
- 关联：US-234、US-235 / AC-234-01/02/04、AC-235-01/02/03/04
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 业主主页 | 链接"待审批同住人申请：1"→/units#review | 同期望 | PASS |
| 2 | 展开我的房屋 | "我的身份与房屋"二级项角标 1 | 同期望 | PASS |
| 3 | 访问 /units/review | 到达 /units；页面含身份卡+底部待审批卡 | 同期望 | PASS |
| 4 | 点通过 | 请求 decision APPROVE；卡片显示暂无；角标消失 | 同期望 | PASS |
| 5 | 换同住人账号访问 /units/review | 到达 /units，无待审批卡；主页无链接；菜单无角标 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-920（小程序）: 微信用户绑定手机号 → 跳转我的房屋 → 引导 → 确认
- 关联：US-239、US-240、US-242 / AC-242-04、AC-239-10、AC-240-01/02
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 绑定手机号页提交 | navigateTo /pages/units/index；无"自动认证"提示；服务端无绑定 | 同期望 | PASS |
| 2 | 我的房屋页 | 引导卡片置顶；提醒仍在；先 10 套+"展开更多（还有 2 套）" | 同期望 | PASS |
| 3 | 展开、取消 2 套、确认 | "已选 10 套"；confirm 请求含 10 个 unit_ids；引导消失、提醒消失 | 同期望 | PASS |
| 4 | 查看页面 | 汇总身份产权业主；明细含类型与面积；底部待审批卡 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-921（小程序）: 选"不是"后不再弹出
- 关联：US-239、US-242 / AC-239-06、AC-242-04
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 打开我的房屋页 | 引导卡片与询问文案 | 同期望 | PASS |
| 2 | 点"不是" | dismiss 1 次；无绑定；卡片消失；提醒仍在 | 同期望 | PASS |
| 3 | 再次进入页面（新实例） | 无引导卡片；无 confirm 请求；认证产权卡片可用 | 同期望 | PASS |
- 结论：PASS

### 既有 E2E 改写（GR-C-001 条件 (a)）

| TC | 文件 | AC | 旧断言 → 新断言 | 结果 |
|---|---|---|---|---|
| TC-E2E-014 | backend/tests/e2e/test_gap_journeys.py | AC-241-01 | 注册即 auto_bound==[unit] 并为产权业主 → 注册后 auto_bound==[]、pending、身份非产权业主；confirm 后为产权业主，后续换号/注销/再注册流程不变 | PASS |
| TC-E2E-501 | backend/tests/e2e/test_identity_display_journey.py | AC-241-01 | 注册后身份即"产权业主"并见单元详情 → 注册后身份"游客"；confirm 后"产权业主"并含类型/面积单元详情 | PASS |
| TC-E2E-101 | backend/tests/e2e/test_registry_import_journeys.py | AC-239-01、AC-240-01 | 业主注册后即为 HEAD/OWNER，再逐级选车位 → 注册后 registry_matches 列出该套、无 Membership；confirm 后 HEAD/OWNER；再逐级选车位 | PASS |
| TC-E2E-102 | backend/tests/e2e/test_registry_import_journeys.py | AC-241-01 | 注册即 HEAD，再重复导入保留认证 → 注册后无 Membership，confirm 后 HEAD，再验证重复导入后认证保留 | PASS |
| TC-E2E-304 | backend/tests/e2e/test_registry_import_scale_journeys.py | AC-239-01 | XLSX 导入后注册即 HEAD/REGISTRY → 注册后无 Membership，confirm 后 HEAD/REGISTRY | PASS |
| TC-E2E-801 | frontend/tests/layout_e2e.spec.js | AC-233-01、AC-235-01/03、AC-236-01 | 二级 6 项；点"待我审批"进 /units/review；角标在其上；右上角"我的身份"；/units#review→/units/review → 二级 5 项；点"我的身份与房屋"进 /units，页面含身份卡+底部待审批卡，角标 2→1 在该项；右上角"我的身份与房屋"；/units#review 与 /units/review 都到 /units，/me/identity 同页 | PASS |
| TC-E2E-802 | frontend/tests/layout_e2e.spec.js | AC-236-04 | 窄屏切换条 6 项 → 5 项且无"选择房屋" | PASS |

### critical path：Must Have 故事 → E2E 级已执行用例

| Must Have US | E2E 级用例 | 结果 |
|---|---|---|
| US-232 | TC-E2E-900、TC-E2E-910、TC-E2E-501〔改〕 | PASS |
| US-233 | TC-E2E-910、TC-E2E-801〔改〕 | PASS |
| US-234 | TC-E2E-901、TC-E2E-902、TC-E2E-913、TC-E2E-801〔改〕 | PASS |
| US-236 | TC-E2E-910、TC-E2E-912、TC-E2E-802〔改〕 | PASS |
| US-237 | TC-E2E-911、TC-E2E-912 | PASS |
| US-238 | TC-E2E-903、TC-E2E-912 | PASS |
| US-239 | TC-E2E-900、TC-E2E-903、TC-E2E-910、TC-E2E-911、TC-E2E-920、TC-E2E-921、TC-E2E-101〔改〕、TC-E2E-304〔改〕 | PASS |
| US-240 | TC-E2E-900、TC-E2E-910、TC-E2E-920 | PASS |
| US-241 | TC-E2E-900、TC-E2E-903、TC-E2E-911、TC-E2E-014〔改〕、TC-E2E-102〔改〕、TC-E2E-501〔改〕 | PASS |
| US-243 | TC-E2E-904、TC-E2E-912 | PASS |

## 变异验证（用例能抓住缺陷的证据，M-TE-012 做法）

在 scratchpad 副本（不改仓库产品代码）上回退被测几行后运行新用例，均如期失败：

| 变异 | 位置 | 被抓住的用例 |
|---|---|---|
| 确认接口不再整批拒绝越权 unit_id，改为静默忽略 | backend phone_match.py 子集校验 | TC-INT-945、946、954；TC-UNIT-907、912、913（6 条 FAIL） |
| 折叠阈值 10 → 12；身份页待审批卡去掉产权业主判定；"认证产权"菜单改回"选择房屋" | frontend RegistryMatchPanel.vue、UnitsIdentity.vue、menus.js | TC-WEB-922/923/912/915、TC-E2E-910/911/913、TC-UNIT-931（8 条 FAIL） |
| 小程序折叠阈值 10 → 11；待审批卡去掉产权业主判定；合并也跳转（客户端守卫） | miniprogram RegistryMatchCard.vue、pages/units、pages/phone | TC-MP-903/908/911、TC-E2E-920（合并守卫变异首次未被发现，已把 TC-MP-908 的合并响应改为误带 pending=true 后复验：FAIL，可抓） |
| Web 绑定手机号页合并也跳转（客户端守卫） | frontend MePhone.vue | TC-WEB-932（同样已加强为合并响应误带 pending=true 后复验：FAIL，可抓；另含阈值变异下的 TC-WEB-922/923） |

## 缺陷

无产品缺陷（DEF 数 0）。

观察项（不构成 AC 不满足，仅供 PM/开发知悉）：
1. CR-003（MINOR，OPEN）：小程序 `RegistryMatchCard` 仅在挂载时拉取，`pages/units/index.vue` 的 `onShow` 不调用其 `load`；从手机号页 `navigateTo` 进入是新实例，AC-242-04 满足（TC-MP-907/TC-E2E-920）。页面已在栈中再次显示时不会刷新卡片，用户故事未要求，未写失败用例。
2. 手动认证成功提示沿用 `ROLE_LABELS`，对 HEAD 显示"认证成功，身份：户主"（`UnitsPick.vue`，既有行为，TC-UNIT-524 旧断言保留）；与 C-75"用户端不显示户主"存在张力，但属本批之前的既有提示，且本批新增的引导确认提示（TC-WEB-926、TC-MP-913）已用"产权业主"。建议下批需求确认是否统一。
3. CR-001（所选全部失败时状态仍置 DONE，之后只能手动认证）、CR-002（GET 每次查清册）：按设计，未写缺陷用例。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-242-01~06、TC-MP-*、TC-E2E-920/921 | 在微信开发者工具构建并上传体验版；用微信账号登录 → 绑定匹配清册的手机号 → 观察是否跳转"我的房屋"并出现引导卡片 → 折叠/展开、取消勾选、确认/"不是" | 与 TC-E2E-920/921 一致；`uni.navigateTo` 真实栈行为正常；页面样式在三套风格下无错位 | 微信开发者工具 + 真机/体验版；测试环境短信为 console 替身 | 是（US-242 为 Should Have，非 Must Have critical path；US-239/240 小程序端体验） |
| MV-02 | AC-235-02、TC-WEB-915 | 产权业主有待审批时，主页点"待审批同住人申请：N" | 进入"我的身份与房屋"页，底部"待我审批的同住人申请"卡片滚动进入可视区域 | 真实浏览器（宽屏与窄屏） | 否 |
| MV-03 | AC-233-02/05、AC-236-04、TC-INT-971 | 宽屏：右上角"我的身份与房屋"与左侧二级项各点一次；浏览器后退；窄屏查看切换条与"我的"总览 | 地址栏分别为 /me/identity、/units，页面一致，后退一次回到点击前页面；左侧高亮正确；窄屏切换条 5 项 | 真实浏览器 + 真实视口 | 是（US-233） |
| MV-04 | `residency 0004_phone_match_prompt`（module_design 数据迁移） | 部署阶段（E2，经用户授权）在测试环境 MySQL 执行 `migrate`，再 `migrate residency 0003` 回退一次并重迁 | 创建/删除 PhoneMatchPrompt 表成功，无其他表变化；注册匹配手机号后出现引导 | 测试机（仅 E2 部署阶段，P7/P8；本阶段测试不得连接） | 否 |

以上 4 项均为"AC 的部分不可测"，对应 AC 的自动化部分已真实执行并通过（见 test_plan"不可测项"）；用例层面 not_testable = 0。
