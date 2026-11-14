<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T09:45:35+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>requirements/product_review.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>phase_status.md</file><file>testing/test_plan.md（0.2.0）</file></input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：产品评审修正（ocap_product_review，INCREMENTAL / baseline）

> 0.3.0（缺陷回流 2/2 后的最终重测）：新增 TC-UNIT-590 ~ 601（`frontend/tests/product_review_rework2.spec.js`）、TC-INT-544 ~ 545（`backend/tests/integration/test_product_review_rework2.py`）；已冻结用例断言未改；DEF-021/022 经 TC-UNIT-586/587 转绿关闭，无新缺陷；三层均 PASSED（单元 500/500、集成 497/497、E2E 53/53，后端全量 712 OK、前端 244/244、小程序 94/94）。本版计数均来自 2026-11-14T09:35 ~ 09:42 的最后一次执行。
>
> （以下为 0.2.0 说明，仍有效）0.2.0（缺陷回流 1/2 后重测）：新增 TC-UNIT-579 ~ 589、TC-INT-539 ~ 543；已冻结用例断言未改；DEF-017/018/019 经 TC-INT-512/513/514 与新增用例确认关闭；新发现 DEF-021、DEF-022（见 e2e 报告"缺陷"与单元报告）。本版计数均来自 2026-11-14T09:04 之后的最后一次执行。

## 测试策略

**被测改动**：MOD-074 ~ 085（身份汇总与房屋聚合、`CLOSED` 终态与注销关闭、报销/备用金发起权限与金额上限、小程序 7 天会话、版式模板管理、报表明细脱敏、规则常量收拢、E2E 夹具命令、Web 公共件与页面、管理端页面、小程序）、迁移 `residency/0002_closed_status`，以及 29 个用户故事（US-150 ~ 178，其中 Must Have 15 个：US-150 ~ 162、176、178）。

**范围**
- in scope：上述故事的 AC 全部（后端 HTTP 行为、前端/小程序页面行为、契约、迁移、文档类 AC）；GR-A-001 / GR-C-001 的 GROUP_D conditions（见下）；远程 HTTP E2E 套件的编写（本阶段不运行）。
- out of scope：浏览器真机视觉验证、微信开发者工具真机、`uni build`、对测试机的任何连接（画像 P4、P4-1：远程套件由 E2 在用户授权后执行）、短信/邮件/微信真实服务（只用 `apps/integrations/fakes.py`）。

**环境**：`PY=/tmp/claude-0/-root-myproject-ocap/0130fd24-0fdc-48ac-9199-c3a574e51a0e/scratchpad/venv/bin/python`（Python 3.12.3、Django 5.2.19）；SQLite 内存库（`config.test_settings`，`MIGRATION_MODULES` 置空）；迁移用例另用 `backend/tests/migration_settings.py` + 系统临时目录的 SQLite 文件库（不连测试机库）；前端 vitest 2.1.9 / Node v22.23.3（jsdom，HTTP 层 mock）；小程序 vitest（uni 桩）。不安装任何依赖。

**判定模式**：INCREMENTAL / baseline（画像 P5）：每层相对基线零新增失败、新写用例全部通过，才进入下一层（回流 1 后 0.2.0 单元层因 TC-UNIT-586/587 失败门控 FAILED，集成与 E2E 层未执行；0.3.0 三层均 PASSED）；E2E critical path 通过率 1.00；E2E 必须覆盖前后端契约（契约用例在集成层）。

**基线来源**：PM invocation 与画像 P4 —— HEAD afa1fe8 改动前：后端 561 条、1 条既有失败 `TC-INT-311`、前端 181/181、小程序 75/75；GROUP_C 后 PM 复跑：后端 585（仅 TC-INT-311 失败）、前端 190/190、小程序 85/85。本阶段开始前我亲自复跑后端全量得 585 / 1 失败（TC-INT-311），与 PM 数字一致。

**回流 2 重测基线（0.3.0）**：PM 在 GROUP_C-005 后复跑：后端 710 OK、前端 232/232、小程序 94/94；我在写新用例前亲自复跑后端 unit/integration 数字与之一致（162 / 495）。判定仍为 baseline。

**回流 1 重测基线（0.2.0）**：PM 在 GROUP_C 修复后复跑：后端 705 OK、前端 221/221、小程序 94/94；我在新写用例前亲自复跑后端全量 `Ran 705 tests ... OK`，与之一致。判定仍为 baseline。

**分层机制（画像 P4）**：后端按目录 `tests/{unit,integration,e2e,smoke}`（Django runner 子命令）；前端与小程序没有分层目录，一律按"页面/组件级、HTTP 层或 uni 桩 mock"归入**单元层**（与既有 TC-UNIT-4xx 前端用例口径一致）；契约、迁移、文档扫描归**集成层**；多步跨角色旅程归 **E2E 层**；`backend/tests/remote/` 为独立的远程 HTTP E2E 套件（不属于默认分层命令）。

**用例编号区间（接续全仓最大编号 TC-UNIT-504 / TC-INT-423 / TC-E2E-308）**
| 区间 | 内容 |
|---|---|
| TC-UNIT-505 ~ 521 | 后端单元（`tests/unit/test_product_review_rules.py`） |
| TC-UNIT-522 ~ 550、577、578 | Web 前端页面/组件（`frontend/tests/product_review_ui.spec.js`） |
| TC-UNIT-579 ~ 589（回流 1 新增） | Web 前端：DEF-020 同类页面中文显示、Web 作废按钮 can_void、REQ-FUNC-158 同类扫描、Web 专有映射守护（`frontend/tests/product_review_rework1.spec.js`） |
| TC-UNIT-590 ~ 601（回流 2 新增） | Web 前端：回流 2 另修 8 处页面（InfoDetail、AdminAudit、AdminFinance、AdminMemberships、AdminContentPosts、AdminContentEditor 保存历史、Tasks 标题回退）的中文与时间格式；`shared/adminText.js` 四张映射的守护（`frontend/tests/product_review_rework2.spec.js`） |
| TC-UNIT-551 ~ 559 | 小程序页面（`miniprogram/tests/product_review_ui.spec.js`） |
| TC-UNIT-560 ~ 567 / 568 ~ 576 | 接管 GROUP_C 的 Web / 小程序 `product_review_core.spec.js`（只加编号前缀，断言未改） |
| TC-INT-424 ~ 477 | 后端集成（`test_product_review_ac.py`） |
| TC-INT-478 ~ 485 | 文档扫描（`test_requirements_numbering.py`） |
| TC-INT-486 ~ 496 | 前后端契约（追加到 `test_frontend_contract.py`） |
| TC-INT-497 | 迁移 0002 正向/反向（`test_migration_residency_0002.py`） |
| TC-INT-499 ~ 514 | product_review §2.1 定位级故事补验（`test_product_review_gap_stories.py`） |
| TC-INT-539 ~ 543（回流 1 新增） | DEF-019 非原审批人各自独立数据被拒 / can_void / DENIED 审计，DEF-017、DEF-018 审计字段（`test_product_review_rework1.py`） |
| TC-INT-544 ~ 545（回流 2 新增） | 字段级契约：`can_void`（Income.vue ↔ /admin/income/sheets）、adminText 枚举与管理端财务/审计页读取字段（`test_product_review_rework2.py`） |
| TC-INT-515 ~ 538 | 接管 GROUP_C 的 `test_product_review_api.py`（515 ~ 532）与 `test_e2e_fixture_command.py`（533 ~ 538）：在每个用例首行补 docstring 编号，断言未改 |
| TC-E2E-309 ~ 317、342、343 | 本地多步旅程（`tests/e2e/test_product_review_journeys.py`） |
| TC-E2E-318、319 | content_publish 补充旅程（`tests/e2e/test_product_review_content.py`） |
| TC-E2E-320 ~ 341 | **远程 HTTP E2E 套件**（`backend/tests/remote/remote_cases.py`，22 条，本阶段 BLOCKED） |

**既有用例的修改（规则：不删用例、不放宽断言）**：`backend/tests/integration/test_registry_import_xlsx_defects.py::XlsxImportTests::test_tc_int_311_downloaded_template_imports_back` —— 期望由"4 行 / 新增 2"改为"6 行、0 失败、新增 4 个专有部分（`1栋1单元3层301号`、`车库A-088`、`1栋负1层924号`、`10栋1层1号`）"，并增加专有部分名称集合断言；用例说明引用 REQ-FUNC-166（US-175 AC-175-02/03）与 admin_polish REQ-FUNC-129、AC-138-02、AC-138-03。依据：已批准需求 REQ-FUNC-166。

**新增的非用例辅助文件**：`backend/tests/migration_settings.py`（只供迁移用例的子进程使用，不匹配 `test*.py`，不被默认命令收集）；`backend/tests/remote/{__init__,remote_client,remote_cases,run_remote}.py`（文件名不匹配 `test*.py`，默认 `manage.py test` 与 CI 不收集；已用全量计数核对：712 = 162 + 497 + 47 + 6，不含远程 22 条（回流 2 后；0.2.0 为 710 = 162 + 495 + 47 + 6；0.1.0 为 705））。

**GROUP_D conditions 对应**
| 来源 | 条件 | 处理 |
|---|---|---|
| GR-A-001 | 定位级 CONSISTENT 行补 E2E；契约扩展到字段级；验证 §8 的 2 处推断 | 见 e2e 报告"product_review §2.1 已验证/未验证清单"、契约 TC-INT-486 ~ 496、§8 验证小节 |
| GR-A-002 / GR-B-001 | 修 TC-INT-311；Q-PR-05 夹具不改清册；Q-B-02 远程不改全局配置 | TC-INT-311 已更新通过；远程护栏 `WRITE_ALLOWLIST` 只允许 `dry_run=1` 预检且禁止写入有效的 `claim.amount_max` |
| GR-C-001 | 接管自验证用例；迁移 0002 正反向；管理员 401 语义核对；远程套件 | 全部完成，见各报告 |

## AC 映射

位置键对应文件见本节末尾的"位置键"表。"新写 / 接管(GROUP_C) / 修改(现有) / 现有"为用例来源。无硬件，运行方式列写"本地自动"（后端 Django runner、vitest）或"本地自动；远程 HTTP"（另有 `backend/tests/remote/` 用例，本阶段 BLOCKED）。测试数据：本地用例全部使用 `tests/support.py` 工厂现造数据（唯一化账号/手机号），无外部数据文件。

| AC | 用例 ID（位置键见下表） | 级别 | 运行方式 | 现有/新写 | 前置 | 动作 | 预期 | 备注 |
|---|---|---|---|---|---|---|---|---|
| AC-150-01 | TC-INT-424[AC]、TC-E2E-309[J]、TC-UNIT-522[WUI]、TC-UNIT-523[WUI]、TC-E2E-336[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | 注册用户，X 有产权业主 | 逐级选楼栋/单元/楼层/户号后提交 | 创建待审批申请，提示"申请已提交，等待产权业主审批"，页面无内部编号输入框 |  |
| AC-150-02 | TC-INT-425[AC] | INT | 本地自动 | 新写 | Y 无产权业主 | 为 Y 提交申请 | 409 UNIT_HAS_NO_OWNER，不创建 | 远程：需第 4 个空闲房屋 id，本地覆盖，远程不测 |
| AC-150-03 | TC-INT-426[AC]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 已有待审申请 | 再次提交 | 409 APPLICATION_PENDING，总数不增 |  |
| AC-150-04 | TC-UNIT-551[MUI]、TC-UNIT-573[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 小程序登录 | 我的房屋逐级选房并申请 | 同 AC-150-01，无内部编号输入框 |  |
| AC-151-01 | TC-INT-427[AC]、TC-E2E-309[J]、TC-UNIT-529[WUI]、TC-E2E-336[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | X 有 2 条待审，业主 O | 打开首页/审批列表 | 计数 2，列表恰 2 条，含昵称/房屋/时间，手机号脱敏 |  |
| AC-151-02 | TC-INT-428[AC]、TC-E2E-309[J]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | O 通过其中 1 条 | 刷新；另一业主再处理同一条 | 计数 1；申请人成同住人；再处理 409 ALREADY_DECIDED |  |
| AC-151-03 | TC-INT-429[AC]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | V 非 X 产权业主 | 看首页/直接审批 | 无提示；403；状态不变 |  |
| AC-151-04 | TC-INT-430[AC]、TC-UNIT-566[WCORE]、TC-UNIT-555[MUI] | INT+UNIT | 本地自动 | 接管(GROUP_C)、新写 | 名下无待审 | 打开首页 | 不显示提示 |  |
| AC-151-05 | TC-UNIT-555[MUI]、TC-UNIT-552[MUI] | UNIT | 本地自动 | 新写 | 产权业主登录小程序 | 打开首页并进入审批 | 同数量，可通过/拒绝 |  |
| AC-152-01 | TC-INT-431[AC]、TC-UNIT-527[WUI]、TC-E2E-309[J]、TC-E2E-336[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | U 已提交未处理 | 打开我的同住人申请 | 一条：房屋名、时间、待审批、处理时间空 |  |
| AC-152-02 | TC-INT-431[AC]、TC-E2E-309[J]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 业主拒绝 | 刷新；再次提交 | 已拒绝+处理时间；再提交成功出新记录 |  |
| AC-152-03 | TC-INT-431[AC]、TC-UNIT-527[WUI]、TC-E2E-336[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | W 从未申请 | 打开列表 | 空列表，"暂无同住人申请" |  |
| AC-152-04 | TC-UNIT-552[MUI] | UNIT | 本地自动 | 新写 | 小程序登录 | 打开同住人申请列表 | 同 Web |  |
| AC-153-01 | TC-INT-432[AC]、TC-E2E-309[J]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | X 有同住人 T | 业主移除（确认） | T 不在名单；T 在他处身份不变；无其他身份回游客 |  |
| AC-153-02 | TC-INT-433[AC]、TC-E2E-309[J]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | T 是同住人 | T 退出（确认） | 身份解除，回游客 |  |
| AC-153-03 | TC-INT-434[AC]、TC-E2E-336[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 另一同住人/他房户主/管理员 | 尝试移除 T | 403，T 仍在 |  |
| AC-153-04 | TC-UNIT-525[WUI]、TC-UNIT-526[WUI]、TC-UNIT-562[WCORE]、TC-UNIT-553[MUI] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 点"移除/退出" | 弹窗点取消 | 不发请求，名单不变 | [UI] |
| AC-153-05 | TC-UNIT-553[MUI]、TC-UNIT-572[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 小程序登录 | 移除/退出（含确认） | 同 AC-153-01/02 |  |
| AC-154-01 | TC-INT-436[AC]、TC-INT-522[API]、TC-UNIT-576[MCORE]、TC-E2E-333[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 非成员登录 | 直接请求发起报销/备用金 | 403，提示含"业委会成员"，不创建 |  |
| AC-154-02 | TC-INT-435[AC]、TC-E2E-312[J]、TC-E2E-334[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 现任委员 | 发起报销 | 创建成功，状态审批中 |  |
| AC-154-03 | TC-INT-522[API]、TC-E2E-333[R] | INT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 业主代表/到期席位成员 | 发起 | 403，不创建 |  |
| AC-154-04 | TC-UNIT-577[WUI]、TC-UNIT-564[WCORE]、TC-UNIT-565[WCORE]、TC-UNIT-556[MUI]、TC-UNIT-575[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 非成员 / 成员 | 查看导航与首页 | 无入口/按钮；成员可见 | [UI] |
| GR-C-001-F03 | TC-INT-437[AC]、TC-INT-522[API] | INT | 本地自动 | 接管(GROUP_C)、新写 | 管理员令牌 | POST 报销/备用金 | AC-154 只规定非成员 403；管理员为 401（IFC-265 登记的语义变化），与 AC 不矛盾，固化现状 | 观察项 OBS-1 |
| AC-155-01 | TC-INT-439[AC]、TC-INT-527[API]、TC-INT-529[API]、TC-E2E-315[J]、TC-E2E-331[R]、TC-E2E-332[R] | INT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 小程序验证码登录 | 闲置 31 分钟后请求 | 仍成功；Web 对照 401 | 远程 332 为慢用例，默认 SKIP |
| AC-155-02 | TC-INT-529[API]、TC-E2E-315[J]、TC-UNIT-510[RULE]、TC-UNIT-511[RULE] | INT+E2E+UNIT | 本地自动 | 接管(GROUP_C)、新写 | 小程序密码登录，可控时钟 | 6 天 23 小时 / 满 7 天 | 访问成功 / 401 |  |
| AC-155-03 | TC-INT-438[AC]、TC-INT-528[API] | INT | 本地自动 | 接管(GROUP_C)、新写 | Web 未勾选记住我 / 管理员 | 闲置 31 分钟 | 被拒；记住我保持 |  |
| AC-156-01 | TC-INT-440[AC]、TC-E2E-310[J]、TC-UNIT-527[WUI]、TC-E2E-337[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | U 已申诉未处理 | 打开我的申诉 | 待审核，处理时间空 |  |
| AC-156-02 | TC-INT-440[AC]、TC-E2E-310[J]、TC-UNIT-527[WUI]、TC-E2E-337[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | 管理员驳回并填原因 | 刷新 | 已驳回+处理时间+原因原文 |  |
| AC-156-03 | TC-INT-440[AC]、TC-E2E-337[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 管理员通过 | 刷新 | 已通过；身份出现在房屋列表 |  |
| AC-156-04 | TC-INT-440[AC]、TC-UNIT-554[MUI]、TC-E2E-337[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | W 从未申诉 | 打开列表 | 空，"暂无申诉" |  |
| AC-156-05 | TC-UNIT-554[MUI]、TC-UNIT-572[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 小程序登录 | 打开申诉列表 | 同 Web（含驳回原因） |  |
| AC-157-01 | TC-INT-441[AC]、TC-INT-517[API]、TC-INT-488[CON]、TC-INT-489[CON]、TC-UNIT-530[WUI]、TC-UNIT-557[MUI]、TC-E2E-310[J]、TC-E2E-321[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | U 在 A 户主、B 同住人 | 查看个人中心/我的房屋/小程序我的 | 三处两行 A（户主）B（同住人），汇总户主，刷新顺序稳定 |  |
| AC-157-02 | TC-INT-442[AC]、TC-INT-518[API]、TC-UNIT-512[RULE]、TC-UNIT-514[RULE] | INT+UNIT | 本地自动 | 接管(GROUP_C)、新写 | 副主任且户主 | 查看身份 | 汇总副主任，房屋行仍户主 |  |
| AC-157-03 | TC-INT-443[AC]、TC-INT-516[API]、TC-UNIT-528[WUI]、TC-E2E-321[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 游客 | 查看身份 | 汇总游客，"暂无已认证房屋" |  |
| AC-157-04 | TC-INT-441[AC]、TC-E2E-310[J]、TC-E2E-321[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 同一用户 | 管理端注册用户列表看其身份 | 与本人汇总一致 |  |
| AC-157-05 | TC-INT-444[AC]、TC-UNIT-530[WUI]、TC-UNIT-550[WUI] | INT+UNIT | 本地自动 | 新写 | 管理员撤销 B 认证 | U 刷新 | 不含 B；全中文；无编辑控件 |  |
| AC-158-01 | TC-UNIT-540[WUI]、TC-UNIT-548[WUI] | UNIT | 本地自动 | 新写 | 管理员点撤销认证 | 弹窗点取消 / 确认 | 后果文案；取消无请求；确认才 POST | [UI] |
| AC-158-02 | TC-INT-444[AC]、TC-E2E-310[J]、TC-E2E-337[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 管理员确认撤销 e2e 用户认证 | 确认生效 | 用户无身份；审计新增撤销记录 |  |
| AC-158-03 | TC-UNIT-542[WUI]、TC-UNIT-548[WUI]、TC-UNIT-525[WUI]、TC-UNIT-526[WUI]、TC-UNIT-562[WCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 撤销席位/删单元/删流程/作废/撤回 | 弹窗点取消 / 确认 | 取消无变更；确认才执行；11 个确认键均被页面使用且"确认失败即 return" | [UI]；Income/Claims/ResolutionDetail/AdminRegistry 的页面级取消路径由 TC-UNIT-548 的源码守护覆盖，未逐页挂载（见 e2e 报告未验证清单） |
| AC-158-04 | TC-UNIT-534[WUI]、TC-UNIT-562[WCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 点注销账号 | 弹窗取消 / 确认 | 列出 4 项后果；取消无请求；确认才注销 | [UI] |
| AC-159-01 | TC-INT-445[AC]、TC-INT-494[CON]、TC-E2E-313[J]、TC-E2E-324[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 管理员，用户 P | 按账号/手机号后四位/实名搜索 | 三次都命中 P；脱敏手机号、最高身份 | 实名搜索只在本地测（夹具无清册实名） |
| AC-159-02 | TC-UNIT-541[WUI]、TC-UNIT-549[WUI] | UNIT | 本地自动 | 新写 | 选中候选 P | 返回表单 | 显示昵称与最高身份；无用户 ID 输入框 | [UI] |
| AC-159-03 | TC-INT-446[AC]、TC-E2E-313[J]、TC-E2E-325[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 选中游客赋予委员 | 提交 | 422 NOT_AN_OWNER，不创建席位 |  |
| AC-159-04 | TC-UNIT-578[WUI]、TC-INT-449[AC] | UNIT+INT | 本地自动 | 新写 | 无匹配/超一页 | 搜索 | "无匹配用户"；可翻页 |  |
| AC-159-05 | TC-INT-447[AC]、TC-E2E-313[J]、TC-E2E-338[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 审批流程页添加审批人 | 选两位成员保存；选非成员 | 列表显示昵称；非成员沿用拒绝 |  |
| AC-159-06 | TC-INT-448[AC]、TC-E2E-313[J]、TC-E2E-324[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 非管理员 | 请求用户搜索 | 403 无用户信息 |  |
| AC-160-01 | TC-INT-449[AC]、TC-E2E-313[J]、TC-UNIT-543[WUI]、TC-E2E-326[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | 注册用户 N>20 | 账号页翻页 | 第 1 页 20，共 N，合计 N 无重复 |  |
| AC-160-02 | TC-INT-449[AC]、TC-UNIT-544[WUI]、TC-E2E-326[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | 搜索命中 M>20 | 翻到第 2 页 | 同一关键词，第 21~40 条 |  |
| AC-160-03 | TC-INT-450[AC]、TC-E2E-313[J] | INT+E2E | 本地自动 | 新写 | 五个管理端列表 >20 | 翻页 | 各列表总数与全部页 |  |
| AC-160-04 | TC-INT-450[AC] | INT | 本地自动 | 新写 | 列表 ≤20 | 打开 | 全部记录与总数，无空白页 |  |
| AC-161-01 | TC-INT-451[AC]、TC-E2E-342[J]、TC-UNIT-539[WUI]、TC-E2E-327[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | 公开决议 N>20 | 翻页 | 20/页，总数 N，合计无重复 |  |
| AC-161-02 | TC-INT-452[AC]、TC-INT-496[CON]、TC-UNIT-563[WCORE] | INT+UNIT | 本地自动 | 接管(GROUP_C)、新写 | 其他用户端列表 >20 | Web 翻页 | 分页形态 {count,results}，usePaging 保持筛选 | Web 各列表页面级逐页翻页未逐一挂载，见未验证清单 |
| AC-161-03 | TC-UNIT-558[MUI]、TC-UNIT-559[MUI]、TC-UNIT-571[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 小程序决议 >20 | 加载更多 | 追加 ≤20，到底显示"没有更多了，共 N 条" |  |
| AC-161-04 | TC-INT-451[AC]、TC-UNIT-539[WUI]、TC-E2E-342[J]、TC-E2E-327[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | 记录 ≤20 | 打开 | 全部记录与总数，无翻页控件 |  |
| AC-162-01 | TC-INT-453[AC]、TC-E2E-314[J]、TC-E2E-339[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 管理员 | 新建"e2e_模板A" | 列表与编辑器模板列表都出现 |  |
| AC-162-02 | TC-INT-453[AC]、TC-E2E-318[C]、TC-E2E-314[J] | INT+E2E | 本地自动 | 新写 | 自定义模板 | 另一内容选用并预览 | 样式值逐项一致，内容文字不变 |  |
| AC-162-03 | TC-INT-454[AC]、TC-E2E-319[C]、TC-UNIT-545[WUI]、TC-E2E-339[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 新写 | 已有自定义模板 | 改名改样式；名称为空 | 新值生效；空名"模板名称不能为空" |  |
| AC-162-04 | TC-INT-455[AC]、TC-INT-530[API]、TC-UNIT-546[WUI]、TC-E2E-314[J]、TC-E2E-339[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 未引用 / 被 K 条引用 | 删除 | 成功；409 提示 K 条，保留 |  |
| AC-162-05 | TC-INT-456[AC]、TC-INT-530[API]、TC-UNIT-545[WUI]、TC-E2E-339[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 内置模板 | 查看/请求修改删除 | 无入口；PUT/DELETE 404，不变 |  |
| AC-162-06 | TC-INT-457[AC]、TC-E2E-339[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 非管理员 | 新建/修改/删除 | 403 |  |
| AC-163-01 | TC-UNIT-535[WUI] | UNIT | 本地自动 | 新写 | 访客 | 看密码登录输入框提示 | "账号或手机号"，不含"邮箱" | [UI] |
| AC-163-02 | TC-INT-458[AC]、TC-E2E-330[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 访客 | 邮箱+密码 | 统一失败提示 |  |
| AC-164-01 | TC-INT-459[AC]、TC-INT-519[API]、TC-INT-521[API]、TC-UNIT-515[RULE]、TC-E2E-311[J] | INT+UNIT+E2E | 本地自动 | 接管(GROUP_C)、新写 | U 有待审申请与申诉 | 注销 | 列表不再出现；审计 2 条关闭 | 注销需验证码，远程不测 |
| AC-164-02 | TC-INT-459[AC]、TC-INT-520[API]、TC-E2E-311[J] | INT+E2E | 本地自动 | 接管(GROUP_C)、新写 | 已关闭记录 | 业主/管理员尝试通过 | 409 ALREADY_CLOSED，不产生房屋关系 |  |
| AC-164-03 | TC-INT-459[AC]、TC-INT-519[API]、TC-UNIT-515[RULE] | INT+UNIT | 本地自动 | 接管(GROUP_C)、新写 | U 有已处理历史 | 注销 | 历史不变 |  |
| AC-164-04 | TC-INT-459[AC]、TC-UNIT-515[RULE] | INT+UNIT | 本地自动 | 新写 | 无待处理 | 注销 | 成功，不新增关闭记录 |  |
| AC-165-01 | TC-INT-460[AC]、TC-UNIT-532[WUI]、TC-E2E-341[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 新写 | 个人中心资料卡 | 选生日保存刷新；留空 | 显示保存日期；留空成功 |  |
| AC-165-02 | TC-INT-461[AC]、TC-UNIT-533[WUI] | INT+UNIT | 本地自动 | 新写 | 合规头像 | 保存 | 个人中心显示图片（鉴权下载） |  |
| AC-165-03 | TC-UNIT-531[WUI] | UNIT | 本地自动 | 新写 | 更换头像 | 打开选择/选超限文件 | 提示"jpg/png，不超过 2 MB"，仅 jpg/png，超限拒绝 | [UI] |
| AC-166-01 | TC-UNIT-577[WUI]、TC-UNIT-556[MUI] | UNIT | 本地自动 | 新写 | 非成员 / 成员 | 看导航与快捷入口 | 无"待办"；成员可见 | [UI] |
| AC-166-02 | TC-INT-462[AC]、TC-E2E-322[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 非成员 | 请求待办 | 403；入口与权限一致 |  |
| AC-166-03 | TC-INT-427[AC]、TC-UNIT-556[MUI] | INT+UNIT | 本地自动 | 新写 | 非成员产权业主有待审申请 | 打开首页 | 仍可见待审提示 |  |
| AC-167-01 | TC-UNIT-524[WUI]、TC-UNIT-560[WCORE]、TC-UNIT-569[MCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 认证成功 | 看提示 | "认证成功，身份：户主"，无 HEAD/OWNER | [UI]；§8 推断 1 的验证 |
| AC-167-02 | TC-UNIT-537[WUI] | UNIT | 本地自动 | 新写 | 投票列表 | 打开 | "进行中/已结束"，"2026-11-13 20:30" | [UI] |
| AC-167-03 | TC-UNIT-543[WUI]、TC-UNIT-560[WCORE] | UNIT | 本地自动 | 接管(GROUP_C)、新写 | 席位页与账号页 | 看状态/启用列 | 中文，是/否，无 ACTIVE/true/false | [UI] |
| AC-168-01 | TC-INT-463[AC]、TC-INT-531[API]、TC-E2E-312[J]、TC-INT-493[CON]、TC-UNIT-574[MCORE]、TC-UNIT-575[MCORE]、TC-E2E-328[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 已生成季度报表 | 小程序点击该期 | 明细与合计，合计与 Web 一致，支出事由为空 | 远程：无报表则 SKIP |
| AC-168-02 | TC-INT-463[AC]、TC-E2E-328[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 未登录 | 请求报表明细 | 401 |  |
| AC-168-03 | TC-UNIT-557[MUI]、TC-INT-463[AC] | UNIT+INT | 本地自动 | 新写 | 无已生成报表 | 打开财务报表 | "暂无已生成报表" |  |
| AC-169-01 | TC-INT-464[AC]、TC-E2E-314[J]、TC-UNIT-536[WUI]、TC-UNIT-567[WCORE]、TC-E2E-340[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 内容已下线 | 打开详情 | 404；页面"内容不存在或已下线"+返回列表 |  |
| AC-169-02 | TC-INT-464[AC]、TC-UNIT-536[WUI] | INT+UNIT | 本地自动 | 新写 | 不存在编号/正常内容 | 打开 | 同样提示；正常照常 |  |
| AC-170-01 | TC-INT-466[AC]、TC-INT-523[API]、TC-E2E-312[J]、TC-UNIT-547[WUI]、TC-E2E-334[R] | INT+E2E+UNIT | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 管理员设上限 500000 | 提交 500000.01 / .00 | 失败提示当前上限；成功；测后恢复 | 远程只测默认边界，不写全局配置（Q-B-02） |
| AC-170-02 | TC-INT-465[AC]、TC-INT-523[API]、TC-UNIT-508[RULE]、TC-E2E-334[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 从未设置 | 提交 1,000,000.01 / .00 | 失败 / 成功 |  |
| AC-170-03 | TC-INT-466[AC]、TC-INT-523[API]、TC-E2E-312[J] | INT+E2E | 本地自动 | 接管(GROUP_C)、新写 | 上限 100 万→50 万 | 查看旧 80 万记录；审计 | 旧记录不变；审计 1 条 |  |
| AC-170-04 | TC-INT-467[AC]、TC-INT-524[API]、TC-UNIT-505[RULE]、TC-UNIT-506[RULE]、TC-E2E-335[R] | INT+UNIT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 非管理员 / 非法值 | 修改上限 | 403；400 原值不变 |  |
| AC-170-05 | TC-INT-471[AC]、TC-INT-525[API]、TC-UNIT-509[RULE] | INT+UNIT | 本地自动 | 接管(GROUP_C)、新写 | 上限 500000 | 录入收入 500000.01 | 拒绝并提示上限 |  |
| AC-171-01 | TC-INT-468[AC]、TC-E2E-316[J] | INT+E2E | 本地自动 | 新写 | 在任 5 人，3 同意 1 反对 1 弃权 | 截止判定 | 通过，分母 5 | 既有 ResolutionJudgeRuleTests 同类 |
| AC-171-02 | TC-INT-468[AC] | INT | 本地自动 | 新写 | 在任 5 人，2/2/1 | 截止判定 | 未通过 |  |
| AC-171-03 | TC-INT-468[AC] | INT | 本地自动 | 新写 | 在任 4 人，2 同意 2 弃权 | 截止判定 | 未通过 |  |
| AC-171-04 | TC-INT-468[AC]、TC-E2E-316[J] | INT+E2E | 本地自动 | 新写 | 截止未到 | 查看 | 不判定 |  |
| AC-172-01 | TC-UNIT-538[WUI]、TC-INT-526[API]、TC-E2E-323[R] | UNIT+INT+E2E | 本地自动；远程 HTTP | 接管(GROUP_C)、新写 | 主任/副主任 | 打开发起页 | 预先显示限制文案 | [UI] |
| AC-172-02 | TC-INT-469[AC] | INT | 本地自动 | 新写 | 51/50 道题 | 提交 | 失败 / 成功 |  |
| AC-172-03 | TC-INT-469[AC] | INT | 本地自动 | 新写 | 选项 1/11/2/10 | 提交 | 失败 / 成功 |  |
| AC-172-04 | TC-INT-469[AC]、TC-E2E-316[J] | INT+E2E | 本地自动 | 新写 | 截止距现在 59/60 分钟 | 发起 | 失败 / 成功（半数决议同） |  |
| AC-173-01 | TC-INT-470[AC]、TC-E2E-323[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 收入文件 5000/5001 行 | 导入 | 接受 / 整份拒绝"文件行数超过 5000" | 远程只验证限值常量 |
| AC-173-02 | TC-INT-470[AC] | INT | 本地自动 | 新写 | 逐条 500/501 | 提交 | 成功 / 拒绝 |  |
| AC-174-01 | TC-INT-472[AC] | INT | 本地自动 | 新写 | 任期开始日早于今天 | 赋予席位 | 拒绝 |  |
| AC-174-02 | TC-INT-473[AC] | INT | 本地自动 | 新写 | 发生日期晚于今日/今日 | 提交报销 | 拒绝 / 成功 |  |
| AC-174-03 | TC-INT-473[AC] | INT | 本地自动 | 新写 | 核销日期 ≤ 今日 | 提交备用金 | 拒绝；明日成功 |  |
| AC-174-04 | TC-INT-474[AC] | INT | 本地自动 | 新写 | 核销关联 51/50 张 | 提交 | 拒绝 / 通过数量校验 |  |
| AC-174-05 | TC-INT-475[AC]、TC-INT-426[AC] | INT | 本地自动 | 新写 | 已有待审申诉/申请 | 再提交 | 409 不新增 |  |
| AC-175-01 | TC-INT-476[AC]、TC-E2E-317[J]、TC-E2E-329[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 管理员下载 xlsx 模板 | 原样预检 | 6 行 / 0 失败 / 4 个新专有部分，只读 | 远程：imported+updated=4（测试环境清册已有真实数据） |
| AC-175-02 | TC-E2E-317[J]、TC-INT-311[X311] | E2E+INT | 本地自动 | 修改(现有)、新写 | 同一模板本地正式导入 | 导入 | 6/0/4，与预检一致 |  |
| AC-175-03 | TC-INT-311[X311] | INT | 本地自动 | 修改(现有) | 既有 TC-INT-311 | 更新断言 | 6 行、0 失败、新增 4 个，通过 | 引用 REQ-FUNC-166、admin_polish REQ-FUNC-129、AC-138-02/03 |
| AC-176-01 | TC-INT-478[REQ] | INT | 本地自动 | 新写 | 全仓需求文档 | 扫描定义行 | 重复定义数 0 | 文档类 |
| AC-176-02 | TC-INT-479[REQ] | INT | 本地自动 | 新写 | user_directory 两文档 | 看开头 | 对照表齐全，与 admin_polish 不重复并衔接本批 | 文档类 |
| AC-176-03 | TC-INT-480[REQ] | INT | 本地自动 | 新写 | ui_theme/registry/content 的同号约束 | 看文档 | 批次前缀注记，重复约束组数 2 | 文档类 |
| AC-177-01 | TC-INT-481[REQ] | INT | 本地自动 | 新写 | ui_theme REQ-FUNC-076/US-082/C-23 | 查看 | "已被 admin_polish REQ-FUNC-135 替代"，原文在 | 文档类 |
| AC-177-02 | TC-INT-482[REQ] | INT | 本地自动 | 新写 | registry AC-098-01/05/06，ocap AC-019-08/AC-004-01/02 | 查看 | 指向性注记，原文在 | 文档类 |
| AC-177-03 | TC-INT-483[REQ] | INT | 本地自动 | 新写 | ocap REQ-FUNC-008/US-008 | 查看 | "跳转微信授权页扫码登录，不内嵌二维码" | 文档类 |
| AC-177-04 | TC-INT-484[REQ] | INT | 本地自动 | 新写 | user_directory REQ-FUNC-140；ocap C-14/AC-049-06/AC-055-04 | 查看 | 现行描述与修正原因；指向 REQ-FUNC-161/163 | 文档类 |
| AC-177-05 | TC-INT-485[REQ] | INT | 本地自动 | 新写 | 被改文档 | 检查文件头/文末 | 版本升、状态 DRAFT/APPROVED、修订记录；原文只允许纯插入（对比 afa1fe8） | 文档类 |
| AC-060-04 | TC-INT-540[RW1]、TC-INT-510[GAP]、TC-INT-514[GAP]、TC-UNIT-584[RW1] | INT+UNIT | 本地自动 | 新写、新写(回流 1) | 已生效收入表 | 原审批人（含流程指定的另一位）作废 | VOID，审计含操作人，报表不再计入，重复作废 409 | Q109=B |
| AC-060-10 | TC-INT-539[RW1]、TC-INT-541[RW1]、TC-INT-514[GAP]、TC-UNIT-584[RW1]、TC-UNIT-585[RW1] | INT+UNIT | 本地自动 | 新写、新写(回流 1) | 其他委员/录入人/管理员各用独立已生效数据 | 尝试作废 | 403（管理员 401/403），保持已生效且仍计入报表；原审批人成功；列表 can_void 与之一致；Web 仅 can_void 行有按钮；DENIED 审计（CR-008 额外行为，固化观察） | DEF-019 关闭 |
| AC-064-09 | TC-INT-540[RW1] | INT | 本地自动 | 新写(回流 1) | 作废完成 | 查审计 | INCOME_VOIDED/SUCCESS，操作人为原审批人 | |
| AC-040-08 / AC-064-06 | TC-INT-512[GAP]、TC-INT-542[RW1] | INT | 本地自动 | 新写、新写(回流 1) | 非法人数上限 | PUT 配置 | 400，新增 1 条 FAILURE 审计（操作人、detail.field），配置不变；合法保存仍写 SUCCESS | DEF-017 关闭 |
| AC-066-05 / AC-064-08 | TC-INT-513[GAP]、TC-INT-543[RW1] | INT | 本地自动 | 新写、新写(回流 1) | 合并使委员/业主代表席位失效 | 查审计 | 各 1 条 SEAT_INVALIDATED（object_id=被取代席位，reason=ACCOUNT_MERGED）；保留席位无失效审计 | DEF-018 关闭 |
| REQ-FUNC-158（AC-167-03 的扩展范围） | TC-UNIT-579 ~ 583[RW1]、TC-UNIT-586[RW1]、TC-UNIT-587[RW1]、TC-UNIT-588 ~ 589[RW1]、TC-UNIT-590 ~ 601[RW2]、TC-INT-545[RW2] | UNIT+INT | 本地自动 | 新写(回流 1、回流 2) | 管理端审批流程/财务/审计/席位关系/内容列表/保存历史，用户端待办/首页待办/决议详情/收入表/信息公开/信息详情 | 渲染页面 | 类别、方式、状态中文；时间"年-月-日 时:分"（审计列含秒，见 OBS-9）；布尔"是/否"；无内部代码；adminText 映射键 = 后端枚举、值为中文 | 全部通过；DEF-020/021/022 关闭 |
| AC-178-01 | 全量回归 | 回归 | 本地自动 | 新写 | 改动前基线 | 运行三套测试 | 除 TC-INT-311 外零新增失败，新写用例全部通过 | 回流 2 后：后端 712 OK（TC-INT-311 已通过）、前端 244/244、小程序 94/94，新增失败 0 |
| AC-178-02 | TC-INT-486[CON]、TC-INT-487[CON]、TC-INT-488[CON]、TC-INT-489[CON]、TC-INT-490[CON]、TC-INT-491[CON]、TC-INT-492[CON]、TC-INT-493[CON]、TC-INT-494[CON]、TC-INT-495[CON]、TC-INT-496[CON]、TC-INT-544[RW2]、TC-INT-545[RW2]、契约-1/2/3/4[CON] | INT | 本地自动 | 新写、现有 | 前端调用清单 | 解析路径+方法并对照后端路由 | 无法对应数 = 0；字段级一致 |  |
| AC-178-03 | TC-INT-477[AC]、TC-E2E-343[J]、TC-E2E-320[R] | INT+E2E | 本地自动；远程 HTTP | 新写 | 部署后测试环境 e2e_ 用户 | 登录、决议列表、我的房屋、个人中心 | 均 200，既有字段齐全 | 本地对应 + 远程 |

**位置键**

| 键 | 文件 |
|---|---|
| AC | `backend/tests/integration/test_product_review_ac.py` |
| API | `backend/tests/integration/test_product_review_api.py` |
| FX | `backend/tests/integration/test_e2e_fixture_command.py` |
| RULE | `backend/tests/unit/test_product_review_rules.py` |
| CON | `backend/tests/integration/test_frontend_contract.py` |
| J | `backend/tests/e2e/test_product_review_journeys.py` |
| C | `backend/tests/e2e/test_product_review_content.py` |
| REQ | `backend/tests/integration/test_requirements_numbering.py` |
| GAP | `backend/tests/integration/test_product_review_gap_stories.py` |
| MIG | `backend/tests/integration/test_migration_residency_0002.py` |
| WUI | `frontend/tests/product_review_ui.spec.js` |
| WCORE | `frontend/tests/product_review_core.spec.js` |
| RW2 | 回流 2 新增：`backend/tests/integration/test_product_review_rework2.py`（TC-INT-544 ~ 545）、`frontend/tests/product_review_rework2.spec.js`（TC-UNIT-590 ~ 601） |
| RW1 | 回流 1 新增：`backend/tests/integration/test_product_review_rework1.py`（TC-INT-539 ~ 543）、`frontend/tests/product_review_rework1.spec.js`（TC-UNIT-579 ~ 589） |
| MUI | `miniprogram/tests/product_review_ui.spec.js` |
| MCORE | `miniprogram/tests/product_review_core.spec.js` |
| R | `backend/tests/remote/remote_cases.py` |
| X311 | `backend/tests/integration/test_registry_import_xlsx_defects.py` |


AC 总数：120 行（0.1.0 的 114 行 + 回流 1 新增 6 行；回流 2 未新增 AC 行，只扩充 REQ-FUNC-158 与 AC-178-02 行的用例；含 GR-C-001-F03 核对 1 行、AC-178-01 全量回归 1 行）覆盖 US-150 ~ 178 的全部 AC；每个 AC 至少 1 个已真实执行的用例（远程用例本阶段不执行，不作为覆盖依据）。

## 回流 1 变更说明（0.2.0）

- **既有用例调整（均为 GROUP_C 在回流 1 中按 AC-060-04/10 做的，非本阶段修改；我逐条核对依据与不放宽）**：`test_finance_polls_api.py::IncomeTests::test_submit_approve_and_void`（录入人作废由 200 改为 403 FORBIDDEN 且保持 EFFECTIVE，新增原审批人作废 200）；`tests/e2e/test_rework_journeys.py::IncomeManualEntryJourneyTests::test_manual_entry_submit_approve_report_then_void`（作废人由录入人改为原审批人）。依据：user_stories AC-060-04/AC-060-10（Q109=B）；断言只收紧、未放宽。**我未修改任何 0.1.0 已冻结用例**（`product_review_*` 各文件修改时间均早于 0.1.0 报告 08:37）。
- **TC-INT-514 补充**：TC-INT-514 保持原样（现已通过）；其未断言"原审批人成功"，由 TC-INT-539/540 补；P-TE-008 做法（每个非授权角色各自独立数据）已用于 TC-INT-539。
- **GR-C-002-F01 结论（TC-UNIT-561 的设计意图）**：TC-UNIT-561 守护的是 ADR-092 的"`*_LABELS` 两端键值一致"——小程序与 Web 共享的角色/状态映射。`FLOW_SCOPE_TEXT`、`APPROVAL_MODE_TEXT`、`INCOME_STATUS_TEXT` 对应 Web 专有页面（管理端审批流程、Web 收入表）；小程序没有这些页面（`miniprogram/utils/labels.js` 无同名表），REQ-FUNC-158 只约束 Web 用户端与管理端。因此**不属于该检查应覆盖的范围，不判为命名规避缺陷**。但原检查只靠 `_LABELS` 后缀识别，新增 Web 专有表会被静默排除，故新增 TC-UNIT-588：非 `_LABELS` 导出恰为这三个、小程序不含、键与后端模型枚举一致，TC-UNIT-589：取值为中文。观察项：小程序 `resolutions/index.vue` 自带 `modeText`（"半数同意/指定负责人"），与 Web 的"半数人员同意/指定负责人审批"措辞不一致，不违反 AC。
- **远程 HTTP 套件（`backend/tests/remote/`）**：回流 1 的修复不影响其用例（作废、committee 配置审计、合并审计不在 22 条之内；审批流程创建用例不检查列表显示），故未改动套件（文件修改时间 08:13 之前），未重跑本地自检；状态仍 BLOCKED（待 E2）。

## 回流 2 变更说明（0.3.0）

- **冻结规则**：未修改任何已冻结用例断言；新增均放在新文件（`product_review_rework2.spec.js`、`test_product_review_rework2.py`），文件修改时间晚于 0.2.0 但早于本版报告。
- **DEF-021/022 关闭**：TC-UNIT-586/587 在 GROUP_C-005 修复后通过；另增 TC-UNIT-596 验证 Tasks 标题回退。
- **回流 2 另修 8 处的覆盖**：InfoDetail（TC-UNIT-590）、AdminAudit（591）、AdminFinance（592）、AdminMemberships（593）、AdminContentPosts（594）、AdminContentEditor 保存历史（595）、Tasks 标题回退（596）；变异检验（页面还原为 `git show HEAD`）8 条失败。
- **GR-C-003 condition（adminText 守护）**：TC-UNIT-597（导出集合恰为 4 张）、598（键 = 后端模型枚举：Claim.TYPES/STATUSES、AuditLog.ACTOR_TYPES/RESULTS，期望来自模型常量）、599（值为中文）、600（页面实际使用）、601（登记范围守护，防新枚举映射逃出检查）；TC-INT-545 用真实响应核对枚举值落在映射键内。
- **TC-UNIT-588 是否纳入 adminText.js**：评估结论为**不纳入**，也不改冻结用例（理由见单元报告"TC-UNIT-588 评估"）；缺口由 597 ~ 601 补上。
- **字段级契约（含 can_void）**：TC-INT-544、545 已执行通过。
- **远程 HTTP 套件**：回流 1/2 的修复不影响其 22 条用例（不调用收入表接口、不检查页面文本），套件文件未改；已按 PM 指令 5 在回流 2 之后的产品代码上重做本地自检（runserver + 临时 SQLite，连续两遍 `Ran 22 tests ... OK (skipped=2)`，cleanup 后 e2e 计数全 0、清册计数不变），结果与 E2 执行清单见 e2e 报告；状态仍 BLOCKED（待 E2）。
- **Must Have 故事覆盖**：未变，US-178 增加 TC-INT-544、545（见下表）。

## 测试数据需求

- 本地：全部由工厂函数 `make_owner / make_unit / make_seat / make_flow / make_admin` 与 `Attachment` 行现造；PNG 头 + 随机字节作为附件；报表用 `LedgerReport` 直接造 detail；版式模板/内容走 API 创建。无 `[DATA_REQUIRED]`。
- 迁移用例：系统临时目录的 SQLite 文件库，用例结束即删除。
- 远程（E2 执行前置）：`OCAP_E2E_FIXTURE=1 OCAP_E2E_PASSWORD=<密码，不入文档> python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25`；账号命名与手机号段见 `module_design.md` MOD-081。
- `[DATA_REQUIRED: 测试环境中至少有 1 份已生成的季度/年度报表]` —— TC-E2E-328（AC-168-01）；没有报表时该用例 SKIP 并写原因。
- `[DATA_REQUIRED: 第 4 个无产权业主的空闲专有部分 id（夹具 --units 4）]` —— 远程验证 AC-150-02；本地已覆盖（TC-INT-425），远程不测。

## 不可测项

| AC | 原因 |
|---|---|
| AC-176-01 ~ 03、AC-177-01 ~ 05 | 文档类，用户故事已声明不适用 [E2E]；已由集成层文档扫描用例执行（TC-INT-478 ~ 485） |
| 视觉类（三套风格逐页观感、动效、窄屏断点、首屏闪烁） | 无浏览器环境，见人工验证清单 |
| 小程序 `uni build -p mp-weixin`、微信开发者工具真机行为 | 开发机 uni alpha 工具链无法构建（GR-C-001-F02），[NOT_TESTABLE: 环境]，见人工验证清单 |
| AC-155-01 的"真实 31 分钟等待"（远程） | 慢用例，默认 SKIP（`OCAP_E2E_SLOW=1` 才运行）；本地用时钟控制代替（TC-INT-439、TC-E2E-315），不计入不可测分母 |
| AC-164-01/02 在测试环境的注销流程 | 需要短信验证码（console 替身），P4-1 要求远程不测需要验证码的流程；本地已覆盖（TC-INT-459、TC-E2E-311） |

## 故事覆盖核对

Must Have 共 15 个：US-150 ~ 162（13）、US-176、US-178。每行列出已真实执行的用例（本地，通过）。远程用例（TC-E2E-320 ~ 341）本阶段 BLOCKED，不计入。

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-150 | TC-INT-424 ~ 426；TC-UNIT-522、523、551、573；TC-E2E-309 | 集成 / 单元 / E2E |
| US-151 | TC-INT-427 ~ 430；TC-UNIT-529、552、555、566；TC-E2E-309 | 集成 / 单元 / E2E |
| US-152 | TC-INT-431；TC-UNIT-527、552；TC-E2E-309 | 集成 / 单元 / E2E |
| US-153 | TC-INT-432 ~ 434；TC-UNIT-525、526、553、562、572；TC-E2E-309 | 集成 / 单元 / E2E |
| US-154 | TC-INT-435 ~ 437、522；TC-UNIT-556、564、565、575、576、577；TC-E2E-312 | 集成 / 单元 / E2E |
| US-155 | TC-INT-438、439、527 ~ 529；TC-UNIT-510、511；TC-E2E-315 | 集成 / 单元 / E2E |
| US-156 | TC-INT-440；TC-UNIT-527、554、572；TC-E2E-310 | 集成 / 单元 / E2E |
| US-157 | TC-INT-441 ~ 444、488、489、517、518；TC-UNIT-512 ~ 514、530、550、557；TC-E2E-310 | 集成 / 单元 / E2E |
| US-158 | TC-INT-444；TC-UNIT-525、526、534、540、542、548、562；TC-E2E-310 | 集成 / 单元 / E2E |
| US-159 | TC-INT-445 ~ 448、494；TC-UNIT-541、549、578；TC-E2E-313 | 集成 / 单元 / E2E |
| US-160 | TC-INT-449、450；TC-UNIT-543、544；TC-E2E-313 | 集成 / 单元 / E2E |
| US-161 | TC-INT-451、452、496；TC-UNIT-539、558、559、563、571；TC-E2E-342 | 集成 / 单元 / E2E |
| US-162 | TC-INT-453 ~ 457、492、530；TC-UNIT-545、546；TC-E2E-314、318、319 | 集成 / 单元 / E2E |
| US-176 | TC-INT-478 ~ 480 | 集成（文档类，E2E 不适用） |
| US-178 | TC-INT-477、486 ~ 496、544、545、契约-1/2/3/4；TC-E2E-343；全量回归（三套） | 集成 / E2E / 回归 |

Should Have 故事（US-163 ~ 175、177）的执行用例见"AC 映射"表，同样每个 AC 至少 1 个已执行用例。
