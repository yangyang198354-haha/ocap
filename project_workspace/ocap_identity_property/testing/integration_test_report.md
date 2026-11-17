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
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（PHASE_08，ocap_identity_property）

## 摘要

- 执行时间：同单元报告（后端 21:59:46~22:02:20；小程序约 22:03；前端 22:11~22:19，均为最后一次执行）。
- 环境：同单元报告（SQLite 内存库 + 真实 DRF 路由器与 ORM + FakeSms/FakeWeChat；前端/小程序仅 mock HTTP 层）。
- 命令：
  - `(cd backend && $PY manage.py test tests.integration --settings=config.test_settings)`
  - `(cd frontend && npx vitest run --passWithNoTests)`（TC-INT → integration 层）
  - `(cd miniprogram && npx vitest run --passWithNoTests)`（TC-INT → integration 层）
- **total = pass + fail + skip + blocked + not_testable = 856 = 856 + 0 + 0 + 0 + 0**（后端 725 + 前端 121 + 小程序 10）
- 通过率 = pass/(pass+fail+blocked) = 856/(856+0+0) = **1.00**
- 判定模式：baseline：基线 integration 层 813（后端 687 + 前端 116 + 小程序 10）；本次 856 = 813 + 新写 43（后端 38、前端 5），改写既有 26 条，新增失败 0。前置层（unit）门控 PASSED，允许执行本层。
- **本层门控：PASSED**

## 执行输出

```
$ (cd backend && $PY manage.py test tests.integration --settings=config.test_settings)
Ran 725 tests in 52.032s
OK

$ (cd frontend && npx vitest run --passWithNoTests)       # 全部 482 条，其中 integration 层 121
 Test Files  41 passed (41)
      Tests  482 passed (482)
   Duration  254.99s (transform 10.46s, setup 0ms, collect 74.04s, tests 115.67s, environment 44.38s, prepare 6.75s)

$ (cd miniprogram && npx vitest run --passWithNoTests)     # 全部 135 条，其中 integration 层 10
Test Files  18 passed (18)
      Tests  135 passed (135)
   Duration  46.39s (transform 2.31s, setup 1.54s, collect 11.11s, tests 8.02s, environment 16.66s, prepare 2.90s)
```

## 分项结果

### 集成边界：账号入口（MOD-133）↔ 引导服务（MOD-132）：注册 / 首次绑定手机号 / 换号 / 账号合并触发（backend/tests/integration/test_phone_match_api.py）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-930 | AC-239-01、AC-241-01 | 清册手机号注册 → auto_bound==[]、registry_match=={pending,count}、无 Membership、行 PENDING。 | PASS | — | — |
| TC-INT-931 | AC-239-03 | 手机号不在清册 → registry_match 为 {False,0}，不建行，注册 201。 | PASS | — | — |
| TC-INT-932 | AC-239-09 | 注册后管理员才在清册补该手机号 → 不建行，GET 匹配为空，再登录也不触发。 | PASS | — | — |
| TC-INT-933 | AC-239-04 | 手机号匹配的专有部分用户均已是产权业主 → count=0 不引导（经绑定手机号触发）。 | PASS | — | — |
| TC-INT-934 | AC-239-04 | 2 套匹配中已拥有 1 套 → count=1，仅列出未拥有的那套。 | PASS | — | — |
| TC-INT-935 | AC-239-05、AC-239-08、AC-242-04 | 微信用户无手机号时无匹配；首次绑定匹配手机号后出现 pending；响应 auto_bound==[]。 | PASS | — | — |
| TC-INT-936 | AC-242-04 | 绑定不在清册的手机号 → registry_match 为 {False,0}，不建行。 | PASS | — | — |
| TC-INT-937 | AC-239-12 | 绑定的手机号已属另一账号 → 合并；registry_match=={False,0}，主账号也无新引导。 | PASS | — | — |
| TC-INT-938 | AC-239-05 | 注册后（PENDING）更换为另一匹配清册的号码 → 行变 EXPIRED，不再引导，也不出现新引导。 | PASS | — | — |
| TC-INT-939 | AC-239-05、AC-239-12 | 换号并入另一账号 → 被并入账号的待确认行不再为 PENDING，主账号无新引导。 | PASS | — | — |

### 集成边界：引导接口 IFC-332/333/334 ↔ 清册/认证/审计/限频（MOD-132 ↔ registry、residency、core）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-940 | AC-239-01、AC-239-07、REQ-NFUNC-043 | 200 只含 pending/total/units；单项只含 unit_id/坐落/类型；不含姓名与手机号。 | PASS | — | — |
| TC-INT-941 | AC-239-08 | 未登录 401；管理员令牌不得读取成员引导接口（401/403）。 | PASS | — | — |
| TC-INT-942 | AC-239-08、REQ-NFUNC-043 | 查询参数（phone/user_id）被忽略；用户 B 只能看到自己手机号的匹配。 | PASS | — | — |
| TC-INT-943 | AC-239-10、AC-239-11 | 同号 12 套全部返回（后端不设上限、不折叠）；total==12，按数字自然顺序。 | PASS | — | — |
| TC-INT-944 | AC-240-01、AC-240-02、AC-241-02 | 请求只含 unit_ids；200 {succeeded,failed,results}；仅勾选的 2 套生成 Membership。 | PASS | — | — |
| TC-INT-945 | AC-240-06、REQ-NFUNC-043 | 含他人手机号的专有部分 → 422 OWNER_NOT_MATCHED，整批无 Membership，响应不含清册信息，仍 PENDING 可再确认。 | PASS | — | — |
| TC-INT-946 | AC-240-06 | 不存在的 unit_id 与越权同为 422 OWNER_NOT_MATCHED（不可据状态码区分存在性）。 | PASS | — | — |
| TC-INT-947 | AC-239-06、AC-241-03 | 无引导 / 已确认 / 已选 | PASS | — | — |
| TC-INT-948 | AC-240-03 | 空列表、非列表、缺字段、字符串/布尔/浮点元素、超 500 个 → 400 INVALID_VALUE，不产生关系。 | PASS | — | — |
| TC-INT-949 | AC-240-02 | 重复的 unit_id 去重，只处理一次，succeeded==1。 | PASS | — | — |
| TC-INT-950 | AC-240-06 | 未登录 401；dismiss 未登录同样 401。 | PASS | — | — |
| TC-INT-951 | AC-240-06 | 确认与手动认证共用 certify:{user.id} 每小时 30 次：先用 29 次手动认证（400/404 均计数），第 30 次确认仍可用，第 31 次 429。 | PASS | — | — |
| TC-INT-952 | AC-240-05 | 审计 origin_label=清册自动绑定，phone_masked=138-style 脱敏，不含明文手机号与清册姓名；用户端响应也不含。 | PASS | — | — |
| TC-INT-953 | AC-240-04 | 所选 B 已被本人手动认证 → A 成功，B 为 ALREADY_CERTIFIED，响应 succeeded==1/failed==1，无 5xx。 | PASS | — | — |
| TC-INT-954 | AC-240-06 | 用户 B 即使被拿到 A 的 unit_id 也无法确认（B 无 PENDING → 409；B 有 PENDING 但手机号不同 → 422）。 | PASS | — | — |
| TC-INT-955 | AC-239-06 | dismiss → 204 无关系；GET pending=false；再次 dismiss 仍 204；再登录不再弹出；可手动认证。 | PASS | — | — |
| TC-INT-956 | AC-239-06 | 无引导行时 dismiss 也返回 204，且不建行。 | PASS | — | — |
| TC-INT-957 | AC-232-01、AC-232-02 | /me/housing 的 units 含 unit_type_label、area_display；未登记为 | PASS | — | — |
| TC-INT-958 | AC-232-03 | 已结束的关系不出现在 /me/housing；无有效关系 units==[]、汇总为游客。 | PASS | — | — |
| TC-INT-959 | REQ-NFUNC-044 | /me identities.units 每套含 unit_type/unit_type_label/area/area_display（输出逐字不变）。 | PASS | — | — |
| TC-INT-966 | AC-241-03 | 注册后未在引导页操作（等同关闭浏览器），重新登录——仍无房屋关系，/me/housing 为空（页面据此显示提醒），引导仍可再次确认。 | PASS | — | — |
| TC-INT-967 | AC-241-04 | 改动前已静默绑定（source=REGISTRY）的既有用户，登录后身份与房屋关系不变，且不产生引导行（不追溯）。 | PASS | — | — |

### 集成边界：前后端契约（客户端 api.js ↔ 后端路由，MOD-137/138 ↔ MOD-132，backend/tests/integration/test_phone_match_contract.py）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-960 | REQ-NFUNC-044、AC-239-01 | Web api.js 三个新增调用被解析且各自 resolve 到 IsMember 视图并支持对应方法。 | PASS | — | — |
| TC-INT-961 | REQ-NFUNC-044、AC-242-04 | 小程序 api.js 同三个调用同样被解析并 resolve。 | PASS | — | — |
| TC-INT-962 | AC-240-01 | 两端 confirm 调用提交的字段名为 unit_ids（后端读取同名键），不提交姓名/手机号。 | PASS | — | — |
| TC-INT-963 | AC-239-01、AC-240-04 | Web 面板与小程序卡片读取 pending/units/unit_id/specific_part/unit_type_label、succeeded/failed， | PASS | — | — |
| TC-INT-964 | AC-239-01、AC-241-01 | Register.vue / MePhone.vue / 小程序 phone 页读取 registry_match.pending，真实注册响应含该字段； | PASS | — | — |
| TC-INT-965 | AC-232-01 | Web 身份页与小程序 | PASS | — | — |

契约结论：Web `frontend/src/shared/api.js` 与小程序 `miniprogram/utils/api.js` 各自的三个新增调用（GET `/me/registry-matches`、POST `/me/registry-matches/confirm`、POST `/me/registry-matches/dismiss`）均被 `extract_calls` 解析、`resolve()` 到后端视图（`RegistryMatchesView`/`RegistryMatchesConfirmView`/`RegistryMatchesDismissView`），视图支持对应 HTTP 方法，权限类恰为 `[IsMember]`，路径为字面量且无 `?`；确认请求键 `unit_ids` 与后端读取一致；面板/卡片读取的 `pending/units/unit_id/specific_part/unit_type_label/succeeded/failed` 是真实响应键子集；`registry_match.pending` 为注册与绑定响应真实字段，前端源码不再读取 `auto_bound`。既有契约套件 `test_frontend_contract.py`、`test_owner_auth_v2_contract.py` 全部通过（对"页面拆分后读取全部源文件"的静态读取，M-TE-035）。无无法对应到后端路由的调用。

### 集成边界：前端路由/菜单 ↔ 页面（MOD-135 ↔ MOD-136，frontend/tests/identity_property_menu_router.spec.js，5 条新写 integration）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-970 | AC-233-02、AC-233-03 | /me/identity 与 /units 解析为同一页面组件、同一 section，且直接显示不跳转（地址栏保持所访问的地址） | PASS | — | — |
| TC-INT-971 | AC-233-02 | 从 / 点进 /me/identity 后后退一次回到 /（无中间跳转历史） | PASS | — | — |
| TC-INT-972 | AC-235-03 | /units/review 与 /units#review 都到达"我的身份与房屋"页并带 #review 定位；不出现 404 | PASS | — | — |
| TC-INT-973 | AC-236-03 | 旧书签 /units/pick 仍到达"认证产权"分区；其余 /units/* 兼容路径可解析 | PASS | — | — |
| TC-INT-974 | AC-233-03 | 未登录访问 /me/identity 与 /units 被带去登录页并保留 redirect（守卫仍生效） | PASS | — | — |

## 既有用例改写（GR-C-001 条件 (a)，integration 层；不删除用例、不改空断言）

| TC | 文件 | AC | 旧断言 → 新断言 | 结果 |
|---|---|---|---|---|
| TC-INT-488 | backend/tests/integration/test_frontend_contract.py | AC-232-01 | /me/housing units[] 字段集严格等于旧 7 键 → 字段集加入 unit_type_label、area_display（9 键） | PASS |
| test_reregister_owner_auto_bound_by_registry | backend/tests/integration/test_gap_must_have.py | AC-241-01 | 注销后同号再注册，auto_bound 含该专有部分，Membership 来源 REGISTRY → auto_bound==[]、registry_match.pending、注册后无关系；confirm 后来源 REGISTRY；再手动认证 409 | PASS |
| TC-INT-658 | backend/tests/integration/test_owner_auth_v2_residency.py | AC-241-01、AC-240-01 | 注册即自动绑定且无姓名 → 注册后无 Membership；confirm 后绑定且无需姓名；姓名为空的清册同样可确认（用例改名 …needs_confirm_without_name） | PASS |
| TC-INT-151 | backend/tests/integration/test_registry_import_enhancement.py | AC-241-01、AC-240-01 | 注册响应 auto_bound 含该专有部分，Membership 已存在为 HEAD/REGISTRY → auto_bound==[]、registry_match=={pending:True,count:1}、注册后无 Membership；confirm 后 HEAD/REGISTRY，身份含"产权业主" | PASS |
| TC-INT-152 | backend/tests/integration/test_registry_import_enhancement.py | AC-239-10、AC-240-02 | 注册后 3 条 Membership 且均 HEAD → 注册后 0 条；confirm 3 个 unit_id 后 3 条、均 HEAD | PASS |
| TC-INT-153 | backend/tests/integration/test_registry_import_enhancement.py | AC-240-05 | 两位业主各自注册即得 HEAD/OWNER → 注册后无 Membership；各自 confirm，先确认者 HEAD、后确认者 OWNER，单元 HEAD 仅 1 | PASS |
| TC-INT-155 | backend/tests/integration/test_registry_import_enhancement.py | AC-239-05、AC-242-04 | 微信用户绑定响应 auto_bound==[unit]，已有 HEAD → auto_bound==[]、registry_match.pending、绑定后无 Membership；confirm 后才有 HEAD | PASS |
| TC-INT-156 | backend/tests/integration/test_registry_import_enhancement.py | AC-240-05 | 绑定后同住人即升级为 HEAD → 绑定后仍为 RESIDENT；confirm 后升级为 HEAD，旧行 end_reason=UPGRADED | PASS |
| TC-INT-157 | backend/tests/integration/test_registry_import_enhancement.py | AC-240-05 | 注册后即有审计 CERTIFY_BY_REGISTRY（来源清册自动绑定、不含明文） → 注册后无该审计；confirm 后有且 origin_label=清册自动绑定、phone_masked=138****0038，不含手机号/姓名明文 | PASS |
| TC-INT-166 | backend/tests/integration/test_registry_import_enhancement.py | AC-239-05 | 绑定响应 auto_bound==[unit]，已有 HEAD 与审计 → auto_bound==[]、pending；绑定后无 Membership/审计；confirm 后 HEAD 与审计 | PASS |
| TC-INT-308 | backend/tests/integration/test_registry_import_xlsx_defects.py | AC-240-04（DEF-009） | 注册时 1 套 certify_owner 抛异常，auto_bound 含其余 2 套 → 注册 auto_bound==[]、count==3；confirm 3 个 unit_id（mock 签名加 detail_extra），succeeded==2、failed==1，错误日志来自 apps.residency.auto_bind | PASS |
| TC-INT-923 | frontend/tests/layout_contract.spec.js | REQ-NFUNC-044（IFC-343） | meApi 导出函数基线 13 个 → 基线加入 registryMatches/confirmRegistryMatches/dismissRegistryMatches（16 个）；方法+路径用例 CASES 另加三项 | PASS |
| TC-INT-803 | frontend/tests/layout_nav.spec.js | AC-236-01 | 展开"我的房屋"见 6 个二级项 → 5 个，文案按新菜单 | PASS |
| TC-INT-810 | frontend/tests/layout_nav.spec.js | AC-235-01 | badges.pendingReview=2 时角标在"待我审批"项 → 角标在"我的身份与房屋"项；0/缺省不显示；菜单无"待我审批" | PASS |
| TC-INT-816 | frontend/tests/layout_nav.spec.js | AC-236-04 | 窄屏切换条 6 项含"选择房屋" → 5 项含"认证产权"，无"选择房屋" | PASS |
| TC-INT-818 | frontend/tests/layout_nav.spec.js | AC-235-01 | /units/review 下"待我审批"项角标 2 且高亮 → /units 下"我的身份与房屋"项角标 2 且高亮；0 不显示 | PASS |
| TC-INT-885 | frontend/tests/layout_pages.spec.js | AC-235-01 | 侧栏角标在"待我审批"项，首页链接 /units/review → 角标在"我的身份与房屋"项，窄屏切换条同值，侧栏无"待我审批" | PASS |
| TC-INT-888 | frontend/tests/layout_pages.spec.js | AC-236-04 | 窄屏我的房屋 6 项 → 5 项 | PASS |
| TC-INT-889 | frontend/tests/layout_pages.spec.js | AC-235-02、AC-237-05 | Home 源码含 to="/units/review" 且不含 /units#review → 含 to="/units#review" 且不含 to="/units/review"；快捷入口"认证我的房屋"→/units/pick | PASS |
| TC-INT-890 | frontend/tests/layout_pages.spec.js | AC-236-02、AC-234-04 | 6 个分区（含 review/选择房屋）各只显示自己的卡片 → 5 个分区各自卡片（含认证产权）；游客身份页无待审批卡；review 分区已取消回退身份页 | PASS |
| TC-INT-898 | frontend/tests/layout_pages.spec.js | AC-233-02 | 7 页含 MeIdentity（标题"身份"） → 7 页中第 2 页换为 UnitsIdentity（"我的身份与房屋"，产权业主另含底部待审批卡）；删除已不存在的 MeIdentity import；夹具补 residents | PASS |
| TC-INT-904 | frontend/tests/layout_pages.spec.js | AC-233-04 | 窄屏总览第 2 项"我的身份" → 第 2 项"我的身份与房屋" | PASS |
| TC-INT-914 | frontend/tests/layout_pages.spec.js | AC-235-01 | 展开"我的房屋"后"待我审批"项应有角标 2 → "我的身份与房屋"项有角标 2（无需先进入 /units*） | PASS |
| TC-INT-824 | frontend/tests/layout_router.spec.js | AC-233-03、AC-236-03 | /units 与 5 个 section（含 review） → /units 与 /me/identity 同组件同 section；pick/appeal/applications/appeals；review 为重定向 | PASS |
| TC-INT-830 | frontend/tests/layout_router.spec.js | AC-235-03 | /units#review 重定向到 /units/review → /units#review 停在 /units(#review)；/units/review 重定向 /units#review；/me/identity 不跳转；#appeal 仍→/units/appeal | PASS |
| TC-INT-841 | frontend/tests/user_menu.spec.js | AC-233-01 | 展开后第 2 项"我的身份" → 第 2 项"我的身份与房屋"，无恰为"我的身份"的项 | PASS |

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 说明 |
|---|---|---|---|
| integration 层用例总数 | 813（687 + 116 + 10） | 856 | +43 新写，全部 PASS |
| integration 层失败 | 0 | 0 | 无既有失败、无新增失败 |
| GROUP_C 报告的"预期失败"integration 层条目 | 26 条（后端 TC-INT-151/152/153/155/156/157/166/308/658/488 与 gap_must_have 再注册用例；前端 TC-INT-803/810/816/818/824/830/841/923/885/914/888/889/890/898/904） | 全部改写后通过 | 逐条依据见上表 |

失败清单：无；既有失败：无；新增失败：0。

## 失败汇总（需路由给开发）

无。观察项（非缺陷，已在 e2e 报告人工清单/注意事项记录）：CR-003（小程序引导卡片仅在挂载时拉取，`onShow` 不重取）无 AC 要求，未写失败用例。
