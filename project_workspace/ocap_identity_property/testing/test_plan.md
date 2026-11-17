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
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：我的身份与房屋整合、认证产权入口与手机号匹配引导认证（ocap_identity_property，INCREMENTAL，GROUP_D）

## 测试策略

- **被测改动**：MOD-132~138（后端 `PhoneMatchService` 与 3 个 registry-matches 接口、注册/绑定手机号入口改造、`/me/housing` 增 `unit_type_label`/`area_display`；Web 菜单/路由/身份页/认证产权/同住人申请/引导面板；小程序同步）。代码评审 CR-001~003 均为 MINOR 且 OPEN，无 CRITICAL/MAJOR。
- **范围 in-scope**：US-232~243 全部 67 个 AC 的可自动化部分；GR-C-001 条件 (a) 既有用例改写；条件 (b) 两条易超时用例的稳定性确认；前后端契约（Web `api.js`、小程序 `api.js` 的 3 个新增 registry-matches 调用）。
- **out-of-scope / 人工**：微信开发者工具构建与真机、真实浏览器视口与滚动可视、MySQL 上执行迁移 0004（P8 禁止连接测试机数据库）、短信/微信手机号快速验证真实调用（P11-3 禁止）。见"不可测项"与 e2e_test_report 人工验证清单。
- **环境**：后端 Python 3.12 + Django 5.2.19（PM 的 venv，仅 `backend/requirements.txt` 依赖）、`config.test_settings`（SQLite 内存库，`MIGRATION_MODULES` 置空）、外部服务经 `apps/integrations/fakes.py`；前端 vitest + jsdom；小程序 vitest（`uni` 为桩）。不使用 `--parallel`。无硬件，P11-1/P11-2 为"无"，运行方式列均为 sim（纯软件，不涉及 hil/manual）。
- **判定模式**：baseline（INCREMENTAL）：每层相对基线零新增失败，新写用例全部通过；critical path = Must Have 故事的 E2E 用例，通过率须 1.00。
- **基线来源**：PM 实跑（HEAD c5ed0ab）：后端 Ran 957 OK（unit 203 / integration 687 / e2e 61 / smoke 6）；前端 37 文件 438/438；小程序 16 文件 119/119。GROUP_C 在改动后实跑 44 条既有用例失败（后端 16、前端 21+2 个无法加载文件、小程序 5+1 条抖动），均对应 implementation_plan"预期失败的既有用例"表，本批已逐条改写（见下"既有用例改写清单"），改写后全部通过，**零新增失败**。
- **分层机制**（P4 无标签机制，按目录与用例 ID 约定）：后端 `tests/unit|integration|e2e|smoke/`；前端/小程序 vitest 无目录分层，按用例 ID 前缀分层：`TC-UNIT`/`TC-WEB`/`TC-MP`（单模块或页面级，仅 mock HTTP 层）计入 unit 层；`TC-INT` 计入 integration；`TC-E2E` 计入 e2e；无编号的既有主题/UI 块用例（theme/ui_blocks 等）计入 unit。同一 AC 的分类在各处一致。
- **先映射后新写**：先 `git grep` 既有用例（identity_display、owner_auth_v2、layout_*、registry_import 等），把已覆盖 AC 的用例改写为新行为；缺口（引导服务/接口、身份页新卡片、折叠边界、契约）新写。
- **新写用例标记**：目录/文件名 `*phone_match*`（后端）、`identity_property_*`（前端、小程序），位置按 module_design。
- **测试数据**：全部合成（"测试清册业主甲"、`139xxxxxxxx` 序列号码、"1栋1单元9层902号"等），不含真实姓名与手机号；后端测试库为内存库，无持久化冲突；`next_phone()` 序列保证唯一。
- **变异验证**：新写用例中关键安全/折叠/可见性用例已在 scratchpad 副本上做变异确认会失败（见 e2e_test_report"变异验证"）。

## 既有用例改写清单（GR-C-001 条件 (a)，REWORK_AUTHORIZED）

不删除用例、不改空断言；每条旧断言 → 新断言及对应 AC 见各层报告"既有用例改写"小节；汇总：

| 来源 | 条目 | 用例数（改写） |
|---|---|---|
| 后端 B1~B16 | test_registry_import_enhancement（151/152/153/155/156/157/166）、xlsx_defects（308）、gap_must_have、gap_journeys（E2E-014）、owner_auth_v2_residency（658）、registry_import_journeys（E2E-101/102）、scale_journeys（E2E-304）、identity_display_journey（E2E-501）、frontend_contract（488） | 16 |
| 前端 F1~F19 | layout_menus（804~807）、layout_nav（803/810/816/818）、layout_router（824/830）、layout_e2e（801/802）、user_menu（841）、layout_contract（923，另在基线用例表加 3 个 registry-matches 项）、identity_display（WEB-501~503）、owner_auth_v2（667~669）、layout_pages（885/914/888/889/890/898/904，删除 MeIdentity import）、product_review_ui（523/524/530，删除 MeIdentity import） | 30 |
| 小程序 M1~M4 | identity_display（MP-501）、owner_auth_v2（MP-504~506）、product_review_ui（UNIT-551）；TC-E2E-202 无需改动 | 5 |

条件 (b)：前端 TC-E2E-803（文件内 `testTimeout: 60000`）与小程序 TC-E2E-202（默认 5000 ms）在多次全量运行中均稳定通过（见 e2e_test_report"全量回归"），**未加超时余量**。

## AC 映射

说明：用例 ID 后带〔改〕的为既有用例改写；其余为新写。级别：unit/integration/e2e；运行方式：sim（本项目无硬件，均在本机软件环境运行）。位置列只写文件名，完整路径见下"新写用例文件"；改写的既有用例路径见各层报告"既有用例改写"。

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-232-01 | TC-UNIT-900、TC-INT-957、TC-INT-959、TC-INT-965、TC-WEB-901、TC-E2E-900、TC-E2E-910、TC-INT-488〔改〕 | unit/integration/e2e | sim | 新写 7 / 现有改写 1 | test_phone_match_service.py；test_phone_match_api.py；test_phone_match_contract.py；identity_property_identity_page.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js；test_frontend_contract.py | 产权业主 1 套住宅+同住人 1 套公寓 | 打开我的身份与房屋页/请求 /me/housing | 2 行含名称、类型、面积、关系；业主行同住人名单+移除，同住人行退出；/me/housing 字段集含 unit_type_label、area_display | 合成（C-73） |
| AC-232-02 | TC-UNIT-901、TC-INT-957、TC-WEB-902 | unit/integration | sim | 新写 3 | test_phone_match_service.py；test_phone_match_api.py；identity_property_identity_page.spec.js | 类型/面积未登记 | 打开页面 | 显示"未登记"，无 null/0/空白 | 合成（C-73） |
| AC-232-03 | TC-INT-958、TC-WEB-903 | integration/unit | sim | 新写 2 | test_phone_match_api.py；identity_property_identity_page.spec.js | 无有效关系（历史关系已结束） | 打开页面 | 暂无已认证房屋、0 行、已结束专有部分不出现、显示提醒 | 合成（C-73） |
| AC-232-04 | TC-WEB-907、TC-WEB-501〔改〕、TC-WEB-502〔改〕、TC-MP-906、TC-MP-501〔改〕 | unit | sim | 新写 2 / 现有改写 3 | identity_property_identity_page.spec.js；identity_display.spec.js；identity_property_pages.spec.js | 已认证 2 套 | 进入主页 | 无逐套明细；小卡片数字 2，可点击进 /units | 合成（C-73） |
| AC-232-05 | TC-WEB-904、TC-WEB-503〔改〕 | unit | sim | 新写 1 / 现有改写 1 | identity_property_identity_page.spec.js；identity_display.spec.js | /me/housing 请求失败 | 打开页面 | 加载失败，请重试+重试；不显示暂无/提醒/游客 | 合成（C-73） |
| AC-233-01 | TC-UNIT-931、TC-UNIT-805〔改〕、TC-INT-841〔改〕、TC-E2E-801〔改〕 | unit/integration/e2e | sim | 新写 1 / 现有改写 3 | identity_property_menu_router.spec.js；layout_menus.spec.js；user_menu.spec.js；layout_e2e.spec.js | 宽屏已登录 | 展开右上角菜单 | 7 项+退出登录；第 2 项"我的身份与房屋"；无恰为"我的身份"的项 | 合成（C-73） |
| AC-233-02 | TC-UNIT-932、TC-INT-970、TC-INT-971、TC-INT-824〔改〕、TC-E2E-910 | unit/integration/e2e | sim | 新写 4 / 现有改写 1 | identity_property_menu_router.spec.js；layout_router.spec.js；identity_property_e2e.spec.js | 两个入口 | 分别进入 /me/identity 与 /units | 同组件同 section；地址栏保持；后退一次回到前页 | 合成（C-73） |
| AC-233-03 | TC-INT-970、TC-INT-974、TC-INT-830〔改〕、TC-E2E-801〔改〕 | integration/e2e | sim | 新写 2 / 现有改写 2 | identity_property_menu_router.spec.js；layout_router.spec.js；layout_e2e.spec.js | 旧书签直开 | 打开 /me/identity、/units | 直接显示该页，不 404；未登录仍被守卫带去登录 | 合成（C-73） |
| AC-233-04 | TC-INT-904〔改〕、TC-INT-898〔改〕 | integration | sim | 新写 0 / 现有改写 2 | layout_pages.spec.js | 窄屏我的总览 | 查看入口 | 文案"我的身份与房屋"，指向 /me/identity | 合成（C-73） |
| AC-233-05 | TC-UNIT-930、TC-E2E-910 | unit/e2e | sim | 新写 2 | identity_property_menu_router.spec.js；identity_property_e2e.spec.js | 宽屏 /me/identity | 查看左侧 | 我的房屋展开，仅"我的身份与房屋"一个二级项高亮；/units 同 | 合成（C-73） |
| AC-234-01 | TC-WEB-910、TC-MP-903、TC-E2E-913、TC-E2E-801〔改〕 | unit/e2e | sim | 新写 3 / 现有改写 1 | identity_property_identity_page.spec.js；identity_property_pages.spec.js；identity_property_e2e.spec.js；layout_e2e.spec.js | 产权业主有 1 条待审批 | 打开身份页 | 最后一个卡片"待我审批的同住人申请"，1 行含通过/拒绝 | 合成（C-73） |
| AC-234-02 | TC-WEB-910、TC-E2E-913 | unit/e2e | sim | 新写 2 | identity_property_identity_page.spec.js；identity_property_e2e.spec.js | 同上 | 点通过 | 提示"已处理"，行消失，卡片显示暂无，数量 0 | 合成（C-73） |
| AC-234-03 | TC-WEB-911、TC-MP-903 | unit | sim | 新写 2 | identity_property_identity_page.spec.js；identity_property_pages.spec.js | 产权业主无待审批 | 打开页 | 卡片仍显示"暂无待审批的同住人申请" | 合成（C-73） |
| AC-234-04 | TC-WEB-912、TC-UNIT-933、TC-INT-890〔改〕、TC-E2E-901、TC-E2E-913、TC-MP-903 | unit/integration/e2e | sim | 新写 5 / 现有改写 1 | identity_property_identity_page.spec.js；identity_property_menu_router.spec.js；layout_pages.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js；identity_property_pages.spec.js | 游客/仅同住人 | 打开页并看二级菜单 | 无卡片（非空卡片），菜单无该项，不请求审批列表 | 合成（C-73） |
| AC-234-05 | TC-E2E-901、TC-WEB-914 | e2e/unit | sim | 新写 2 | test_phone_match_journeys.py；identity_property_identity_page.spec.js | A 非 2 栋户产权业主 | 列表与直接审批 | 卡片不含该申请；审批 403 FORBIDDEN，状态仍 PENDING | 合成（C-73） |
| AC-234-06 | TC-E2E-902、TC-WEB-913、TC-E2E-901 | e2e/unit | sim | 新写 3 | test_phone_match_journeys.py；identity_property_identity_page.spec.js | 2 套各 1 条；同一专有部分 2 位业主 | 打开页 | 恰 2 行；两位业主都能看到同一申请 | 合成（C-73） |
| AC-235-01 | TC-UNIT-933、TC-UNIT-806〔改〕、TC-INT-810〔改〕、TC-INT-818〔改〕、TC-INT-885〔改〕、TC-INT-914〔改〕、TC-E2E-902、TC-E2E-913 | unit/integration/e2e | sim | 新写 3 / 现有改写 5 | identity_property_menu_router.spec.js；layout_menus.spec.js；layout_nav.spec.js；layout_pages.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js | 产权业主有待审批 | 看二级菜单 | 角标挂在"我的身份与房屋"，为 0 不显示 | 合成（C-73） |
| AC-235-02 | TC-WEB-916、TC-INT-889〔改〕、TC-WEB-915 | unit/integration | sim | 新写 2 / 现有改写 1 | identity_property_identity_page.spec.js；layout_pages.spec.js | 主页链接 | 点击 | 链接指向 /units#review；进入后卡片被 scrollIntoView（真实可视区见人工清单） | 合成（C-73） |
| AC-235-03 | TC-UNIT-807〔改〕、TC-INT-830〔改〕、TC-INT-972、TC-WEB-915、TC-E2E-913 | unit/integration/e2e | sim | 新写 3 / 现有改写 2 | layout_menus.spec.js；layout_router.spec.js；identity_property_menu_router.spec.js；identity_property_identity_page.spec.js；identity_property_e2e.spec.js | 旧书签 /units/review、/units#review | 打开 | 到达身份页并定位；非产权业主无卡片；不 404 | 合成（C-73） |
| AC-235-04 | TC-WEB-916、TC-E2E-913 | unit/e2e | sim | 新写 2 | identity_property_identity_page.spec.js；identity_property_e2e.spec.js | 游客/同住人 | 看主页与菜单 | 无待审批链接、无角标 | 合成（C-73） |
| AC-236-01 | TC-UNIT-804〔改〕、TC-UNIT-931、TC-INT-803〔改〕、TC-E2E-910 | unit/integration/e2e | sim | 新写 2 / 现有改写 2 | layout_menus.spec.js；identity_property_menu_router.spec.js；layout_nav.spec.js；identity_property_e2e.spec.js | 宽屏展开我的房屋 | 看二级菜单 | 恰 5 项（我的身份与房屋、认证产权、认证申诉、我的同住人申请、我的申诉），无"选择房屋" | 合成（C-73） |
| AC-236-02 | TC-WEB-940、TC-UNIT-523〔改〕、TC-INT-890〔改〕、TC-MP-904、TC-E2E-912 | unit/integration/e2e | sim | 新写 3 / 现有改写 2 | identity_property_match_panel.spec.js；product_review_ui.spec.js；layout_pages.spec.js；identity_property_pages.spec.js；identity_property_e2e.spec.js | 点认证产权 | 页面加载 | 标题认证产权，含选房/姓名/认证按钮，无"申请成为同住人"按钮 | 合成（C-73） |
| AC-236-03 | TC-INT-973、TC-INT-824〔改〕 | integration | sim | 新写 1 / 现有改写 1 | identity_property_menu_router.spec.js；layout_router.spec.js | 旧书签 /units/pick | 打开 | 到达认证产权分区 | 合成（C-73） |
| AC-236-04 | TC-INT-816〔改〕、TC-INT-888〔改〕、TC-E2E-802〔改〕、TC-UNIT-931 | integration/e2e/unit | sim | 新写 1 / 现有改写 3 | layout_nav.spec.js；layout_pages.spec.js；layout_e2e.spec.js；identity_property_menu_router.spec.js | 窄屏切换条 | 看各页切换项 | 5 项含"认证产权"，无"选择房屋" | 合成（C-73） |
| AC-237-01 | TC-WEB-905、TC-MP-902 | unit | sim | 新写 2 | identity_property_identity_page.spec.js；identity_property_pages.spec.js | 任意已登录用户 | 打开身份页 | 有"认证产权"按钮，点击进认证产权页（小程序滚动到认证卡片） | 合成（C-73） |
| AC-237-02 | TC-WEB-903、TC-MP-902、TC-E2E-911、TC-E2E-912 | unit/e2e | sim | 新写 4 | identity_property_identity_page.spec.js；identity_property_pages.spec.js；identity_property_e2e.spec.js | 无有效关系 | 打开页 | 显示"您还没有认证任何专有部分，请先认证产权"+入口 | 合成（C-73） |
| AC-237-03 | TC-WEB-905、TC-MP-902 | unit | sim | 新写 2 | identity_property_identity_page.spec.js；identity_property_pages.spec.js | 已有房屋 | 打开页 | 不显示提醒，按钮仍显示 | 合成（C-73） |
| AC-237-04 | TC-WEB-906 | unit | sim | 新写 1 | identity_property_identity_page.spec.js | 仅有待审批同住人申请 | 打开页 | 仍显示提醒 | 合成（C-73） |
| AC-237-05 | TC-WEB-907、TC-WEB-502〔改〕、TC-INT-889〔改〕、TC-E2E-911 | unit/integration/e2e | sim | 新写 2 / 现有改写 2 | identity_property_identity_page.spec.js；identity_display.spec.js；layout_pages.spec.js；identity_property_e2e.spec.js | 主页无绑定 | 看空状态与快捷入口 | "去认证产权"链接→/units/pick；快捷入口"认证我的房屋"→/units/pick | 合成（C-73） |
| AC-238-01 | TC-WEB-940、TC-UNIT-667〔改〕、TC-UNIT-668〔改〕、TC-UNIT-669〔改〕、TC-UNIT-524〔改〕、TC-MP-904、TC-MP-504〔改〕、TC-MP-505〔改〕、TC-MP-506〔改〕、TC-E2E-912 | unit/e2e | sim | 新写 3 / 现有改写 7 | identity_property_match_panel.spec.js；owner_auth_v2.spec.js；product_review_ui.spec.js；identity_property_pages.spec.js；identity_property_e2e.spec.js | 打开认证产权页 | 查看姓名框 | 标签"您本人的姓名"，占位"请输入您本人的姓名（须与业主清册登记的姓名一致）"，无"请输入姓名"占位，无"户主" | 合成（C-73） |
| AC-238-02 | TC-WEB-940、TC-E2E-912 | unit/e2e | sim | 新写 2 | identity_property_match_panel.spec.js；identity_property_e2e.spec.js | 认证产权页 | 查看 | 无同住人按钮；提示链接指向 /units/applications | 合成（C-73） |
| AC-238-03 | TC-WEB-941、TC-UNIT-667〔改〕、TC-MP-504〔改〕 | unit | sim | 新写 1 / 现有改写 2 | identity_property_match_panel.spec.js；owner_auth_v2.spec.js | 姓名为空/全空格 | 点认证产权 | 提示"请输入姓名"，不发认证请求 | 合成（C-73） |
| AC-238-04 | TC-WEB-941、TC-UNIT-669〔改〕、TC-MP-506〔改〕 | unit | sim | 新写 1 / 现有改写 2 | identity_property_match_panel.spec.js；owner_auth_v2.spec.js | 服务端 OWNER_NOT_MATCHED | 点认证产权 | 提示并转申诉页带入姓名，不含清册信息 | 合成（C-73） |
| AC-239-01 | TC-UNIT-902、TC-UNIT-906、TC-INT-960、TC-UNIT-908、TC-INT-930、TC-INT-940、TC-INT-964、TC-WEB-920、TC-WEB-930、TC-E2E-900、TC-E2E-910、TC-E2E-920、TC-INT-151〔改〕 | unit/integration/e2e | sim | 新写 12 / 现有改写 1 | test_phone_match_service.py；test_phone_match_contract.py；test_phone_match_api.py；identity_property_match_panel.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js；test_registry_import_enhancement.py | 清册手机号 P 注册 | 注册成功 | registry_match pending；进入 /units/pick 显示询问文案与"是，确认认证"/"不是"；此时无 Membership | 合成（C-73） |
| AC-239-02 | TC-WEB-922、TC-MP-911、TC-INT-940 | unit/integration | sim | 新写 3 | identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_phone_match_api.py | 引导页打开 | 查看 | 匹配的专有部分默认全选预选（无需逐级选择） | 合成（C-73） |
| AC-239-03 | TC-UNIT-903、TC-INT-931、TC-WEB-921、TC-WEB-931、TC-MP-910 | unit/integration | sim | 新写 5 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js | 手机号不在清册 | 注册 | 不建行，直接进主页；接口失败面板不渲染 | 合成（C-73） |
| AC-239-04 | TC-UNIT-904、TC-INT-933、TC-INT-934 | unit/integration | sim | 新写 3 | test_phone_match_service.py；test_phone_match_api.py | 用户已是匹配专有部分的产权业主 | 触发匹配 | 已拥有的不计入；全部已拥有则不引导 | 合成（C-73） |
| AC-239-05 | TC-UNIT-905、TC-UNIT-921、TC-INT-935、TC-INT-938、TC-WEB-932、TC-E2E-920、TC-INT-155〔改〕、TC-INT-166〔改〕 | unit/integration/e2e | sim | 新写 6 / 现有改写 2 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_e2e.spec.js；test_registry_import_enhancement.py | 微信用户首次绑定手机号；之后换号 | 绑定/换号 | 绑定出现引导；换号后行 EXPIRED，无新引导 | 合成（C-73） |
| AC-239-06 | TC-UNIT-909、TC-UNIT-914、TC-UNIT-920、TC-INT-947、TC-INT-955、TC-INT-956、TC-WEB-928、TC-MP-914、TC-E2E-903、TC-E2E-911、TC-E2E-921 | unit/integration/e2e | sim | 新写 11 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js | 引导页 | 点"不是" | dismiss 204 无关系；GET pending=false；再登录不再弹；confirm 409；仍可手动认证 | 合成（C-73） |
| AC-239-07 | TC-UNIT-908、TC-INT-940、TC-WEB-920、TC-MP-909 | unit/integration | sim | 新写 4 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js | 引导页与响应 | 检查 | 只含坐落与类型；清册姓名/他人手机号/完整手机号 0 次 | 合成（C-73） |
| AC-239-08 | TC-UNIT-907、TC-INT-935、TC-INT-941、TC-INT-942、TC-WEB-921 | unit/integration | sim | 新写 5 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js | 无手机号/他人/未登录 | 访问引导接口 | 无匹配；未登录 401；查询参数被忽略，成功探测数 0 | 合成（C-73） |
| AC-239-09 | TC-UNIT-909、TC-INT-932 | unit/integration | sim | 新写 2 | test_phone_match_service.py；test_phone_match_api.py | 注册后清册才补手机号 | 再登录 | 不建行、不引导 | 合成（C-73） |
| AC-239-10 | TC-INT-943、TC-WEB-922、TC-MP-911、TC-E2E-910、TC-E2E-920 | integration/unit/e2e | sim | 新写 5 | test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；identity_property_e2e.spec.js | 匹配 12 套 | 打开引导页 | 前 10 套+"展开更多（还有 2 套）"；展开后 12 套；默认全选"已选 12 套"；后端返回全部无上限 | 合成（C-73） |
| AC-239-11 | TC-INT-943、TC-WEB-923、TC-MP-911 | integration/unit | sim | 新写 3 | test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js | 恰 10 套（及 11 套边界） | 打开引导页 | 10 套全显示无"展开更多"；11 套折叠 1 套 | 合成（C-73） |
| AC-239-12 | TC-INT-937、TC-INT-939、TC-WEB-932、TC-MP-908 | integration/unit | sim | 新写 4 | test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js | 绑定/换号发生账号合并 | 合并成功 | registry_match 为 {false,0}，不跳转引导；被并入账号的待确认行不再 PENDING | 合成（C-73） |
| AC-240-01 | TC-UNIT-910、TC-INT-944、TC-INT-962、TC-WEB-926、TC-MP-913、TC-E2E-900、TC-E2E-910 | unit/integration/e2e | sim | 新写 7 | test_phone_match_service.py；test_phone_match_api.py；test_phone_match_contract.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js | 引导页 1 套 | 点"是，确认认证" | 提示"认证成功，身份：产权业主"；房屋行出现，不含"户主"；请求只含 unit_ids | 合成（C-73） |
| AC-240-02 | TC-UNIT-911、TC-INT-944、TC-INT-949、TC-WEB-924、TC-MP-912、TC-E2E-900 | unit/integration/e2e | sim | 新写 6 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_phone_match_journeys.py | 3 套取消 1 套 | 确认 | 仅勾选的被认证；unit_ids 去重 | 合成（C-73） |
| AC-240-03 | TC-INT-948、TC-WEB-925、TC-MP-912 | integration/unit | sim | 新写 3 | test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js | 取消全部/非法 body | 确认 | 按钮禁用不发请求；服务端 400 INVALID_VALUE | 合成（C-73） |
| AC-240-04 | TC-UNIT-915、TC-INT-963、TC-UNIT-916、TC-UNIT-923、TC-INT-953、TC-WEB-927、TC-MP-913、TC-INT-308〔改〕 | unit/integration | sim | 新写 7 / 现有改写 1 | test_phone_match_service.py；test_phone_match_contract.py；test_phone_match_api.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_registry_import_xlsx_defects.py | 所选中 1 套已被认证/抛异常 | 确认 | 其余成功；succeeded/failed 数量；无 5xx；提示"成功 X 套，未成功 Y 套" | 合成（C-73） |
| AC-240-05 | TC-UNIT-917、TC-UNIT-918、TC-UNIT-919、TC-UNIT-922、TC-INT-952、TC-INT-153〔改〕、TC-INT-156〔改〕、TC-INT-157〔改〕 | unit/integration | sim | 新写 5 / 现有改写 3 | test_phone_match_service.py；test_phone_match_api.py；test_registry_import_enhancement.py | 确认认证 | 查看角色与审计 | 首位 HEAD、后者 OWNER、同住人升级；审计 origin_label=清册自动绑定、phone_masked 脱敏、无明文 | 合成（C-73） |
| AC-240-06 | TC-UNIT-912、TC-UNIT-913、TC-INT-945、TC-INT-946、TC-INT-950、TC-INT-951、TC-INT-954、TC-WEB-929 | unit/integration | sim | 新写 8 | test_phone_match_service.py；test_phone_match_api.py；identity_property_match_panel.spec.js | unit_ids 含他人手机号的专有部分/不存在/未登录/超限 | 构造 confirm | 整批 422 OWNER_NOT_MATCHED，无 Membership，响应无清册信息，仍 PENDING；401；限频 30 次/小时与手动认证共用键，第 31 次 429 | 合成（C-73） |
| AC-241-01 | TC-INT-930、TC-INT-964、TC-WEB-930、TC-MP-907、TC-E2E-900、TC-INT-151〔改〕、TC-INT-658〔改〕、test_reregister_owner_auto_bound_by_registry〔改〕、TC-E2E-014〔改〕 | integration/unit/e2e | sim | 新写 5 / 现有改写 4 | test_phone_match_api.py；test_phone_match_contract.py；identity_property_match_panel.spec.js；identity_property_pages.spec.js；test_phone_match_journeys.py；test_registry_import_enhancement.py；test_owner_auth_v2_residency.py；test_gap_must_have.py；test_gap_journeys.py | 清册号注册、未操作 | 查看 | 有效关系数 0；auto_bound 恒 []；无"自动认证"提示（前端源码也不再读 auto_bound） | 合成（C-73） |
| AC-241-02 | TC-INT-944、TC-WEB-926、TC-E2E-900 | integration/unit/e2e | sim | 新写 3 | test_phone_match_api.py；identity_property_match_panel.spec.js；test_phone_match_journeys.py | 同上 | 引导页确认 | 此时才产生有效关系 | 合成（C-73） |
| AC-241-03 | TC-INT-966、TC-INT-947、TC-E2E-903、TC-E2E-911 | integration/e2e | sim | 新写 4 | test_phone_match_api.py；test_phone_match_journeys.py；identity_property_e2e.spec.js | 未操作即离开，重新登录 | 打开身份页 | 仍无关系；提醒与认证产权按钮；引导仍可再确认 | 合成（C-73） |
| AC-241-04 | TC-INT-967、TC-UNIT-924 | integration/unit | sim | 新写 2 | test_phone_match_api.py；test_phone_match_service.py | 改动前已静默绑定的用户 | 登录 | 关系与身份不变，不建引导行 | 合成（C-73） |
| AC-242-01 | TC-MP-901、TC-MP-501〔改〕、TC-E2E-920 | unit/e2e | sim | 新写 2 / 现有改写 1 | identity_property_pages.spec.js；identity_display.spec.js；identity_property_e2e.spec.js | 小程序 1 套住宅(产权业主)+1 套公寓(同住人) | 打开我的房屋页 | 汇总身份+2 行含名称/类型/面积(未登记)/关系；首页无逐套明细 | 合成（C-73） |
| AC-242-02 | TC-MP-903 | unit | sim | 新写 1 | identity_property_pages.spec.js | 游客/同住人 vs 产权业主 | 打开页 | 前者无待审批卡片；产权业主页底有并可通过 | 合成（C-73） |
| AC-242-03 | TC-MP-902、TC-MP-904 | unit | sim | 新写 2 | identity_property_pages.spec.js | 小程序 | 查看认证产权卡片 | 标题认证产权，姓名占位为本人姓名，无同住人按钮；无关系时提醒 | 合成（C-73） |
| AC-242-04 | TC-INT-935、TC-INT-936、TC-INT-961、TC-MP-907、TC-MP-908、TC-MP-909、TC-E2E-920、TC-E2E-921 | integration/unit/e2e | sim | 新写 8 | test_phone_match_api.py；test_phone_match_contract.py；identity_property_pages.spec.js；identity_property_e2e.spec.js | 微信用户绑定匹配手机号 | 绑定完成 | navigateTo 我的房屋页出现引导；不再提示自动认证；确认后房屋出现；不匹配不引导 | 合成（C-73） |
| AC-242-05 | TC-MP-909 | unit | sim | 新写 1 | identity_property_pages.spec.js | 小程序引导卡片 | 检查展示 | 不含清册姓名/他人手机号/完整手机号 | 合成（C-73） |
| AC-242-06 | TC-MP-905、TC-UNIT-551〔改〕 | unit | sim | 新写 1 / 现有改写 1 | identity_property_pages.spec.js；product_review_ui.spec.js | 小程序同住人申请卡片 | 未选/选定后点申请 | 未选提示"请先选择房号"；选定只提交 {unit_id}，提示并出现在列表 | 合成（C-73） |
| AC-243-01 | TC-WEB-942、TC-UNIT-523〔改〕、TC-E2E-904、TC-E2E-912、TC-MP-905 | unit/e2e | sim | 新写 4 / 现有改写 1 | identity_property_match_panel.spec.js；product_review_ui.spec.js；test_phone_match_journeys.py；identity_property_e2e.spec.js；identity_property_pages.spec.js | /units/applications | 选房点申请 | 提示"申请已提交，等待产权业主审批"，列表新增 1 行，请求不含姓名 | 合成（C-73） |
| AC-243-02 | TC-WEB-942、TC-WEB-940 | unit | sim | 新写 2 | identity_property_match_panel.spec.js | 申请页 | 查看 | 含说明、无姓名框；认证产权页无该按钮 | 合成（C-73） |
| AC-243-03 | TC-WEB-942、TC-MP-905 | unit | sim | 新写 2 | identity_property_match_panel.spec.js；identity_property_pages.spec.js | 未选专有部分 | 查看按钮 | 禁用/拒绝，不发请求 | 合成（C-73） |
| AC-243-04 | TC-WEB-943、TC-E2E-904 | unit/e2e | sim | 新写 2 | identity_property_match_panel.spec.js；test_phone_match_journeys.py | 所选无有效产权业主 | 点申请 | 409 UNIT_HAS_NO_OWNER，提示后端文案，列表不变 | 合成（C-73） |
| AC-243-05 | TC-WEB-943、TC-E2E-904 | unit/e2e | sim | 新写 2 | identity_property_match_panel.spec.js；test_phone_match_journeys.py | 已是该专有部分产权业主 | 点申请 | 409 ALREADY_CERTIFIED，无申请记录 | 合成（C-73） |
| AC-243-06 | TC-WEB-943、TC-E2E-904 | unit/e2e | sim | 新写 2 | identity_property_match_panel.spec.js；test_phone_match_journeys.py | 已有待审申请 | 再次申请 | 409 APPLICATION_PENDING，只有 1 条待审；该申请出现在业主待审批（US-234） | 合成（C-73） |

### 新写用例文件

| 层 | 文件 | 用例 ID | 数量 |
|---|---|---|---|
| unit（后端） | backend/tests/unit/test_phone_match_service.py（+ 支撑 backend/tests/phone_match_support.py） | TC-UNIT-900~924 | 25 |
| integration（后端） | backend/tests/integration/test_phone_match_api.py | TC-INT-930~959、966、967 | 32 |
| integration（后端契约） | backend/tests/integration/test_phone_match_contract.py | TC-INT-960~965 | 6 |
| e2e（后端多步旅程） | backend/tests/e2e/test_phone_match_journeys.py | TC-E2E-900~904 | 5 |
| unit/integration（前端） | frontend/tests/identity_property_menu_router.spec.js | TC-UNIT-930~933、TC-INT-970~974 | 9 |
| unit（前端页面级） | frontend/tests/identity_property_identity_page.spec.js | TC-WEB-901~907、910~916 | 14 |
| unit（前端页面级） | frontend/tests/identity_property_match_panel.spec.js | TC-WEB-920~932、940~943 | 17 |
| e2e（前端） | frontend/tests/identity_property_e2e.spec.js | TC-E2E-910~913 | 4 |
| unit（小程序页面级） | miniprogram/tests/identity_property_pages.spec.js | TC-MP-901~914 | 14 |
| e2e（小程序） | miniprogram/tests/identity_property_e2e.spec.js | TC-E2E-920、921 | 2 |
| 合计 | | | 128（unit 74 / integration 43 / e2e 11） |

用例 ID 在三端各自编号区间互不重叠（后端 TC-UNIT-900~924、TC-INT-930~967、TC-E2E-900~904；前端 TC-UNIT-930~933、TC-INT-970~974、TC-E2E-910~913、TC-WEB-901~943；小程序 TC-MP-901~914、TC-E2E-920~921）。

## 测试数据需求

- 清册：合成专有部分（`1栋1单元9层902号` 等）、合成业主"测试清册业主甲/乙/丙/丁"、合成手机号（`tests.support.next_phone()` 序列与 `138000000xx`/`139000000xx` 固定样例）；车位样例 `车库B-n` 用于 10/11/12 套折叠边界。无 `[DATA_REQUIRED]`。
- 持久存储：后端为内存 SQLite，用例间事务回滚；前端/小程序无持久存储。

## 不可测项

| AC / 事项 | 原因 | 处理 |
|---|---|---|
| AC-242-01~06 的微信真机/开发者工具部分 | 小程序无法在本机构建（M-SD-006）；`uni` 为桩，WXSS 真实渲染、`uni.navigateTo` 真实栈行为未覆盖 | 页面脚本/模板的编译挂载已测（TC-MP-*）；真机见人工验证清单 MV-01 |
| AC-235-02 的"卡片位于可视区域内" | jsdom 无布局，仅可断言 `scrollIntoView` 被调用于 `#review` 元素 | 自动化部分已测（TC-WEB-915）；真实视口见 MV-02 |
| AC-233-02 的真实浏览器后退行为、窄屏 CSS 显隐 | jsdom 无真实浏览器历史栈与 CSS 媒体查询 | 路由级 `router.back()` 已测（TC-INT-971）；真实浏览器见 MV-03 |
| 迁移 `residency 0004_phone_match_prompt` 在 MySQL 上执行 | P8 禁止测试连接测试机数据库；测试配置置空迁移，SQLite 内存库以模型直接建表 | 开发已在 SQLite scratch 做 migrate/回退；MySQL 由 E2 部署阶段核验 MV-04 |
| 真实短信/微信手机号快速验证 | P11-3 不得真实调用，只用 FakeSmsGateway/FakeWeChatClient | 已用替身覆盖 |

上述 4 项（MV-01~MV-04）为 AC 层面的"部分不可测"，**不在用例层面 metrics 中计数**（用例级 not_testable = 0，每个涉及的 AC 都已有真实执行的自动化用例）。

## 故事覆盖核对

每个 Must Have 故事至少 1 个真实执行的用例（"已执行"= 本次全量最后一次运行通过）：

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-232 | TC-UNIT-900、TC-WEB-901、TC-UNIT-901、TC-WEB-902、TC-WEB-903、TC-WEB-907、TC-WEB-501〔改〕、TC-WEB-502〔改〕、TC-MP-906、TC-MP-501〔改〕、TC-WEB-904、TC-WEB-503〔改〕 | unit |
| US-232 | TC-INT-957、TC-INT-959、TC-INT-965、TC-INT-488〔改〕、TC-INT-958 | integration |
| US-232 | TC-E2E-900、TC-E2E-910 | e2e |
| US-233 | TC-UNIT-931、TC-UNIT-805〔改〕、TC-UNIT-932、TC-UNIT-930 | unit |
| US-233 | TC-INT-841〔改〕、TC-INT-970、TC-INT-971、TC-INT-824〔改〕、TC-INT-974、TC-INT-830〔改〕、TC-INT-904〔改〕、TC-INT-898〔改〕 | integration |
| US-233 | TC-E2E-801〔改〕、TC-E2E-910 | e2e |
| US-234 | TC-WEB-910、TC-MP-903、TC-WEB-911、TC-WEB-912、TC-UNIT-933、TC-WEB-914、TC-WEB-913 | unit |
| US-234 | TC-INT-890〔改〕 | integration |
| US-234 | TC-E2E-913、TC-E2E-801〔改〕、TC-E2E-901、TC-E2E-902 | e2e |
| US-236 | TC-UNIT-804〔改〕、TC-UNIT-931、TC-WEB-940、TC-UNIT-523〔改〕、TC-MP-904 | unit |
| US-236 | TC-INT-803〔改〕、TC-INT-890〔改〕、TC-INT-973、TC-INT-824〔改〕、TC-INT-816〔改〕、TC-INT-888〔改〕 | integration |
| US-236 | TC-E2E-910、TC-E2E-912、TC-E2E-802〔改〕 | e2e |
| US-237 | TC-WEB-905、TC-MP-902、TC-WEB-903、TC-WEB-906、TC-WEB-907、TC-WEB-502〔改〕 | unit |
| US-237 | TC-INT-889〔改〕 | integration |
| US-237 | TC-E2E-911、TC-E2E-912 | e2e |
| US-238 | TC-WEB-940、TC-UNIT-667〔改〕、TC-UNIT-668〔改〕、TC-UNIT-669〔改〕、TC-UNIT-524〔改〕、TC-MP-904、TC-MP-504〔改〕、TC-MP-505〔改〕、TC-MP-506〔改〕、TC-WEB-941 | unit |
| US-238 | TC-E2E-912 | e2e |
| US-239 | TC-UNIT-902、TC-UNIT-906、TC-UNIT-908、TC-WEB-920、TC-WEB-930、TC-WEB-922、TC-MP-911、TC-UNIT-903、TC-WEB-921、TC-WEB-931、TC-MP-910、TC-UNIT-904、TC-UNIT-905、TC-UNIT-921、TC-WEB-932、TC-UNIT-909、TC-UNIT-914、TC-UNIT-920、TC-WEB-928、TC-MP-914、TC-MP-909、TC-UNIT-907、TC-WEB-923、TC-MP-908 | unit |
| US-239 | TC-INT-960、TC-INT-930、TC-INT-940、TC-INT-964、TC-INT-151〔改〕、TC-INT-931、TC-INT-933、TC-INT-934、TC-INT-935、TC-INT-938、TC-INT-155〔改〕、TC-INT-166〔改〕、TC-INT-947、TC-INT-955、TC-INT-956、TC-INT-941、TC-INT-942、TC-INT-932、TC-INT-943、TC-INT-937、TC-INT-939 | integration |
| US-239 | TC-E2E-900、TC-E2E-910、TC-E2E-920、TC-E2E-903、TC-E2E-911、TC-E2E-921 | e2e |
| US-240 | TC-UNIT-910、TC-WEB-926、TC-MP-913、TC-UNIT-911、TC-WEB-924、TC-MP-912、TC-WEB-925、TC-UNIT-915、TC-UNIT-916、TC-UNIT-923、TC-WEB-927、TC-UNIT-917、TC-UNIT-918、TC-UNIT-919、TC-UNIT-922、TC-UNIT-912、TC-UNIT-913、TC-WEB-929 | unit |
| US-240 | TC-INT-944、TC-INT-962、TC-INT-949、TC-INT-948、TC-INT-963、TC-INT-953、TC-INT-308〔改〕、TC-INT-952、TC-INT-153〔改〕、TC-INT-156〔改〕、TC-INT-157〔改〕、TC-INT-945、TC-INT-946、TC-INT-950、TC-INT-951、TC-INT-954 | integration |
| US-240 | TC-E2E-900、TC-E2E-910 | e2e |
| US-241 | TC-WEB-930、TC-MP-907、TC-WEB-926、TC-UNIT-924 | unit |
| US-241 | TC-INT-930、TC-INT-964、TC-INT-151〔改〕、TC-INT-658〔改〕、test_reregister_owner_auto_bound_by_registry〔改〕、TC-INT-944、TC-INT-966、TC-INT-947、TC-INT-967 | integration |
| US-241 | TC-E2E-900、TC-E2E-014〔改〕、TC-E2E-903、TC-E2E-911 | e2e |
| US-243 | TC-WEB-942、TC-UNIT-523〔改〕、TC-MP-905、TC-WEB-940、TC-WEB-943 | unit |
| US-243 | TC-E2E-904、TC-E2E-912 | e2e |

Should Have 故事（不在 Must Have 核对范围，同批已测）：

| Should US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-235 | TC-UNIT-933、TC-UNIT-806〔改〕、TC-WEB-916、TC-WEB-915、TC-UNIT-807〔改〕 | unit |
| US-235 | TC-INT-810〔改〕、TC-INT-818〔改〕、TC-INT-885〔改〕、TC-INT-914〔改〕、TC-INT-889〔改〕、TC-INT-830〔改〕、TC-INT-972 | integration |
| US-235 | TC-E2E-902、TC-E2E-913 | e2e |
| US-242 | TC-MP-901、TC-MP-501〔改〕、TC-MP-903、TC-MP-902、TC-MP-904、TC-MP-907、TC-MP-908、TC-MP-909、TC-MP-905、TC-UNIT-551〔改〕 | unit |
| US-242 | TC-INT-935、TC-INT-936、TC-INT-961 | integration |
| US-242 | TC-E2E-920、TC-E2E-921 | e2e |

### 核对结论

- Must Have 故事 10 个（US-232、233、234、236、237、238、239、240、241、243），无空行；每个都有 unit 层与 e2e 层的已执行用例；US-232/233/234/236/237/239/240/241 另有 integration 层用例；US-238、US-243 没有独立 integration 层用例（其 AC 由页面级 unit 用例与 e2e 旅程覆盖，后端规则由 TC-E2E-903/904 与既有 residency 集成用例覆盖）。
- critical path（Must Have 故事的 E2E 用例）：10/10 个 Must Have 故事均有 E2E 级已执行用例 → 覆盖率 1.00；口径"替代"（见 e2e_test_report）。
- 契约测试：`backend/tests/integration/test_phone_match_contract.py`（TC-INT-960~965）解析 Web 与小程序 `api.js` 的三个新增 registry-matches 调用，逐个 resolve 到后端路由（视图 `RegistryMatchesView/ConfirmView/DismissView`，权限 `IsMember`）；另有前端 `layout_contract.spec.js` TC-INT-923/924/925 把三个函数纳入基线、方法+路径与 `urls.py` 对应；既有 `test_frontend_contract.py` 全部（含 TC-INT-488 字段集更新）通过。
