<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T12:37:10+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/integration_test_report.md</file>
    <file>requirements/user_stories.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告

## 摘要

critical path 口径：替代（后端多步 HTTP 旅程——真实批量导入接口 + 管理命令 + 认证/选房/列表接口，TC-E2E-510~514；前端 jsdom 挂载真实 `AdminRegistry.vue` + 带状态假服务端，TC-E2E-515。项目无浏览器 E2E 框架）

- 执行时间：2026-11-16T12:26:22+08:00 ~ 12:35（+08:00）；环境同单元/集成报告（SQLite 内存库、临时目录、合成数据）；不连接测试机，不跑 `backend/tests/remote`。
- 本层命令（仓库根，`PY=/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python`）：
  - `(cd backend && $PY manage.py test tests.e2e --settings=config.test_settings)` → `Ran 55 tests … OK`（既有 50 + 新写 5）
  - 仅新写：`(cd backend && $PY manage.py test tests.e2e.test_unit_sort_filters_journeys --settings=config.test_settings)` → `Ran 5 tests … OK`
  - `(cd frontend && npx vitest run tests/registry_filters.spec.js)` → `Tests 11 passed (11)`（含 TC-E2E-515 一条）
- **total = pass + fail + skip + blocked + not_testable = 56 = 56 + 0 + 0 + 0 + 0**（后端 55 + 前端新写 1；其中既有 50、新写 6）。AC-187-07 为流程性验收，已在 test_plan“不可测项”登记，其对应的是 AC 而非用例，不入本层用例计数。
- critical path 覆盖率 = 有 E2E 用例的 Must Have 故事 / Must Have 故事总数 = 10 / 10 = 1.00（US-183~192，见“故事 → E2E”表）
- critical path 通过率 = pass / (pass + fail + blocked) = 6 / (6 + 0 + 0) = 1.00（TC-E2E-510~515）；前后端契约由 TC-INT-584~587、TC-E2E-512（用页面真实参数名驱动后端）、TC-E2E-515（页面驱动假服务端）共同覆盖
- 上一层（集成）门控：PASSED（576/576）。
- **本层门控：PASSED**（baseline：既有 50 条零新增失败、新写 6 条全部通过、critical path 通过率 1.00）

### 故事 → E2E

| US | E2E 用例 |
|---|---|
| US-183、184、185、186、192 | TC-E2E-510（186 另有 511） |
| US-187 | TC-E2E-513 |
| US-188 | TC-E2E-514（513 前后联动） |
| US-189、190 | TC-E2E-512、515 |
| US-191 | TC-E2E-515 |

## 全量回归

| 范围 | 命令 | 结果 | 基线 | 相对基线新增失败 |
|---|---|---|---|---|
| 后端全量 | `(cd backend && $PY manage.py test --settings=config.test_settings)` | `Ran 822 tests in 140.934s` / `OK`（= 基线 723 + 新写 99；分层 unit 185 + integration 576 + e2e 55 + smoke 6 = 822） | Ran 723 OK | 0 |
| 后端分层 smoke | `(cd backend && $PY manage.py test tests.smoke --settings=config.test_settings)` | `Ran 6 tests … OK` | 6 通过 | 0 |
| 前端全量 | `(cd frontend && npx vitest run --passWithNoTests)` | `Test Files 25 passed (25)` / `Tests 259 passed (259)`（= 基线 248 + 新写 11） | 24 文件 / 248 通过 | 0 |
| 小程序全量 | `(cd miniprogram && npx vitest run --passWithNoTests)` | `Test Files 14 passed (14)` / `Tests 97 passed (97)` | 97 通过 | 0 |
| 静态检查 | `python -m compileall -q backend` | 无错误 | — | 0 |
| 系统检查 | `(cd backend && $PY manage.py check --settings=config.test_settings)` | `System check identified no issues (0 silenced).` | — | 0 |
| 迁移漂移 | `(cd backend && $PY manage.py makemigrations --check --dry-run --settings=config.test_settings)` | `No changes detected` | — | 0 |

相对基线新增失败数：**0**（逐条列出：无）。新写用例总数 110 = 单元 33（后端 23 + 前端 10）+ 集成 71 + E2E 6（后端 5 + 前端 1）。

## 用户旅程

### TC-E2E-510: 导入旧清册 → 修正命令 → 逐级选房（含地下车位）→ 认证 → 房屋列表顺序一致
- 关联：US-183 / AC-183-01~03，US-184 / AC-184-01~03，US-185 / AC-185-01、02，US-186 / AC-186-01、02，US-192 / AC-192-01、02；环境：SQLite、真实路由与鉴权头、合成清册（楼栋 11/10/2/1，1 栋下负一/负二车位，“08”层“0801”号）。位置：`backend/tests/e2e/test_unit_sort_filters_journeys.py::OptionsAndHousingJourney::test_tc_e2e_510_…`

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 管理员 POST `/admin/registry/import` 导入旧清册 | 200 | 200，导入成功 | PASS |
| 2 | 用户 GET `/units/options`（修正前） | 第一级 [1,2,10,11]；1 栋下楼层 [负二,负一] | 与期望一致 | PASS |
| 3 | `relocate_underground_parking`（dry-run → `--apply --backup --expect-changes 2`） | candidates=2、would_change=2、conflicts=0；apply 成功 | 一致 | PASS |
| 4 | GET `/units/options` 第一级 | [1,2,10,11,地下车位]（地下车位最后） | 一致 | PASS |
| 5 | GET options building=1 → unit_no=1 | 单元 [1]；楼层 [1,08]，无负层 | 一致 | PASS |
| 6 | GET options building=地下车位 / floor=负一 | skipped=[unit_no]；楼层 [负二,负一]；车位号 [1]，类型“车位” | 一致 | PASS |
| 7 | 用户依次认证 地下车位车位 → 10 栋 → 2 栋（认证时间与自然顺序相反） | 各 201 | 201 | PASS |
| 8 | GET `/me` 与 `/me/housing`；再刷新 5 次 | 顺序均为 [2栋,10栋,地下车位车位]，逐项相同；`specific_part` 为“地下车位负一1号” | 一致，5 次不变 | PASS |
- 结论：PASS

### TC-E2E-511: 手机号不在清册的地下车位认证提示
- 关联：US-186 / AC-186-02；环境同上。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入并执行修正 | 成功 | 成功 | PASS |
| 2 | 陌生用户对地下车位车位 POST `/certifications` | 422 PHONE_NOT_IN_REGISTRY | 一致 | PASS |
| 3 | 同一用户对普通房屋做同样请求 | 422 PHONE_NOT_IN_REGISTRY（与地下车位一致） | 一致 | PASS |
- 结论：PASS

### TC-E2E-512: 管理员按页面真实参数过滤清册（接口侧契约旅程）
- 关联：US-189 / AC-189-01、03、04、05、07、08，US-190 / AC-190-01、02，US-191（接口侧）；环境同上。参数名取自 `AdminRegistry.vue` 的 `admin.registryUnits({...})` 解析结果。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | GET `/admin/registry/units/filter-options` | 楼栋 [1,2,10,11,地下车位]，单元 [1] | 一致 | PASS |
| 2 | 列表 building=1 / building=地下车位&unit_type=PARKING / building=1&unit_type=PARKING | count 2 / 2 / 0 | 一致 | PASS |
| 3 | owner_phone=1234 | 仅 10 栋，返回完整手机号 | 一致 | PASS |
| 4 | owner_name=乙测；q=0801；q=0801&unit_type=APARTMENT；room=0801&unit_no=1 | count 1 / 1 / 0 / 1 | 一致 | PASS |
| 5 | 不带任何过滤（重置） | count=7，与过滤前相同 | 7 | PASS |
| 6 | 普通用户访问列表与 filter-options | 403 | 403 | PASS |
- 结论：PASS

### TC-E2E-513: 导出文件经真实批量导入预检（修正前与修正后）
- 关联：US-187 / AC-187-01~05，US-188 / AC-188-01；环境同上，输出文件在临时目录。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入旧清册；`export_registry_import_file --output …csv`（只读） | diff_*=0；relocated_units=2；precheck_rows_failed=0；库计数不变 | 一致 | PASS |
| 2 | 文件含“0801”；POST `/admin/registry/import` dry_run | failed=0、imported=2（将在地下车位下新增）、owners_created=2 | 一致 | PASS |
| 3 | `relocate_underground_parking --apply`（expect 2）后再次导出 | 文件字节与修正前相同 | 相同 | PASS |
| 4 | 对新文件 dry_run 预检 | failed=0、imported=0、updated=0、owners_created=0 | 一致 | PASS |
| 5 | 正式导入新文件 | 专有部分/业主/手机号数量与导入前相同；“0801”户的楼层仍为“08” | 一致 | PASS |
- 结论：PASS

### TC-E2E-514: 已认证车位被修正后绑定不变，再按备份还原
- 关联：US-188 / AC-188-01、02、04、06；环境同上。
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入清册；用户认证 1 栋负一车位 | 201 | 201 | PASS |
| 2 | apply（expect 2，备份到临时目录） | moved=2 | moved=2 | PASS |
| 3 | GET `/me/housing` | 仍为同一 unit_id，名称“地下车位负一1号”，角色不变，绑定未终止 | 一致 | PASS |
| 4 | 再次 apply（expect 0） | moved=0 | moved=0 | PASS |
| 5 | `--restore 备份 --apply` | restored=2、differences=0；全部记录（含标识、updated_at）与修正前逐项相等 | 一致 | PASS |
| 6 | GET `/me/housing` | 名称恢复为修正前标识，unit_id 不变 | 一致 | PASS |
- 结论：PASS

### TC-E2E-515: 管理员在后台页面过滤清册（前端旅程，真实页面 + 带状态假服务端）
- 关联：US-189 / AC-189-01、04、05、06、08，US-191 / AC-191-01、03；环境：vitest + jsdom 挂载真实 `AdminRegistry.vue`，假服务端按 IFC-291 语义过滤。位置：`frontend/tests/registry_filters.spec.js`
| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 打开页面 | 共 3 条 | 共 3 条 | PASS |
| 2 | 楼栋选 1 | 只显示 1 栋记录，不含 10 栋，共 1 条 | 一致 | PASS |
| 3 | 叠加类型“车位” | 空状态“暂无数据”，共 0 条 | 一致 | PASS |
| 4 | 清空类型与楼栋，姓名输入“张三”/“李四” | 命中“张三丰（13800001234）”/ 不再出现 | 一致 | PASS |
| 5 | 电话“9999”→“5678” | 共 0 条 → 命中 10 栋 | 一致 | PASS |
| 6 | 点“重置” | 共 3 条；页面文字与占位不含 select / No Data | 一致 | PASS |
- 结论：PASS

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
| 无 | — | 本批未发现产品缺陷。观察项 O-01（库内楼层含“-”时导出自检拒绝落盘，属保护性失败）、O-02（`unit_type=` 空串 400，既有行为）见 test_plan，不作缺陷 | TC-INT-620 | `import_spec`/导入校验（既有） |

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| MV-01 | AC-187-01~03（真实数据）；AUTH-01 | 用户**另行授权**后，在测试机 `backend/` 目录执行 `export_registry_import_file --output …`，先看 `floor|…|recognized/unrecognized` 写法清单（`relocate_underground_parking` dry-run），再导出并核对 `diff_*=0`、`precheck_rows_failed=0` | 与合成用例同样通过；若出现含“-”楼层或缺口（gaps）按 O-01 处理 | 测试机 shell（P9：由主会话在授权后执行） | 否（真实数据验收，非自动化 critical path） |
| MV-02 | AC-188-01~06（真实数据）；AUTH-02 | 授权后在测试机执行 dry-run → `--apply --backup <路径> --expect-changes N` → 抽查 → 必要时 `--restore` | 总数、绑定数与修正前相等；被识别记录楼栋为“地下车位”；冲突时整批停止 | 测试机 shell，MySQL | 否 |
| MV-03 | CR-003（MySQL 并发） | MySQL 下在 apply 期间并发执行批量导入，观察事务回滚且库保持修正前状态 | 唯一约束报错使整个事务回滚 | MySQL 测试库（SQLite 忽略 `select_for_update`） | 否 |
| MV-04 | AC-191-01~03 视觉 | 部署后用真实浏览器打开后台“业主清册”，展开类型/楼栋/单元下拉并制造空结果 | 页面无英文 “select”“No Data”，下拉与空状态为中文 | 浏览器 + 测试环境 | 否（jsdom 已验证文字，视觉为补充） |
| MV-05 | AC-184-01~03 | 部署后用真机小程序与 Web 各打开“选择房屋”，比较四级顺序 | 逐项相同，地下车位最后 | 微信小程序真机 + 浏览器 | 否（服务端单点 + TC-INT-563 已守护） |

人工验证均不属于本批已执行 critical path 用例；“待人工验证的 critical path 用例”数 = 0。
