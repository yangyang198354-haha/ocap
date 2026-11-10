<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:35:27+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/e2e_test_report.md（1.0.0）</file><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（PHASE_09）

## 摘要

critical path 口径：替代（最高层可执行的完整 API 旅程 `backend/tests/e2e`；项目无浏览器 E2E 框架）

- 执行时间：1.0.0 为 2026-11-10 23:07–23:08；**1.1.0 缺陷回流复测 2026-11-11 00:28（Asia/Shanghai）**
- 环境：PM venv（Python 3.12.3、Django 5.2.19、openpyxl 3.1.5）；`config.test_settings`；微信/短信 fake
- 范围：`backend/tests/e2e` 全量 25 个用例 = 基线 22 + 本次新写 3（TC-E2E-302 ~ TC-E2E-304，文件 `test_registry_import_scale_journeys.py`）
- 命令：`(cd backend && <venv python> manage.py test tests.e2e --settings=config.test_settings)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 25 = 25 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 25 / 25 = **100%**

critical path 覆盖率 = 有 E2E 旅程的 Must Have 故事 / Must Have 故事总数 = **11 / 11 = 100%**（1.1.0 为 US-093、US-094、US-102 增补旅程 TC-E2E-304/302）

critical path 通过率 = **100%**（11 个 Must Have 故事的旅程用例全部通过；前后端契约由 TC-INT-164/165 与前端组件用例 TC-UNIT-115/116 覆盖，均通过）

判定模式：INCREMENTAL baseline（零新增失败，新写 3/3 通过）→ **本层门控：PASSED**

```
$ (cd backend && <venv python> manage.py test tests.e2e --settings=config.test_settings)
Ran 25 tests in 15.585s
OK
Found 25 test(s).
[TC-E2E-302] 20000 行合法：预检 1.1s，正式 5.7s（SQLite 内存库）
[TC-E2E-303] 20000 行含 2000 非法：预检 1.2s，正式 5.3s（SQLite 内存库）
```

## 全量回归

| 命令 | 计数 | 相对基线新增失败 |
|---|---|---|
| `(cd backend && <venv python> manage.py test --settings=config.test_settings)` | `Ran 342 tests in 25.541s` / `OK` | **0**（基线 327 → +15 新写） |
| `(cd frontend && npx vitest run --passWithNoTests)` | `Test Files 14 passed (14)` / `Tests 128 passed (128)` | **0**（基线 126/126；+2 新写；TC-UNIT-114 已修正，GR-C-002-F01 清除） |
| `(cd miniprogram && npx vitest run --passWithNoTests)` | `Test Files 10 passed (10)` / `Tests 69 passed (69)` | **0**（基线 69/69） |

分层计数（各自 `OK`）：`tests.unit` 66、`tests.integration` 245、`tests.e2e` 25、`tests.smoke` 6，合计 342 = 66 + 245 + 25 + 6。前端 128 = 基线 126 + 2 新写。

有效性验证：新写的 3 个后端测试文件在 `git archive HEAD`（修复前）基线树上运行 15 个用例 10 个失败（均对应 DEF-007~011），修复后 342 全绿。基线树运行的 TC-E2E-304 失败（合并单元格），TC-E2E-302/303 通过（性能口径在修复前后均成立）。

## 用户旅程

### TC-E2E-101: 管理员导入多业主与车位 → 业主注册自动绑定 → 用户端选车位

- 关联：US-092 / AC-092-01；US-093 / AC-093-02；US-094 / AC-094-01；US-096/AC-096-01；US-098 / AC-098-02、AC-098-06；US-102 / AC-102-01、AC-102-03；US-103 / AC-103-01
- 环境：SQLite 内存库；管理员令牌；FakeSmsGateway

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | GET `/admin/registry/import/spec` | 200，max_rows=20000 | 200，max_rows=20000 | PASS |
| 2 | GET `/admin/registry/import/template?file_type=csv` | 200，含表头"楼栋" | 200，含"楼栋" | PASS |
| 3 | 同一文件预检 `dry_run=1` | 200，清册 0 条 | 200，RegistryUnit=0 | PASS |
| 4 | 正式导入（住宅 3 业主 + 车位 1 业主） | imported=2、owners_created=4、failed=0 | (2, 4, 0) | PASS |
| 5 | 13700000101 注册 | 住宅 membership=HEAD | HEAD | PASS |
| 6 | 13700000102 注册 | membership=OWNER，/me label"产权业主" | OWNER，"产权业主" | PASS |
| 7 | 用户 GET `options?building=车库` | skipped=["unit_no","floor"]，直接列户号 A-101，label 含"车位" | 一致 | PASS |
| 8 | 13700000103 注册 | 车位 membership=HEAD，/me units 含"车库-A-101" | 一致 | PASS |

- 结论：PASS

### TC-E2E-102: 首次导入 → 认证 → 重复导入改类型 → 管理端编辑业主 → 认证保留

- 关联：US-099 / AC-099-01、AC-099-03、AC-099-05；US-095 / AC-095-02；US-101 / AC-101-03
- 环境：SQLite 内存库；管理员令牌

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入 张伟(13700000201) + 李娜 | failed=0 | 一致 | PASS |
| 2 | 张伟注册 | 住宅 membership=HEAD | HEAD | PASS |
| 3 | 重导（张伟新号 13700000202 + 王强，类型公寓 90.00） | updated=1，errors=[]，changes=[{fields:["unit_type","area"]}] | 一致 | PASS |
| 4 | 查库与列表 | type=APARTMENT/90.00；业主 张伟/李娜/王强；label"公寓" | 一致 | PASS |
| 5 | 张伟手机号 | ["13700000201","13700000202"] | 一致 | PASS |
| 6 | PUT owners 仅保留张伟 | 200，业主 ["张伟"]，原 membership 保留 | 一致 | PASS |
| 7 | 审计 | REGISTRY_UNIT_CHANGED 存在 | 存在 | PASS |
| 8 | 先注册 13700000203，再建 legacy 单元 + 手机号，GET `unit_type=UNSET` | legacy 出现在列表；手动认证 201 | 一致 | PASS |

- 结论：PASS

### TC-E2E-103: 无手机号业主 → 认证提示申诉 → 管理员补录 → 同一用户认证成功

- 关联：US-104 / AC-104-01、AC-104-04；US-102 / AC-102-09
- 环境：SQLite 内存库；管理员令牌

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 导入 王芳（手机号空） | failed=0 | 一致 | PASS |
| 2 | 用户（13900000301）POST `/certifications` | 422 PHONE_NOT_IN_REGISTRY，details.appeal_available=true | 一致 | PASS |
| 3 | 管理端查看该单元业主 | phones=[] | 一致 | PASS |
| 4 | PUT owners 补录 13900000301 | 200；Membership 仍为 0（补录不触发自动绑定） | 一致 | PASS |
| 5 | 同一用户再次 POST `/certifications` | 201，role=HEAD，无需申诉 | 一致 | PASS |

- 结论：PASS

### TC-E2E-104: 新增车位缺面积被拒 → 新增商铺 → 改面积 → 按类型筛选 → 审计留痕

- 关联：US-097 / AC-097-01、AC-097-04、AC-097-06、AC-097-07
- 环境：SQLite 内存库；管理员令牌

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | POST 车位（无面积） | 400"车位须填写专有部分面积"，清册 0 条 | 一致 | PASS |
| 2 | POST 商铺 120.25 | 201，label"商铺"，area"120.25" | 一致 | PASS |
| 3 | PATCH 面积 130.5 | 200，area"130.50" | 一致 | PASS |
| 4 | GET `units?unit_type=SHOP` | 仅返回该单元 | 一致 | PASS |
| 5 | 审计 | REGISTRY_UNIT_CHANGED 存在 | 存在 | PASS |

- 结论：PASS

### TC-E2E-302: 20000 行合法清册 → 预检 → 正式导入（AC-094-07、AC-100-07）

- 关联：US-094 / AC-094-07；US-100 / AC-100-07
- 环境：SQLite 内存库（**非目标机口径**）；管理员令牌；程序生成 20000 行 csv（<5 MB）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | POST import `dry_run=1` | 200；rows_total=rows_ok=20000，failed=0，dry_run=true；库 0 条；耗时 <60 s | 一致；预检 1.1 s | PASS |
| 2 | POST import 正式 | 200；rows_total=rows_ok=20000，failed=0；imported=owners_created=phones_created=20000；耗时 <60 s | 一致；正式 5.7 s | PASS |
| 3 | 查库 | RegistryUnit/Owner/Phone 各 20000 | 一致 | PASS |

- 结论：PASS

### TC-E2E-303: 20000 行含约 10% 非法行 → 预检与正式一致（AC-100-08、AC-100-07）

- 关联：US-100 / AC-100-07、AC-100-08
- 环境：同上；每第 10 行手机号为 "12345"（2000 行）

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 预检 | rows_total=20000，rows_ok=18000，failed=2000，imported=18000，errors 非空且字段为"手机号"；<60 s | 一致；1.2 s | PASS |
| 2 | 正式导入 | 同预检逐项一致（rows_total/rows_ok/failed/imported/updated/owners_created/phones_created）；<60 s | 一致；5.3 s | PASS |
| 3 | 查库 | 18000 单元；第 0 行（非法）未写入 | 一致 | PASS |

- 结论：PASS（错误清单下载由前端组件用例 TC-UNIT-116 覆盖）

### TC-E2E-304: 下载 xlsx 模板 → 填入含前导零文本与合并楼栋 → 预检 → 导入 → 业主注册自动绑定

- 关联：US-093 / AC-093-01、AC-093-03、AC-093-04；US-102 / AC-102-01
- 环境：SQLite 内存库；管理员令牌；openpyxl 现读现写工作簿

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | GET template `file_type=xlsx`，清空示例后填 "1栋/08/8/0801" 两位业主，楼栋 A2:A3 合并 | 200，可由 openpyxl 读取 | 一致 | PASS |
| 2 | 上传预检 | 200，failed=0，imported=1，库 0 条 | 一致 | PASS |
| 3 | 上传正式 | 200，failed=0，owners_created=2；specific_part="1栋-08-8-0801"，unit_no="08"，room="0801" | 一致 | PASS |
| 4 | 13700040001 注册 | membership HEAD / source REGISTRY | 一致 | PASS |

- 结论：PASS

## 缺陷

无。1.1.0 复测未发现新的产品缺陷（DEF-013 起无）；DEF-007~012 的修复均由新用例证实有效。

## 人工验证清单

1.0.0 的 M-01~M-03（xlsx 模板结构、合并单元格/隐藏列/第二工作表、xlsx 文本单元格）已由自动化用例覆盖（TC-UNIT-307/309/310、TC-INT-304~307/311、TC-E2E-304），从人工清单中移除。以下为目标机性能口径复核（测试环境 SQLite 计时已通过，但非目标机口径）：

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-04 | AC-094-07 / TC-E2E-302（测试环境已通过） | 用 20000 行合法 csv（≤5 MB）在目标机正式导入，记录接口耗时 | 20000 行全部处理，合计 20000，≤60 秒返回 | 画像 P7 测试环境（内网入口），无并发导入 | 否（Should/性能口径；故事 US-094 的 critical path 旅程为 TC-E2E-101） |
| M-05 | AC-100-07 / TC-E2E-302 | 同一 20000 行文件在目标机点击预检并观察"处理中"状态 | 60 秒内显示预检结果，清册无变化 | 同上 | 否 |
| M-06 | AC-100-08 / TC-E2E-303 | 20000 行含约 2000 行非法的文件在目标机正式导入 | 60 秒内显示结果，合计 20000、失败约 2000，可下载错误清单，"处理中"消失 | 同上 | 否 |

## 备注

- 「critical path 口径：替代」依据画像 P3/P4：项目无浏览器 E2E 框架（无 Playwright/Cypress），最高可执行端到端级用例为完整 API 旅程。
- AC-095-05 的"同号再次比对不通过"以 TC-INT-117 的等价证据覆盖（手机号唯一，无法新建同号账号），未计入 E2E。
- 1.1.0：xlsx 与 20000 行规模已纳入通过率分母并全部通过；耗时为测试环境（SQLite、开发机）口径，目标机口径见人工清单 M-04~M-06。
- 1.0.0 → 1.1.0 对 critical path 的影响：Must Have 故事旅程集不变（11/11），新增旅程使 US-093（xlsx 分支）与 US-094（AC-094-07）在 E2E 层不再依赖人工清单。
