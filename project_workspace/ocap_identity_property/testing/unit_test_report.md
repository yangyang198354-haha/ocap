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
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（PHASE_07，ocap_identity_property）

## 摘要

- 执行时间（最后一次执行，均晚于对应测试文件的最后一次修改）：后端各层 2026-11-17T21:59:46~22:02:20+08:00（后端测试文件最后修改 21:59:38）；小程序 22:03 前后（小程序测试文件最后修改 21:59:38）；前端 22:11:11（JSON 报告）与 22:15:17~22:19:32（默认报告，上表输出）（前端测试文件最后修改 22:10:58）。
- 环境：本机 Python 3.12 + Django 5.2.19（PM 的 scratchpad venv）、`config.test_settings`（SQLite 内存库、MIGRATION_MODULES 置空、外部服务经 `apps/integrations/fakes.py`）；前端 vitest（jsdom）；小程序 vitest（`uni` 桩）。不使用 `--parallel`。未连接测试机/生产库，未调用任何真实外部服务。
- 命令：
  - `(cd backend && $PY manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run --passWithNoTests)`（前端不分目录，按用例 ID 前缀归层：TC-UNIT/TC-WEB/无编号主题用例 → unit）
  - `(cd miniprogram && npx vitest run --passWithNoTests)`（TC-MP/TC-UNIT/无编号 → unit）
- **total = pass + fail + skip + blocked + not_testable = 692 = 692 + 0 + 0 + 0 + 0**（后端 228 + 前端 345 + 小程序 119）
- 通过率 = pass/(pass+fail+blocked) = 692/(692+0+0) = **1.00**
- 判定模式：baseline（INCREMENTAL）：相对基线零新增失败且新写用例全部通过。基线 unit 层 618（后端 203 + 前端 310 + 小程序 105）；本次 692 = 618 + 新写 74（后端 25、前端 35、小程序 14），改写既有 18 条，新增失败 0。
- **本层门控：PASSED**

## 执行输出

```
$ (cd backend && $PY manage.py test tests.unit --settings=config.test_settings)
Ran 228 tests in 1.736s
OK

$ (cd frontend && npx vitest run --passWithNoTests)      # 全部 482 条（unit 层 345 / integration 121 / e2e 16）
 Test Files  41 passed (41)
      Tests  482 passed (482)
   Duration  254.99s (transform 10.46s, setup 0ms, collect 74.04s, tests 115.67s, environment 44.38s, prepare 6.75s)

$ (cd miniprogram && npx vitest run --passWithNoTests)    # 全部 135 条（unit 层 119 / integration 10 / e2e 6）
Test Files  18 passed (18)
      Tests  135 passed (135)
   Duration  46.39s (transform 2.31s, setup 1.54s, collect 11.11s, tests 8.02s, environment 16.66s, prepare 2.90s)
```

按用例 ID 前缀归层（来自 vitest JSON 报告，`--reporter=json`，同一次代码状态）：前端 UNIT 229 + WEB 72 + 无编号 44 = 345；小程序 MP 55 + UNIT 51 + 无编号 13 = 119；全部 passed，failed 0。

## 分项结果

### 后端：MOD-132 清册匹配引导服务 / MOD-134 展示口径（backend/tests/unit/test_phone_match_service.py，25 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-900 | AC-232-01 | 类型与面积格式化口径（住宅 + 两位小数 + ㎡）。 | PASS | — | — |
| TC-UNIT-901 | AC-232-02 | 类型或面积未登记显示 | PASS | — | — |
| TC-UNIT-902 | AC-239-01 | 手机号匹配 2 套 → 返回 2，建 PENDING，用户此时无 Membership（AC-241-01）。 | PASS | — | — |
| TC-UNIT-903 | AC-239-03 | 无匹配返回 0 且不建行；已有 DISMISSED 行不被改动。 | PASS | — | — |
| TC-UNIT-904 | AC-239-04 | 已是产权业主的专有部分不计入；全部已绑定 → 0 不建行。 | PASS | — | — |
| TC-UNIT-905 | AC-239-05 | 再次触发（n>0）把 DISMISSED/EXPIRED 重置为 PENDING 且 resolved_at 清空。 | PASS | — | — |
| TC-UNIT-906 | AC-239-01（不得影响注册主流程） | 内部异常被吞掉，返回 0。 | PASS | — | — |
| TC-UNIT-907 | AC-239-08 | 无手机号用户：open_prompt=0、pending_matches=[]、confirm 拒绝。 | PASS | — | — |
| TC-UNIT-908 | AC-239-01、AC-239-07 | 自然顺序（9 < 10），只含 unit_id/坐落/类型（未登记）。 | PASS | — | — |
| TC-UNIT-909 | AC-239-06、AC-239-09 | 状态非 PENDING 时即使清册匹配也返回 []。 | PASS | — | — |
| TC-UNIT-910 | AC-240-01、AC-240-02 | 确认 → 各套 HEAD，状态 DONE，resolved_at 有值。 | PASS | — | — |
| TC-UNIT-911 | AC-240-02 | 只确认勾选的 2 套，第 3 套无关系。 | PASS | — | — |
| TC-UNIT-912 | AC-240-06、REQ-NFUNC-043 | 含手机号未登记的专有部分 → 整批 422 OWNER_NOT_MATCHED，无 Membership，状态仍 PENDING。 | PASS | — | — |
| TC-UNIT-913 | AC-240-06 | 不存在的 unit_id 与越权同一出口 422。 | PASS | — | — |
| TC-UNIT-914 | AC-239-06、AC-239-09 | 无行 / DISMISSED / DONE / EXPIRED 均 409 MATCH_NOT_PENDING。 | PASS | — | — |
| TC-UNIT-915 | AC-240-04 | 已是产权业主的一套返回 ALREADY_CERTIFIED，不重复绑定，其余成功。 | PASS | — | — |
| TC-UNIT-916 | AC-240-04 | 单套抛异常 → code=FAILED，其余套仍成功。 | PASS | — | — |
| TC-UNIT-917 | AC-240-05 | 审计 origin_label=清册自动绑定，phone_masked 脱敏，明文手机号/姓名不入审计。 | PASS | — | — |
| TC-UNIT-918 | AC-240-05 | 先到先得——已有户主时后确认者为 OWNER，单元 HEAD 仅 1。 | PASS | — | — |
| TC-UNIT-919 | AC-240-05 | 同住人确认后升级为产权业主（原 RESIDENT 以 UPGRADED 结束）。 | PASS | — | — |
| TC-UNIT-920 | AC-239-06 | PENDING → DISMISSED 且 resolved_at；无行或非 PENDING 为空操作。 | PASS | — | — |
| TC-UNIT-921 | AC-239-05、AC-239-12 | expire 仅改 PENDING → EXPIRED；DONE/DISMISSED 不变。 | PASS | — | — |
| TC-UNIT-922 | REQ-NFUNC-044 | certify_owner 不传 detail_extra 时审计 detail 不含 phone_masked（旧调用不变）。 | PASS | — | — |
| TC-UNIT-923 | AC-240-04 | certify_one 已认证返回 (None, ALREADY_CERTIFIED)，成功返回 (role, None)。 | PASS | — | — |
| TC-UNIT-924 | REQ-NFUNC-044（ADR-130） | AutoBindService.bind_by_phone 保留且行为不变（直接调用仍绑定）。 | PASS | — | — |

### 前端：菜单（MOD-135，frontend/tests/identity_property_menu_router.spec.js，4 条新写 unit）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-930 | AC-233-05 | /me/identity 与 /units 都使"我的房屋"展开、仅二级项"我的身份与房屋"高亮（Q-IP-16=A） | PASS | — | — |
| TC-UNIT-931 | AC-236-01、AC-233-01、REQ-NFUNC-045 | 菜单文案残留数为 0——无"选择房屋""待我审批的同住人申请"二级项，无恰为"我的身份"的项 | PASS | — | — |
| TC-UNIT-932 | AC-233-02 | 右上角项与左侧二级项同名，两个入口地址不同（/me/identity、/units）、均保留 | PASS | — | — |
| TC-UNIT-933 | AC-235-01、AC-234-04 | 仅"我的身份与房屋"二级项带 pendingReview 角标；对所有受众可见（游客与非产权业主也看得到菜单，卡片由页面控制） | PASS | — | — |

### 前端：身份与房屋页、引导面板、认证产权、同住人申请（MOD-136/137，页面级，31 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-WEB-901 | AC-232-01 | 2 套房——汇总身份 + 恰 2 行，每行含名称/类型/面积/关系；产权业主行含同住人名单与"移除"，同住人行含"退出" | PASS | — | — |
| TC-WEB-902 | AC-232-02 | 类型或面积未登记显示"未登记"，不显示 null/0/空白 | PASS | — | — |
| TC-WEB-903 | AC-232-03、AC-237-02 | 无有效关系——"暂无已认证房屋"、行数 0，并显示提醒与"认证产权"入口，点击进入认证产权页 | PASS | — | — |
| TC-WEB-904 | AC-232-05 | 房屋接口失败——"加载失败，请重试"+重试，不显示"暂无已认证房屋"/提醒/游客；重试成功后恢复明细 | PASS | — | — |
| TC-WEB-905 | AC-237-01、AC-237-03 | 已有房屋时不显示提醒，"认证产权"按钮仍显示且进入认证产权页 | PASS | — | — |
| TC-WEB-906 | AC-237-04 | 仅有 1 条待审批的同住人申请、无有效关系——仍显示提醒（以有效关系数判定） | PASS | — | — |
| TC-WEB-907 | AC-232-04、AC-237-05 | 主页只保留"认证房屋"数量小卡片（2），无逐套明细；游客空状态显示"去认证产权"；快捷入口"认证我的房屋"指向 /units/pick | PASS | — | — |
| TC-WEB-910 | AC-234-01、AC-234-02 | 产权业主——页面最后一个卡片为"待我审批的同住人申请"，含 1 行与通过/拒绝；通过后提示"已处理"，行消失并显示"暂无待审批的同住人申请" | PASS | — | — |
| TC-WEB-911 | AC-234-03 | 产权业主但无待审批——底部卡片仍显示，内容"暂无待审批的同住人申请" | PASS | — | — |
| TC-WEB-912 | AC-234-04、REQ-NFUNC-042 | 游客与仅同住人——页面上没有该卡片（不是空卡片），且不请求审批列表 | PASS | — | — |
| TC-WEB-913 | AC-234-06 | 2 个专有部分各 1 条待审批——卡片列出恰 2 行，分别对应两个专有部分 | PASS | — | — |
| TC-WEB-914 | AC-234-05 | 审批接口 403 时前端提示服务端文案且列表不被清空（权限由后端把关，界面不做乐观更新） | PASS | — | — |
| TC-WEB-915 | AC-235-03（定位） | 访问 /units#review 的产权业主——数据加载后卡片被滚动到可视区；非产权业主无该卡片也不报错 | PASS | — | — |
| TC-WEB-916 | AC-235-02、AC-235-04 | 主页"待审批同住人申请：2"链接指向 /units#review；游客与同住人不显示该链接 | PASS | — | — |
| TC-WEB-920 | AC-239-01、AC-239-07 | 1 套——询问文案含坐落与类型；两个按钮"是，确认认证""不是"；不渲染接口多给的姓名/手机号 | PASS | — | — |
| TC-WEB-921 | AC-239-03、AC-239-08 | pending=false 或接口失败——面板不渲染、不抛错 | PASS | — | — |
| TC-WEB-922 | AC-239-10 | 12 套——先显示 10 套 +"展开更多（还有 2 套）"，默认全选"已选 12 套"，展开后 12 套全显示且按钮消失 | PASS | — | — |
| TC-WEB-923 | AC-239-11 | 恰 10 套不折叠（无"展开更多"）；11 套折叠 1 套；1 套为单句，2 套为列表 | PASS | — | — |
| TC-WEB-924 | AC-240-02 | 3 套取消勾选第 3 套——"已选 2 套"，确认只提交 2 个 unit_ids（请求体只含 unit_ids，无姓名/手机号） | PASS | — | — |
| TC-WEB-925 | AC-240-03 | 取消勾选全部——"是，确认认证"禁用，点击不发请求 | PASS | — | — |
| TC-WEB-926 | AC-240-01、AC-241-02 | 单套确认成功——提示"认证成功，身份：产权业主"，刷新 /me 与房屋数据，面板消失并 emit resolved | PASS | — | — |
| TC-WEB-927 | AC-240-04 | 部分成功——警告"成功 1 套，未成功 1 套"，不弹错误；多套全成功提示"认证成功，共认证 N 套" | PASS | — | — |
| TC-WEB-928 | AC-239-06 | 点"不是"——只 POST dismiss，不发 confirm，不绑定；面板关闭并 emit resolved | PASS | — | — |
| TC-WEB-929 | AC-240-06 | 确认被服务端拒绝（422）——提示服务端文案，面板保留可再次操作，按钮恢复可点 | PASS | — | — |
| TC-WEB-930 | AC-239-01、AC-241-01 | 注册返回 registry_match.pending → 提示"注册成功"并进入 /units/pick；不再出现"自动认证"提示 | PASS | — | — |
| TC-WEB-931 | AC-239-03 | 注册无匹配（pending=false 或缺字段）→ 直接进入主页 / | PASS | — | — |
| TC-WEB-932 | AC-239-05、AC-239-12 | 首次绑定手机号匹配 → 进入 /units/pick；合并（merged=true）或无匹配 → 不跳转；换号不跳转 | PASS | — | — |
| TC-WEB-940 | AC-236-02、AC-238-01、AC-238-02 | 认证产权页——标题"认证产权"、姓名标签/占位为本人姓名、无"申请成为同住人"按钮、无"户主"、含指向 /units/applications 的提示链接 | PASS | — | — |
| TC-WEB-941 | AC-238-03、AC-238-04 | 姓名全空格——提示"请输入姓名"不发请求；OWNER_NOT_MATCHED——转申诉页并带入姓名，不显示清册信息 | PASS | — | — |
| TC-WEB-942 | AC-243-01、AC-243-02、AC-243-03 | 我的同住人申请页——标题不变，上方发起区含说明与按钮、无姓名框；未选房屋按钮禁用；选定后提交只含 {unit_id}，成功提示并刷新列表 | PASS | — | — |
| TC-WEB-943 | AC-243-04、AC-243-05、AC-243-06 | 后端 409 三种拒绝（无产权业主 / 已是产权业主 / 已有待审）——提示后端文案，列表行数不变 | PASS | — | — |

### 小程序：我的房屋页、首页、绑定手机号页、引导卡片（MOD-138，14 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-MP-901 | AC-242-01 | 已有 1 套住宅（产权业主）+ 1 套公寓（同住人）——汇总身份 + 2 行，含名称/类型/面积（未登记）/关系；同住人名单与"移除"、"退出" | PASS | — | — |
| TC-MP-902 | AC-242-03、AC-237-02、AC-237-03 | 无任何有效房屋——提醒"您还没有认证任何专有部分，请先认证产权"；有房屋则不显示提醒；"认证产权"按钮始终在 | PASS | — | — |
| TC-MP-903 | AC-242-02、AC-234-04、AC-234-01、AC-234-03 | 游客与仅同住人无"待我审批"卡片；产权业主在页面底部看到并可通过 | PASS | — | — |
| TC-MP-904 | AC-242-03、AC-236-02、AC-238-01 | 卡片标题"认证产权"、姓名占位为本人姓名；无"申请成为同住人"出现在认证产权卡片；无"选择房屋""户主"文案 | PASS | — | — |
| TC-MP-905 | AC-242-06、AC-243-01、AC-243-03 | 未选房号点"申请成为同住人"提示"请先选择房号"不发请求；选定后只提交 {unit_id}，提示并出现在申请列表 | PASS | — | — |
| TC-MP-906 | AC-232-04 | 首页游客显示"共 0 套"与"去认证产权"空状态；"待审批同住人申请"链接指向我的房屋页 review 定位；游客无该链接 | PASS | — | — |
| TC-MP-907 | AC-242-04、AC-241-01 | 绑定成功且 registry_match.pending → 跳转"我的房屋"页；不再提示"已绑定并按清册自动认证 N 个专有部分" | PASS | — | — |
| TC-MP-908 | AC-242-04、AC-239-12 | 无匹配或账号合并——不跳转、不引导 | PASS | — | — |
| TC-MP-909 | AC-242-04、AC-242-05、AC-239-07 | 1 套——询问文案、两个按钮、已选 1 套；不渲染接口多给的姓名/手机号；无需输入姓名 | PASS | — | — |
| TC-MP-910 | AC-239-03 | pending=false 或接口失败——卡片不渲染 | PASS | — | — |
| TC-MP-911 | AC-239-10、AC-239-11 | 12 套折叠 10 + "展开更多（还有 2 套）"，默认全选"已选 12 套"，展开后 12 套；恰 10 套不折叠 | PASS | — | — |
| TC-MP-912 | AC-240-02、AC-240-03 | 取消勾选 1 套——已选 2 套，确认只提交 2 个 unit_ids；全部取消后确认按钮禁用且不发请求 | PASS | — | — |
| TC-MP-913 | AC-240-01、AC-240-04 | 单套确认成功提示"认证成功，身份：产权业主"；部分失败提示"成功 1 套，未成功 1 套" | PASS | — | — |
| TC-MP-914 | AC-239-06 | 点"不是"——只调用 dismiss，不发 confirm，卡片关闭并 emit resolved | PASS | — | — |

## 既有用例改写（GR-C-001 条件 (a)，unit 层；不删除用例、不改空断言）

| TC | 文件 | AC | 旧断言 → 新断言 | 结果 |
|---|---|---|---|---|
| TC-WEB-501 | frontend/tests/identity_display.spec.js | AC-232-04 | 主页含"共 2 套"与逐套名称/类型/面积/关系 → 主页只有小卡片数字 2，点击进 /units；不含"共 2 套"与任何明细；明细断言迁至 TC-WEB-901 | PASS |
| TC-WEB-502 | frontend/tests/identity_display.spec.js | AC-237-05 | 游客主页"共 0 套"+"暂无已认证房屋" → 小卡片数字 0 + "去认证产权"链接指向 /units/pick | PASS |
| TC-WEB-503 | frontend/tests/identity_display.spec.js | AC-232-04 | 加载中"共 — 套" → 小卡片数值"—"，不显示 0 与"去认证产权" | PASS |
| TC-UNIT-804 | frontend/tests/layout_menus.spec.js | AC-236-01 | 我的房屋二级项 6 项（含"待我审批的同住人申请""选择房屋"） → 5 项：我的身份与房屋、认证产权、认证申诉、我的同住人申请、我的申诉；不含两个旧名 | PASS |
| TC-UNIT-805 | frontend/tests/layout_menus.spec.js | AC-233-01 | 个人中心第 2 项"我的身份" → 第 2 项"我的身份与房屋"，地址仍 /me/identity | PASS |
| TC-UNIT-806 | frontend/tests/layout_menus.spec.js | AC-235-01 | 仅"待我审批的同住人申请"带 pendingReview 角标键 → 仅"我的身份与房屋"带 pendingReview | PASS |
| TC-UNIT-807 | frontend/tests/layout_menus.spec.js | AC-235-03 | LEGACY_UNITS_HASH={#review:/units/review,#appeal:/units/appeal} → 仅 {#appeal:/units/appeal} | PASS |
| TC-UNIT-667 | frontend/tests/owner_auth_v2.spec.js | AC-238-01、AC-238-03 | 按占位"请输入姓名"取输入框 → 按占位"请输入您本人的姓名（须与业主清册登记的姓名一致）"取；"请输入姓名"仍是为空时的提示 | PASS |
| TC-UNIT-668 | frontend/tests/owner_auth_v2.spec.js | AC-238-01 | 同上 → 同上；提交仍为 {unit_id,name(去空格)} | PASS |
| TC-UNIT-669 | frontend/tests/owner_auth_v2.spec.js | AC-238-01、AC-238-04 | 同上 → 同上；OWNER_NOT_MATCHED 转申诉页行为不变 | PASS |
| TC-UNIT-523 | frontend/tests/product_review_ui.spec.js | AC-243-01、AC-236-02 | 在 UnitsPick 点"申请成为同住人"提交 {unit_id} → UnitsPick 无该按钮；在 UnitsApplications 选房点"申请成为同住人"，提交 {unit_id} 并提示 | PASS |
| TC-UNIT-524 | frontend/tests/product_review_ui.spec.js | AC-238-01 | 按占位"请输入姓名"取输入框 → 按新占位取 | PASS |
| TC-UNIT-530 | frontend/tests/product_review_ui.spec.js | AC-232-01 | MeIdentity 身份卡零按钮、列出汇总身份与户主房屋 → UnitsIdentity 身份卡：汇总身份、名称、类型、面积；无 input/select；按钮仅"认证产权"；夹具补 residents | PASS |
| TC-MP-501 | miniprogram/tests/identity_display.spec.js | AC-242-01 | 首页逐套显示名称/类型/面积/关系 → 首页只含"共 2 套"，明细均不在首页，点击卡片 navigateTo /pages/units/index；明细断言迁至 TC-MP-901 | PASS |
| TC-MP-504 | miniprogram/tests/owner_auth_v2.spec.js | AC-238-01、AC-238-03 | 按占位"请输入姓名"取框；按钮 byText('认证') → 按新占位取框；认证按钮改为文本恰为"认证"（页面新增"认证产权"按钮） | PASS |
| TC-MP-505 | miniprogram/tests/owner_auth_v2.spec.js | AC-238-01 | 同上 → 同上 | PASS |
| TC-MP-506 | miniprogram/tests/owner_auth_v2.spec.js | AC-238-01、AC-238-04 | 同上 → 同上 | PASS |
| TC-UNIT-551 | miniprogram/tests/product_review_ui.spec.js | AC-242-06、AC-243-01 | 唯一 UnitPicker；占位列表 ['请输入姓名','产权人名字'] → 占位 ['请输入您本人的姓名（…）','产权人名字']；2 个 UnitPicker，第 2 个属同住人发起区 | PASS |

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 说明 |
|---|---|---|---|
| unit 层用例总数 | 618（203 + 310 + 105） | 692 | +74 新写，全部 PASS |
| unit 层失败 | 0 | 0 | 无既有失败、无新增失败 |
| GROUP_C 报告的"预期失败" unit 层条目 | 18 条（后端 0、前端 TC-UNIT-804~807/667~669、TC-WEB-501~503、TC-UNIT-523/524/530，小程序 TC-MP-501/504~506、TC-UNIT-551） | 全部改写后通过 | 逐条依据见上表（旧→新断言、AC） |

失败清单：无。既有失败：无（画像 P4 已声明的既有失败 test_tc_int_311 已不复现，本次也未出现）。

## 失败汇总（需路由给开发）

无。
