<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-10T23:08:49.4033974+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（PHASE_09）

## 摘要

critical path 口径：替代（最高层可执行的完整 API 旅程 `backend/tests/e2e`；项目无浏览器 E2E 框架）

- 执行时间：2026-11-10 23:07–23:08（Asia/Shanghai）
- 环境：Python 3.14.6、Django 6.0.6；`config.test_settings`；微信/短信 fake
- 范围：`backend/tests/e2e` 全量 22 个用例，其中本次新写 4 个（TC-E2E-101 ~ TC-E2E-104）
- 命令：`python manage.py test tests.e2e --settings=config.test_settings`

**metrics**：total = pass + fail + skip + blocked + not_testable = 22 = 22 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 22 / 22 = **100%**

critical path 覆盖率 = 有 E2E 旅程的 Must Have 故事 / Must Have 故事总数 = **11 / 11 = 100%**

critical path 通过率 = **100%**（11 个 Must Have 故事的旅程用例全部通过）

判定模式：INCREMENTAL baseline（零新增失败）→ **本层门控：PASSED**

## 全量回归

| 命令 | 计数 | 相对基线新增失败 |
|---|---|---|
| `python manage.py test --settings=config.test_settings`（`backend/`） | `Ran 327 tests in 3.842s` / `OK` | **0**（基线 247 → +80 用例） |
| `npx vitest run`（`frontend/`） | `Tests 2 failed \| 124 passed (126)` | **0**（2 个失败为既有 `theme.spec.js`、`theme_build.spec.js` 环境问题） |
| `npx vitest run`（`miniprogram/`） | `Test Files 10 passed (10)` / `Tests 69 passed (69)` | **0** |

分层计数（各自 `OK`）：`tests.unit` 62、`tests.integration` 237、`tests.e2e` 22、`tests.smoke` 6，合计 327。

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

## 缺陷

无。本次测试未发现需路由给开发的产品缺陷。

## 人工验证清单

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-093-01（xlsx 模板结构） | 在安装 `openpyxl` 的环境（测试机/CI）下载 xlsx 模板并打开 | 第一个工作表为数据表（8 列表头 + 多业主/空手机号/车位示例），"填写说明"工作表在其后 | 已安装 `backend/requirements.txt`（含 openpyxl） | 否 |
| M-02 | AC-093-03 | 删除 xlsx 模板示例行后填入真实数据上传（含隐藏列/合并单元格/第二工作表） | 导入成功，不因模板结构失败 | 同上 | 否 |
| M-03 | AC-093-04（xlsx 分支） | 在 xlsx 中填 "0801"、"13800000000"，导入后查库/页面 | 保存为 "0801" 与 "13800000000"，无前导零丢失、无 "3.0" | 同上 | 否 |
| M-04 | AC-094-07 / TC-INT-113 对应 | 用 20000 行合法 csv（≤5 MB）正式导入，记录接口耗时 | 20000 行全部处理，合计 20000，≤60 秒返回 | 画像 P7 测试环境（内网入口），无并发导入 | 是（性能） |
| M-05 | AC-100-07 | 同一 20000 行文件点击预检并把页面"处理中"状态计入观察 | 60 秒内显示预检结果，清册无变化 | 同上 | 是（性能） |
| M-06 | AC-100-08 | 20000 行含约 2000 行非法的文件正式导入 | 60 秒内显示结果，合计 20000、失败约 2000，可下载错误清单，"处理中"消失 | 同上 | 是（性能） |

## 备注

- 「critical path 口径：替代」依据画像 P3/P4：项目无浏览器 E2E 框架（无 Playwright/Cypress），最高可执行端到端级用例为完整 API 旅程。
- AC-095-05 的"同号再次比对不通过"以 TC-INT-117 的等价证据覆盖（手机号唯一，无法新建同号账号），未计入 E2E。
- xlsx 与性能项不计入本报告通过率分母，详见 test_plan 不可测项。
