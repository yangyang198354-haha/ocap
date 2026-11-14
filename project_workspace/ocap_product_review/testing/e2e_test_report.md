<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T09:45:35+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>phase_status.md</file><file>testing/test_plan.md</file><file>testing/unit_test_report.md</file><file>testing/integration_test_report.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告：产品评审修正（0.3.0）

## 摘要

critical path 口径：替代（本地 HTTP API 多步旅程 `tests.e2e` TC-E2E-309 ~ 319、342、343 + jsdom 页面用例；项目没有浏览器 E2E 框架。远程 HTTP 旅程 TC-E2E-320 ~ 341 已编写并经本地自检，待 E2 执行）

> 0.3.0（缺陷回流 2/2 后的最终重测）。上一层（集成）门控 PASSED，本层按 baseline 模式执行。

- 执行时间：2026-11-14T09:40:41 ~ 09:42（+08:00，最后一次执行）；环境同集成层（SQLite 内存库、`apps/integrations/fakes.py` 替身，不连测试机与外网）。
- 命令：`(cd backend && $PY manage.py test tests.e2e --settings=config.test_settings)`、`tests.smoke`、全量回归（见下）。
- total = pass + fail + skip + blocked + not_testable = 53 = 53 + 0 + 0 + 0 + 0（本地 E2E 47 + 冒烟 6；远程套件 22 条 BLOCKED 单列，不计入本层 total，见"远程 HTTP E2E 套件"）。
- 通过率 = pass / (pass + fail + blocked) = 53 / 53 = 1.0000
- critical path 覆盖率 = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = 14 / 14 = 1.00（Must Have 共 15：US-150 ~ 162、US-176、US-178；US-176 为文档编号类故事，用户故事声明 [E2E] 不适用，列为 NOT_TESTABLE（E2E），已由集成层 TC-INT-478 ~ 480 真实执行；若把 US-176 计入分母则为 14 / 15 = 0.93，口径已在此写明）。
- critical path 通过率 = 10 / 10 = 1.00（Must Have 故事关联的本地 E2E 旅程：TC-E2E-309、310、312、313、314、315、318、319、342、343，全部 PASS；覆盖 US-150 ~ 162、178）。
- 判定模式：baseline；E2E 覆盖前后端契约（契约用例在集成层 TC-INT-486 ~ 496、544、545 与契约-1 ~ 4，全部通过）。
- **本层门控：PASSED**（零新增失败；critical path 覆盖 14/14、通过 10/10 = 1.00；全量回归新增失败 0）。

## 全量回归

```
$ (cd backend && $PY manage.py test tests.e2e --settings=config.test_settings)
Ran 47 tests in 16.544s
OK
$ (cd backend && $PY manage.py test tests.smoke --settings=config.test_settings)
Ran 6 tests in 0.242s
OK
$ (cd backend && $PY manage.py test --settings=config.test_settings)
Ran 712 tests in 53.871s
OK
$ (cd frontend && npx vitest run --passWithNoTests)
 Test Files  23 passed (23)
      Tests  244 passed (244)
$ (cd miniprogram && npx vitest run --passWithNoTests)
 Test Files  13 passed (13)
      Tests  94 passed (94)
```

后端 712 = unit 162 + integration 497 + e2e 47 + smoke 6；`manage.py check` → `System check identified no issues (0 silenced).`；`makemigrations --check --dry-run` → `No changes detected`；`compileall -q backend` 退出 0。

| 套件 | 基线（GROUP_C-005 后 PM 复跑） | 本次 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | 710 OK | 712 OK（+2 新写 TC-INT-544、545） | 0 |
| 前端 vitest | 232 / 232 | 244 / 244（+12 新写 TC-UNIT-590 ~ 601） | 0 |
| 小程序 vitest | 94 / 94 | 94 / 94 | 0 |

画像 P4 登记的既有失败 TC-INT-311 已通过；相对基线新增失败逐条列出：无。

## 用户旅程

以下为本地 HTTP API 多步旅程（Django test client，真实认证头、真实视图与数据库，仅外部服务替身）。每条旅程的步骤即用例 docstring 所述顺序，全部断言在同一用例内；用例文件在本版未改动（修改时间均早于 0.1.0 报告），本次全部真实重跑，结果取自 `-v 2` 输出（13 个 product_review 旅程 `Ran 13 tests ... OK`）。

### TC-E2E-309: 逐级选房申请同住人 → 审批 → 移除 → 退出
- 关联：US-150、151、152、153 / AC-150-01、151-01/02、152-01/02、153-01/02；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 申请人逐级选房并提交申请 | 201，待审批 | 同期望 | PASS |
| 2 | 产权业主打开首页/审批列表 | 计数与列表一致，手机号脱敏 | 同期望 | PASS |
| 3 | 业主拒绝 → 申请人看到"已拒绝" → 再次申请 | 新记录；重复提交被拒（409） | 同期望 | PASS |
| 4 | 业主通过 → 业主移除同住人 → 再申请通过 → 同住人退出 | 身份解除，回到游客 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-310: 申诉驳回 → 再申诉通过 → 三处身份一致 → 撤销认证
- 关联：US-156、157、158 / AC-156-01 ~ 04、157-01、157-04、158-02；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 提交申诉，管理员驳回并填原因 | 用户端状态"已驳回"+原因原文 | 同期望 | PASS |
| 2 | 再申诉，管理员通过 | 状态"已通过"，身份出现 | 同期望 | PASS |
| 3 | 个人中心/我的房屋/管理端目录三处身份 | 汇总身份一致 | 同期望 | PASS |
| 4 | 管理员撤销认证 | 用户无身份；审计新增 1 条 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-312: 非成员被拒 → 委员发起报销 → 审批 → 报表明细 → 上限变更
- 关联：US-154、168、170 / AC-154-01/02、168-01、170-01/03；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 非成员发起报销 | 403，含"业委会成员" | 同期望 | PASS |
| 2 | 委员发起并审批通过，生成季度报表 | 201；报表明细与合计，支出事由为空 | 同期望 | PASS |
| 3 | 管理员把上限改为 500000，再提交 500000.01 / 500000.00 | 失败并提示当前上限 / 成功；旧记录不变 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-313: 用户搜索 → 赋予席位 → 配置审批人 → 翻页
- 关联：US-159、160 / AC-159-01/03/05/06、160-01；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理员按手机号后四位搜索；选游客赋予席位 | 命中；422 NOT_AN_OWNER | 同期望 | PASS |
| 2 | 选产权业主赋予委员；流程添加该席位持有者为审批人 | 成功 | 同期望 | PASS |
| 3 | 非管理员搜索 | 403 | 同期望 | PASS |
| 4 | 席位与账号列表翻页 | 总数一致，合计无重复 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-314 / 318 / 319: 版式模板管理（新建、选用、改样式、被引用删除被拒、内置不可改）
- 关联：US-162、169、113 / AC-162-01 ~ 05、169-01、113-01/03/04；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 新建模板 → 内容选用并发布 → 预览样式值逐项一致 | 成功 | 同期望 | PASS |
| 2 | 改名改样式；已发布内容立即按新样式渲染 | 新值生效 | 同期望 | PASS |
| 3 | 删除被引用模板 | 409，提示引用 1 条，保留 | 同期望 | PASS |
| 4 | 内容下线 → 用户端 404 → 删内容 → 删模板成功；内置模板 PUT/DELETE | 404；成功；404 | 同期望 | PASS |
- 结论：PASS（314、318、319 三条均 PASS）

### TC-E2E-315: 小程序账号密码登录 7 天会话
- 关联：US-155 / AC-155-01/02；环境：本地（可控时钟）。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 小程序账号密码登录 | 200 | 同期望 | PASS |
| 2 | 闲置 31 分钟、6 天 23 小时后访问 | 仍成功 | 同期望 | PASS |
| 3 | 满 7 天后访问 | 401 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-342: 公开决议列表分页
- 关联：US-161 / AC-161-01、04；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 45 条决议翻 3 页 | 20 / 20 / 5，合计 45 无重复，每页带总数 | 同期望 | PASS |
| 2 | 删到 15 条；小程序"加载更多"语义连续翻页 | 仅 1 页；结果同上 | 同期望 | PASS |
- 结论：PASS

### TC-E2E-343: 既有用户流程不变（零回归）
- 关联：US-178 / AC-178-03 的本地对应；环境：本地。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 登录、决议列表、我的房屋、个人中心 | 全部 200，既有字段齐全、含义不变 | 同期望 | PASS |
- 结论：PASS

### 其他本地旅程（非 Must Have 故事，均 PASS）
TC-E2E-311（US-164 注销关闭待处理项）、316（US-171/172 半数决议分母与窗口）、317（US-175 导入模板预检与导入一致）。

## 远程 HTTP E2E 套件（画像 P4-1；状态仍 BLOCKED，待 E2）

- 套件：`backend/tests/remote/{remote_client,remote_cases,run_remote}.py`，TC-E2E-320 ~ 341，22 条；用例文件本版**未修改**（修改时间 08:13 及更早）。
- 回流 1/2 的修复是否影响其用例：回流 1（收入表作废仅原审批人、`can_void`、committee 配置失败审计、合并席位失效审计）与回流 2（Web 页面中文与时间格式）均不在 22 条用例的断言与 `WRITE_ALLOWLIST` 内：套件不调用收入表接口，不检查前端页面文本；`/admin/approval/flows` 用例只检查创建与权限，不检查列表显示。因此无需改动，用例编号与计数不变。
- **本地自检（针对回流 1/2 之后的产品代码，runserver + 临时 SQLite，PM 指令 5）**：2026-11-14T09:33 ~ 09:36，`config.test_settings` 的派生设置（scratchpad 内，文件库 SQLite；`migrate --run-syncdb`；预置 5 个住宅清册行与实名/手机号），`manage.py runserver 127.0.0.1:18765 --noreload`，`OCAP_E2E_ALLOW_LOCAL=1` 指向回环地址；`e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25` 后连续运行两遍：

```
== run 1
.................s...s
Ran 22 tests in 9.400s
OK (skipped=2)
== run 2
.................s...s
Ran 22 tests in 8.204s
OK (skipped=2)
```
  跳过的 2 条为 TC-E2E-328（本地无已生成报表）与 TC-E2E-332（慢用例，未设 `OCAP_E2E_SLOW`）。第二遍通过说明用例自行恢复数据（可重复运行）。`e2e_fixture status` 在两遍之后：e2e 用户 35、管理员 1、claims 2、resolutions 25 等；`cleanup --execute` 之后各项均为 0；`registry_counts` 全程不变（RegistryUnit/Owner/Phone = 5/5/5），未改动清册。服务器已停止，临时库保留在 scratchpad（不入库）。
- 状态：22 条仍 BLOCKED（待 E2 在用户授权后部署并对公开入口执行；本阶段不连接测试机与外网）；总计 22 = 0 + 0 + 0 + 22 + 0。

### E2 执行清单（完整）

前置条件：部署的版本含 `e2e_fixture` 命令与迁移 `residency/0002_closed_status`；测试环境已导入业主清册，且至少 3 个"住宅类、无有效房屋关系、无待审申诉/同住人申请"的专有部分（夹具只读选房，不写清册；不足时 setup 报"可选房屋不足"）。凭据只写变量名，值由 E2 自行生成并保管，不入文档与日志。

| 步骤 | 位置 | 命令 / 说明 |
|---|---|---|
| 1 夹具 setup | 测试机 `/home/yangyang/ocap/backend`（E2 经 SSH 执行；测试代码本身只走公开入口） | `OCAP_E2E_FIXTURE=1 OCAP_E2E_PASSWORD=<密码> python manage.py e2e_fixture setup --units 3 --bulk-users 25 --bulk-resolutions 25`（输出 JSON，含 user/unit 清单与 `registry_counts`；记下 `registry_counts` 作为后续比对基线） |
| 2 状态核对 | 同上 | `OCAP_E2E_FIXTURE=1 python manage.py e2e_fixture status` |
| 3 运行 | 任意开发机（只需 `requests`，不依赖 Django） | `OCAP_E2E_BASE_URL=https://ai-freeark.xin/ocap/ OCAP_E2E_PASSWORD=<同上> python backend/tests/remote/run_remote.py -v` |
| 4 慢用例（可选） | 同上 | 另设 `OCAP_E2E_SLOW=1`（TC-E2E-332 等待约 31 分钟，对应人工清单 H-7） |
| 5 清理 | 测试机 | 先 dry-run：`OCAP_E2E_FIXTURE=1 python manage.py e2e_fixture cleanup`，核对 would_delete 仅为 `e2e_` 数据；再 `OCAP_E2E_FIXTURE=1 python manage.py e2e_fixture cleanup --execute` |
| 6 清理验收 | 测试机 | `e2e_fixture status`：所有 e2e 计数为 0，`registry_counts` 与步骤 1 相同，`claim_amount_max` 仍为 `1000000.00`（未被改动） |

- 环境变量名：`OCAP_E2E_FIXTURE`（夹具命令门控，=1）、`OCAP_E2E_PASSWORD`（夹具与测试共用密码，须符合账号密码规则）、`OCAP_E2E_BASE_URL`（仅允许 `https://ai-freeark.xin/…`）、`OCAP_E2E_SLOW`（可选，=1 运行慢用例）。`OCAP_E2E_ALLOW_LOCAL` 仅本地自检用，**远程执行不要设置**。
- 预期计数：`Ran 22 tests`；20 条通过、0 失败、`OK (skipped=2)`：TC-E2E-328 因测试环境无已生成报表而 SKIP（若已有则通过，计 21 通过、skipped=1），TC-E2E-332 为慢用例默认 SKIP（设 `OCAP_E2E_SLOW=1` 则运行）。退出码 0 全过 / 1 有失败 / 2 缺环境变量或目标被护栏拒绝（未发出任何请求）。
- 护栏：目标主机非 `ai-freeark.xin`、任何未登记的写请求、写有效的 `claim.amount_max`（只允许非法值负例）、`registry/import` 非 `dry_run=1` 均在发出前抛 GuardError；只使用 `e2e_` 账号；GET 以外的请求只在 `WRITE_ALLOWLIST` 内。
- 失败时的清理步骤：无论成功与否都执行步骤 5、6；若中途中断（网络/SSH 断开）先 `status` 查看残留，再 `cleanup`（dry-run）→ `cleanup --execute`；清理后 `registry_counts` 与步骤 1 不一致或出现非 `e2e_` 数据变化时，立即停止并上报（不得自行修复清册）。失败用例的现象、HTTP 状态与路径记入 deployment_report，缺陷回流 GROUP_C。
- 数据依赖：`[DATA_REQUIRED: 测试环境至少有 1 份已生成的季度/年度报表]`（TC-E2E-328，否则 SKIP）；`[DATA_REQUIRED: 第 4 个无产权业主的空闲专有部分 id]`（AC-150-02 远程不测，本地 TC-INT-425 已覆盖，见 H-6）。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 | 状态 |
|---|---|---|---|---|---|
| DEF-017 | MINOR | 配置保存失败无失败审计 | TC-INT-512、542 | `backend/apps/committee/views.py:AdminCommitteeConfigView.put` | 已关闭（0.3.0 复跑通过） |
| DEF-018 | MINOR | 合并使席位失效无审计 | TC-INT-513、543 | `backend/apps/committee/services.py:merge_seats` | 已关闭 |
| DEF-019 | MAJOR | 已生效收入表可被非原审批人作废 | TC-INT-514、539 ~ 541、544、TC-UNIT-584/585 | `backend/apps/income/services.py:void_sheet`、`views.py` | 已关闭 |
| DEF-020 | MINOR | 审批流程列表等显示内部代码（REQ-FUNC-158） | TC-UNIT-579 ~ 583 | `frontend/src/admin/AdminFlows.vue` 等 5 处 | 已关闭 |
| DEF-021 | MINOR | 首页待办卡片显示 `EXPENSE` 与 ISO 时间 | TC-UNIT-586、596 | `frontend/src/portal/Home.vue:27-28`、`Tasks.vue:16` | 已关闭（回流 2 修复，TC-UNIT-586 PASS） |
| DEF-022 | MINOR | 决议详情"表决截止"显示 ISO 时间 | TC-UNIT-587 | `frontend/src/portal/ResolutionDetail.vue:7` | 已关闭（TC-UNIT-587 PASS） |

本轮新缺陷：无（未新增 DEF-023）。

## 观察项（更新）

- OBS-1、OBS-2、OBS-3、OBS-5、OBS-6：同 0.1.0，未变化。OBS-4 已关闭。OBS-7（小程序 `modeText` 与 Web 措辞不一致）、OBS-8（作废被拒写 DENIED 审计为需求之外的额外行为，TC-INT-541 固化现状）：未变化。
- OBS-9（新增）：AdminAudit 时间列含秒（`datetime()`），REQ-FUNC-158 写"统一为年-月-日 时:分"；开发在回流 2 命中清单中说明"审计需要秒"，满足 AC-167-02 的形式（无 T、无时区），未判缺陷，建议用户确认是否接受。
- OBS-10（新增）：AdminFinance 筛选下拉"通过/拒绝"与表格列"已通过/未通过"措辞不统一；审计主体/结果与报销状态的中文措辞为开发自拟（GR-C-003-F02），待用户确认。

## 人工验证清单

沿用 0.2.0 的 H-1 ~ H-9（内容未变；回流 2 新增的页面级中文与时间格式由 TC-UNIT-579 ~ 596 覆盖，不新增人工项）：

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| H-1 | US-150 ~ 157、161 的小程序 AC（AC-150-04、151-05、152-04、153-05、156-05、157、161-03） | 用微信开发者工具或真机打开体验版，走一遍"我的房屋→申请同住人→业主审批→移除/退出"，首页待审批提示，决议列表加载更多 | 与 Web 相同的数据、状态与中文显示；无内部编号输入框 | 微信开发者工具或真机；小程序构建产物（`uni build`，GR-C-001-F02 未验证） | 是 |
| H-2 | AC-153-04、158-01/03/04（界面确认弹窗） | 浏览器中逐页点击 撤销认证/席位、删除专有部分/流程、作废/撤回收入表与决议、移除/退出同住人、注销账号，各点一次"取消"、一次"确认" | 取消不变更；弹窗写明后果 | Chrome/Edge；测试环境 | 是（US-153、158 为 Must Have） |
| H-3 | ui_theme 视觉类 AC | 三套风格各打开用户端与管理端主要页面，窄屏与桌面各看一遍 | 无明显错位、对比度可读、首屏无错误风格闪烁 | 浏览器 + 手机；测试环境 | 否 |
| H-4 | AC-164-01/02 的测试环境注销流程 | 用 e2e_ 之外的专用测试账号提交同住人申请与申诉后注销（验证码由 E2 从服务日志只读获取） | 业主与管理员待办清空；记录关闭 | 测试环境 + E2 读取日志 | 否 |
| H-5 | AC-170-01 写全局配置步骤 | 经用户授权后在管理端改上限并测后恢复 | 超限被拒、恢复默认 | 测试环境 + 用户授权 | 否 |
| H-6 | AC-150-02（远程） | 夹具 `--units 4`，用第 4 个空闲房屋验证"暂无产权业主"拒绝 | 409 UNIT_HAS_NO_OWNER | 测试环境 + E2 提供空闲房屋 id | 否 |
| H-7 | AC-155-01（31 分钟慢用例） | `OCAP_E2E_SLOW=1` 运行 TC-E2E-332 | miniapp 会话 200，Web 会话 401 | 测试环境，约 31 分钟 | 否 |
| H-8 | AC-168-01（远程） | 测试环境至少有 1 份已生成报表后运行 TC-E2E-328 | 明细合计与列表一致、支出事由为空 | 测试环境 | 否 |
| H-9 | AC-060-10 / DEF-019 | 以非原审批人的业委会成员登录 Web 收入表页，查看已生效收入表；再以原审批人登录 | 非原审批人看不到"作废"按钮；原审批人有按钮，点击后须确认 | 浏览器；测试环境（需两位成员账号） | 否（本地 TC-INT-539 ~ 541、544、TC-UNIT-584 已覆盖） |
