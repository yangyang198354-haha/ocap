<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T22:46:57.2524963+08:00</timestamp>
  <project_name>ocap_user_directory</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file><file>architecture/module_design.md</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 注册用户目录信息展示 测试计划

## 测试策略

- 被测改动：后端 `AdminUserListView` 新增 身份/认证套数/清册实名/上次登录 与实名搜索；Web 后台账号页新增四列与时间格式化。
- 范围：
  - in scope：US-132 ~ 136 的全部 AC；GR-B-001-F01（实名同记录匹配）、GR-B-001-F02（查询数有界）。
  - out of scope：既有身份认证流程、清册导入、其他后台页面。
- 环境：后端 `python manage.py test --settings=config.test_settings`（SQLite 内存库，Django test runner）；前端 `npm run test -- --run`（vitest + jsdom）。
- 判定模式：INCREMENTAL / baseline，零新增失败；新写用例全部通过；critical path 通过率 100%。
- 基线：后端 520 tests OK（9 skipped）；前端 152 passed / 2 failed（既有 Windows 主题环境问题：`theme_build.spec.js` CRLF、`theme.spec.js` 依赖 `/tmp`）；小程序 75 passed。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::类::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-132-01 身份与认证基础 | TC-INT-389 | 集成 | sim | 新写 | `backend/tests/integration/test_admin_user_directory.py::AdminUserDirectoryTests::test_tc_int_389_identity_priority` | 户主/游客/同住人/委员用户 | GET /admin/users | 身份与认证套数文案正确 | 5 个用户 |
| AC-132-02 主任优先于户主 | TC-INT-389 | 集成 | sim | 新写 | 同上 | 用户同时 CHAIR+HEAD | 同上 | 身份“主任” | 同上 |
| AC-132-03 副主任优先于产权业主 | TC-INT-389 | 集成 | sim | 新写 | 同上 | 用户同时 MEMBER/OWNER | 同上 | 身份“委员” | 同上 |
| AC-132-04 过期席位不计 | TC-INT-389 | 集成 | sim | 新写 | 同上 | 过期 REPRESENTATIVE + HEAD | 同上 | 身份“户主” | 同上 |
| AC-132-05 多套认证计数 | TC-INT-390 | 集成 | sim | 新写 | `...::test_tc_int_390_certified_units_count_and_revoke` | 两套有效认证 | 同上 | certified_units=2，撤销后=1 | 2 个专有部分 |
| AC-132-06 非管理员拒绝 | TC-INT-396 | 集成 | sim | 新写 | `...::test_tc_int_396_permissions` | 未登录/普通用户 | GET /admin/users | 401 / 403 | 普通用户 |
| AC-133-01 单套实名 | TC-INT-391 | 集成 | sim | 新写 | `...::test_tc_int_391_real_names_dedupe_and_join` | 清册张三+手机号匹配 | 同上 | real_names=["张三"] | 1 套 |
| AC-133-02 多套姓名并列 | TC-INT-391 | 集成 | sim | 新写 | 同上 | 两套姓名张三/李四 | 同上 | ["张三","李四"] | 2 套 |
| AC-133-03 同名去重 | TC-INT-391 | 集成 | sim | 新写 | 同上 | 三套其中两套同名 | 同上 | 只出现一次“张三” | 3 套 |
| AC-133-04 非业主/无手机号/未匹配 | TC-INT-392 | 集成 | sim | 新写 | `...::test_tc_int_392_real_names_empty_cases` | 四类空场景 | 同上 | real_names=[] | 4 个用户 |
| AC-133-05 撤销后不显示实名 | TC-INT-392 | 集成 | sim | 新写 | 同上 | 已结束 HEAD 认证 | 同上 | real_names=[]，身份游客 | 同上 |
| AC-134-01 时间格式 | TC-UNIT-410 | 单元（前端） | sim | 新写 | `frontend/tests/admin_users.spec.js::formatDateTime` | ISO 字符串 | 调用 formatDateTime | `2026-11-10 09:05` | 固定 ISO |
| AC-134-02 从未登录 | TC-UNIT-411 | 单元（前端） | sim | 新写 | `frontend/tests/admin_users.spec.js::四列渲染` | last_login_at=null | 挂载页面 | 显示“从未登录” | 2 行用户 |
| AC-134-03 最近一次登录 | TC-INT-393 | 集成 | sim | 新写 | `...::test_tc_int_393_last_login` | 用户有 last_login_at | GET /admin/users | 返回 ISO8601 | 2 个用户 |
| AC-134-04 绝对时间 | TC-UNIT-410 | 单元（前端） | sim | 新写 | 同上 | ISO 字符串 | formatDateTime | 不含相对时间 | 固定 ISO |
| AC-135-01 原列/脱敏保留 | TC-UNIT-411 | 单元（前端） | sim | 新写 | 同上 | 两行用户 | 挂载页面 | 四列存在，手机号 138****0001 | 2 行用户 |
| AC-135-02 实名搜索命中 | TC-INT-394 | 集成 | sim | 新写 | `...::test_tc_int_394_search_real_name_and_existing` | 清册张三 | GET ?q=张三 | 结果包含该用户 | 2 个用户 |
| AC-135-03 原搜索不变 | TC-INT-394 | 集成 | sim | 新写 | 同上 | 账号/昵称/手机号/后 4 位 | 同上 | 均命中相应用户 | 同上 |
| AC-135-04 未命中空列表 | TC-INT-394 | 集成 | sim | 新写 | 同上 | q=不存在 | 同上 | count=0 | 同上 |
| AC-135-05 分页/排序不变 | TC-INT-397 | 集成 | sim | 新写 | `...::test_tc_int_397_query_count_bounded` | 20 个用户 | page_size=1/20 | 查询数不随行数增长 | 20 个用户 |
| AC-136-01 撤销后回游客 | TC-INT-392 | 集成 | sim | 新写 | 同 AC-133-05 | 已结束认证 | GET /admin/users | 身份游客/未认证/实名空 | 1 个用户 |
| AC-136-02 部分撤销计数与实名 | TC-INT-390 | 集成 | sim | 新写 | 同 AC-132-05 | 两套撤销一套 | 同上 | certified_units=1 | 2 个专有部分 |
| AC-136-03 户主撤销后同住人身份 | TC-INT-390 | 集成 | sim | 新写 | 同上 | 户主+同住人 | 同上 | 身份仍为户主，数量减少 | 2 个专有部分 |
| AC-136-04 席位到期回退 | TC-INT-389 | 集成 | sim | 新写 | 同 AC-132-04 | 过期席位+HEAD | 同上 | 身份户主 | 1 个用户 |

补充用例：
- TC-INT-395：实名搜索同记录负向（跨 RegistryPhone 记录不得误匹配），对应 GR-B-001-F01。
- TC-E2E-305：管理员登录 → 按实名搜索 → 看到四类信息，覆盖 US-132 ~ 136 的端到端路径。
- TC-UNIT-411：四列渲染与空值文案（未认证/—/从未登录）。

## 测试数据需求

- 专有部分、清册业主、清册手机号、房屋关系、业委会席位均由测试内工厂创建，无需外部数据。
- 手机号使用 `tests.support.next_phone()` 或固定未占用号码，避免唯一约束冲突。
- 前端使用 `frontend/tests/http.mock.js` 模拟 HTTP，不访问真实后端。

## 不可测项

无。所有 AC 均有可执行用例。

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-132 身份与认证状态 | TC-INT-389、TC-INT-390、TC-INT-396、TC-E2E-305 | 集成 / E2E |
| US-133 清册实名 | TC-INT-391、TC-INT-392、TC-E2E-305 | 集成 / E2E |
| US-134 上次登录时间 | TC-INT-393、TC-UNIT-410、TC-UNIT-411、TC-E2E-305 | 单元（前端）/ 集成 / E2E |
| US-135 列表与实名搜索 | TC-INT-394、TC-INT-395、TC-INT-397、TC-UNIT-411、TC-E2E-305 | 单元（前端）/ 集成 / E2E |
| US-136 撤销后一致性 | TC-INT-389、TC-INT-390、TC-INT-392、TC-E2E-305 | 集成 / E2E |
