<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T19:10:55+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/integration_test_report.md</file>
    <file>development/implementation_plan.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（ocap_owner_auth_v2，INCREMENTAL / baseline）

## 摘要

critical path 口径：替代（后端多步 HTTP 旅程：真实令牌与权限、管理命令 `relocate_shops`/`export_registry_import_file`、真实批量导入接口 `/admin/registry/import?dry_run=1`；前端/小程序用 vitest + jsdom 组件测试补充；前后端契约由 `test_frontend_contract.py` 与 `test_owner_auth_v2_contract.py` 守护。无浏览器 E2E 框架）。

- 执行时间：2026-11-16T19:05:28+08:00（E2E/冒烟）、19:06:00+08:00（全量回归），均为最后一次执行。
- 命令：
  1. `cd backend && /tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python manage.py test tests.e2e --settings=config.test_settings`
  2. `cd backend && …/python manage.py test tests.smoke --settings=config.test_settings`
  3. 全量回归见下节。
- **E2E 层 total = pass + fail + skip + blocked + not_testable = 67 + 0 + 0 + 0 + 5 = 72**：pass 67 = 后端 e2e 61（其中新写 6）+ smoke 6；not_testable 5 = NT-01~NT-05（见 test_plan"不可测项"，已写入下方人工验证清单，不计入通过率分母）。
- 通过率 = pass / (pass + fail + blocked) = 67 / 67 = **1.00**。
- critical path 覆盖率 = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = **14 / 14 = 1.00**（US-193~206；逐故事见 test_plan"故事覆盖核对"，本批新写旅程 TC-E2E-516~521 共 6 条）。
- critical path 通过率 = 6 / 6 = **1.00**（TC-E2E-516~521 全部通过）。
- 待人工验证（critical path 中无法自动化的部分，单独计数）：**4 项**（M-01、M-02、M-03、M-05，见人工验证清单）；AC-201-01 小程序 pdf 记 PARTIAL（NT-01，OQ-06）。
- 判定模式：INCREMENTAL baseline——相对基线零新增失败（见全量回归）、新写用例全部通过。上一层（集成）门控：PASSED。**本层门控：PASSED**（带"待人工验证 4 项"，PM 终态至多 DELIVERED_WITH_ISSUES 的判断依据见协议 §K）。

## 全量回归

| 范围 | 命令 | 计数 | 相对基线新增失败 |
|---|---|---|---|
| 后端全量 | `cd backend && …/python manage.py test --settings=config.test_settings` | `Ran 945 tests in 73.018s` / `OK`（基线 822 = 821 OK + 1 既有环境失败；本次 822 + 新写 123 = 945） | **0**（基线失败 TC-INT-611 已修正为通过） |
| 前端全量 | `cd frontend && npx vitest run --passWithNoTests` | `Test Files 26 passed (26)`、`Tests 281 passed (281)`（基线 259/259 + 新写 22） | 0 |
| 小程序全量 | `cd miniprogram && npx vitest run --passWithNoTests` | `Test Files 15 passed (15)`、`Tests 104 passed (104)`（基线 97/97 + 新写 7） | 0 |
| 静态检查 | `python -m compileall -q backend`；`cd backend && python manage.py check --settings=config.test_settings` | `COMPILE_OK`；`System check identified no issues (0 silenced).` | 0 |
| 远程套件语法 | `ast.parse` `backend/tests/remote/remote_cases.py`、`remote_client.py` | `REMOTE_AST_OK`（**本批不运行 remote**，P4-1，仅部署后由 E2 执行） | — |

相对基线新增失败：**0 条**（逐条列出：无）。既有失败 TC-INT-611 的修正见集成报告。

## 用户旅程

全部为后端 HTTP/命令旅程（`backend/tests/e2e/test_owner_auth_v2_journeys.py`），合成数据，运行方式 `sim`。

### TC-E2E-516: 选商铺 → 姓名核对失败 → 转申诉 → 管理员审核 → 追加清册 → 再次认证
- 关联：US-193/194/197/198/199/200/201/203/204；AC-193-01、AC-194-02、AC-200-03、AC-199-01、AC-197-01、AC-198-04/05、AC-203-01、AC-204-04；环境：SQLite 测试库 + 管理命令 + 真实 DRF 路由与令牌。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 门牌型商铺"建设南路142号"+住宅，`relocate_shops --apply` | 改库 1 条 | 命令成功 | PASS |
| 2 | GET /units/options（第一级） | `["1","商铺"]` | 一致 | PASS |
| 3 | GET /units/options?building=商铺 | level=unit_no，`level_label="楼栋/门牌"` | 一致 | PASS |
| 4 | 逐级选到户号 | levels=[building, unit_no, room]，得到商铺 id | 一致 | PASS |
| 5 | POST /certifications（姓名"王五"） | 422 OWNER_NOT_MATCHED，响应不含原业主名/号码 | 一致 | PASS |
| 6 | 上传资料 + POST /appeals（owner_name 王五） | 201 | 201 | PASS |
| 7 | 管理员 GET /admin/appeals?status=PENDING | 含 owner_name、账号、昵称、坐落 `商铺建设南路142号1号`、资料 1 个 | 一致 | PASS |
| 8 | 管理员/无关用户/未登录 下载资料 | 200 / 403 / 401 | 一致 | PASS |
| 9 | POST decision APPROVE | 200，registry_update=OWNER_ADDED | 一致 | PASS |
| 10 | 查清册 | 业主 {原业主甲, 王五}；号码 {原号码, 申诉人号} | 一致 | PASS |
| 11 | GET /me/housing | 房屋=该商铺，名称 `商铺建设南路142号1号`，身份"产权业主" | 一致 | PASS |
| 12 | 管理员撤销认证 → 用户 POST /certifications（王五） | 房屋清空 → 201；再用原业主名 409 ALREADY_CERTIFIED | 一致 | PASS |
- 结论：PASS

### TC-E2E-517: 无手机号微信用户 → 姓名 + 产权证明 → 通过（只写姓名）
- 关联：US-202/203；AC-202-01/02、AC-203-02。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 无手机号账号输入与清册同名认证 | 422 OWNER_NOT_MATCHED（不再 409 PHONE_REQUIRED，不自动认证） | 一致 | PASS |
| 2 | 申诉不带资料 | 400 PROOF_REQUIRED | 一致 | PASS |
| 3 | 带资料申诉 | 201 | 201 | PASS |
| 4 | 管理员列表 | has_phone=false，phone=null | 一致 | PASS |
| 5 | 通过 | notice「该产权人无联系电话」；清册新增姓名、不写电话；用户成为产权业主 | 一致 | PASS |
- 结论：PASS

### TC-E2E-518: 第二套房——认证失败 → 驳回 → 再申诉 → 通过
- 关联：US-204、US-203；AC-204-01/04、AC-203-09。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 已认证第一套房；认证第二套房（清册登记他人） | 422，第二套清册业主与号码逐项不变 | 一致 | PASS |
| 2 | 申诉 → 管理员拒绝（原因） | 清册无变化；我的申诉含驳回原因 | 一致 | PASS |
| 3 | 再申诉 → 通过 | 第二套追加其姓名与号码；第一套认证与清册不变；我的房屋含两套 | 一致 | PASS |
- 结论：PASS

### TC-E2E-519: 商铺改库 → 导出 → 导入预检 → 幂等
- 关联：US-193/195/196；AC-195-01/02/04/06、AC-193-01/02、AC-196-01/02/03。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 旧结构清册：1/2 栋内商铺、门牌型商铺、住宅、地下车位；已认证商铺业主；待审申诉 | — | — | PASS |
| 2 | 未归类时导出（目录 700） | 退出码 2，无文件 | 一致 | PASS |
| 3 | 改库 dry-run | would_change=3，conflicts=0 | 一致 | PASS |
| 4 | apply（备份、--expect-changes 3） | moved=3、lost_origin=0、前后单元数 5/5 | 一致 | PASS |
| 5 | 第一级与第二级 | `["1","地下车位","商铺"]`；商铺下 `["1栋","2栋","枫林路124号附1号"]`；1 栋仅余住宅 | 一致 | PASS |
| 6 | 已认证业主与待审申诉 | 仍绑同一记录，名称 `商铺1栋负1层1139号`；申诉仍待审，坐落随之变化 | 一致 | PASS |
| 7 | 导出 --output-dir | structure=shop_relocated；差 0；预检失败/新增/更新 0；文件 0600 | 一致 | PASS |
| 8 | 把导出文件交给 `/admin/registry/import?dry_run=1` | dry_run=true、imported=0、updated=0、failed=0；清册仍 5 条 | 一致 | PASS |
| 9 | 再 dry-run | would_change=0、already_target=3 | 一致 | PASS |
- 结论：PASS

### TC-E2E-520: 席位补录与未来席位按开始日生效
- 关联：US-205/206；AC-205-01/04、AC-206-01~04。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 授予开始日=今天−200 天 | 201，effective=true；/me 显示委员且通过委员接口权限层 | 一致 | PASS |
| 2 | 授予开始日=今天+10 天 | 201，effective=false | 一致 | PASS |
| 3 | 开始前：/me、委员接口、再次授予、到期任务、列表 | 身份"产权业主"、committee=null；403；409 ALREADY_SEATED；expire_due=0；effective 标志分别 true/false | 一致 | PASS |
| 4 | 本地日期 = 开始日前一天 / 开始日 | 仍不生效 / /me 显示委员且过权限层 | 一致 | PASS |
- 结论：PASS

### TC-E2E-521: 任期已结束被拒与授予权限
- 关联：US-205；AC-205-02、AC-205-06。

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 12 个月任期，开始日 2020-01-01 | 400「按配置任期，该席位已于 2021-01-01 结束，不能授予」，无席位 | 一致 | PASS |
| 2 | 普通用户令牌/未登录授予 | 403 / 401 | 一致 | PASS |
- 结论：PASS

### 前端/小程序侧（jsdom 组件测试，计入单元层命令输出）
TC-UNIT-667~688（Web）、TC-MP-504~510（小程序）覆盖姓名输入、转申诉、多附件、`level_label`、AdminAppeals、ProofThumbs（懒加载/弹窗/pdf/权限）、"待生效"；既有 jsdom 旅程 TC-E2E-515 等随全量通过。浏览器/真机行为见人工验证清单。

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| DEF-024 | MINOR（既有，非本批引入；开发评审 CR-005 OPEN） | 席位授予 `term_start="2026-02-30"`（格式合法、日期不存在）→ `parse_date` 抛 `ValueError` → 500 | 无失败用例（本机 scratch 复现；HEAD 版同样代码） | `backend/apps/committee/views.py:63`（`parse_date`） |

本批新写用例全部通过，**无新增产品缺陷**；全量回归零新增失败。

## 人工验证清单

自动化无法覆盖或属授权后/部署后步骤的项（含 API 测试替身"无"的情形：本批不涉及闭源 API，P11-3 的微信/短信均经 Fake，故无此类项）。

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-201-01（小程序 pdf）/ NT-01 | 用户确认 OQ-06 是否接受"小程序申诉资料仅图片，pdf 仅 Web"；若不接受，另批实现 `wx.chooseMessageFile`（需微信官方资料，`[UNSOURCED]`） | 用户答复（接受 / 另批） | 用户决定；若实现需微信开发者工具真机 | 是（US-201 Must Have，AC 记 PARTIAL） |
| M-02 | AC-198-01/02 / NT-02（CR-001） | E2 部署后，管理员登录测试环境 `https://ai-freeark.xin/ocap/` 后台打开申诉页，准备一页含 20 条×最多 5 个资料（图片+pdf）的数据（只用 `e2e_` 账号提交）；滚动观察缩略图懒加载与内存/带宽；点击缩略图看大图、上/下一份、pdf 预览与下载、关闭后页码与筛选保持；用普通用户令牌直接访问附件 URL | 缩略图数量=资料数；大图弹出可切换；pdf 可预览并有下载入口；关闭不重载；无权访问 403 无内容；无明显卡顿 | 真实浏览器（Chrome/Edge 与手机浏览器各一）；测试环境 | 是 |
| M-03 | AC-196-03 / NT-03 | 用户另行授权导出后，在目标机核对 `/home/yangyang/ocap_exports/` 目录权限 700、文件权限 600、文件名含日期；用站点 URL 尝试取该文件名 | `stat` 为 700/600；URL 返回 404/403 | 测试机（须授权，主会话只读核对） | 是 |
| M-04 | AC-195-07、AC-196-05 / NT-04、NT-05 | 授权前确认对测试环境清册写入数为 0；授权后 `git grep` 仓库（含 `project_workspace/`）检索导出文件名与样例姓名/手机号 | 写入 0；检索 0 命中；报告与日志只含计数 | 主会话 | 否 |
| M-05 | AC-195-01/02、Q-OA-26/29 | 用户另行授权后，在测试机运行 `relocate_shops` dry-run（只读）核对：商铺条数（预期 107）、旧楼栋写法分布、楼层写法、冲突数；再按授权 apply 并核对 `lost_origin=0`、计数前后相等，导出预检 0 | 与 107 条一致、无冲突、计数相等 | 测试机（须授权）；部署新代码后 | 是 |
| M-06 | GR-C-001-F03、N-01 | 用户在 HBuilderX/微信开发者工具构建并手动发布新版小程序；旧版小程序认证将收到 400 | 新版可用，旧版认证 400 | HBuilderX、微信开发者工具、真机 | 否（E1 范围） |
| M-07 | GR-C-001-F02、画像 P4-1 | 部署后 E2 运行 `backend/tests/remote/**`（需 `OCAP_E2E_BASE_URL`、`OCAP_E2E_PASSWORD`）：TC-E2E-337 现仅提交/驳回，护栏拒绝任何非 REJECT 的申诉决定 | 远程套件通过；清册与非 `e2e_` 数据无变化 | E2（devops-engineer）；测试环境 | 否 |

## 冻结核对

报告写出前最后一次修改的测试文件均早于全量回归的开始时间（19:06:00）：

| 测试文件 | 最后修改时间 |
|---|---|
| `backend/tests/unit/test_owner_auth_v2_rules.py` | 2026-11-16 18:58:15 |
| `backend/tests/integration/test_owner_auth_v2_shops.py` | 2026-11-16 18:58:02 |
| `backend/tests/integration/test_owner_auth_v2_residency.py` | 2026-11-16 18:51:52 |
| `backend/tests/integration/test_owner_auth_v2_contract.py` | 2026-11-16 18:51:21 |
| `backend/tests/integration/test_owner_auth_v2_seats.py` | 2026-11-16 18:50:21 |
| `backend/tests/e2e/test_owner_auth_v2_journeys.py` | 2026-11-16 18:53:40 |
| `backend/tests/integration/test_registry_export_cmd.py` | 2026-11-16 18:42:55 |
| `backend/tests/remote/remote_cases.py` / `remote_client.py` | 2026-11-16 18:42:46 / 18:42:55 |
| `frontend/tests/owner_auth_v2.spec.js` | 2026-11-16 18:55:50 |
| `miniprogram/tests/owner_auth_v2.spec.js` | 2026-11-16 18:57:08 |

四份报告写出时间 19:08~19:13，晚于所有测试文件；报告写出后未再改动测试文件（返回前以 `ls -l --time-style=full-iso` 复核）。变异探针（20 处）只在 scratchpad 副本进行，未触及仓库。
