<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T11:21:10+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>3.0.0</version>
  <input_files><file>testing/integration_test_report.md（1.0.0）</file><file>testing/test_plan.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>testing/test_plan.md（2.1.0）</file><file>development/implementation_plan.md（DEF-013 修复）</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（PHASE_08）

## 摘要

**2.1.0（缺陷回流第 2 次，DEF-013）复测**：执行时间 2026-11-11T11:21:10+08:00（Asia/Shanghai）。新写 3 个 DEF-013 回归用例（文件 `backend/tests/integration/test_registry_import_query_bounds.py`，TC-INT-312、TC-INT-312b、TC-INT-313）。

- **环境说明（缺陷回流第 2 次，DEF-013）**：仓库 HEAD 下后端在 Python 3.12 无法导入——另一项目 ocap_content_publish 的 `backend/apps/content/media.py:212`（`list[...]` 注解与类内静态方法 `list` 冲突，TypeError），不属本项目、未改动仓库中的 `apps/content`。后端测试在 scratch 副本运行：`git archive HEAD` 导出 + 覆盖工作区的 `backend/apps/registry/importing.py` 与新增测试文件 `backend/tests/integration/test_registry_import_query_bounds.py`；副本含 `frontend/`、`miniprogram/` 源码（契约测试读取），仅在副本 `media.py` 第 1 行后加 `from __future__ import annotations`。Python 3.12.3、Django 5.2.19、openpyxl（PM venv，未安装任何依赖）。前端/小程序 vitest 直接在仓库内运行。

**metrics（2.1.0）**：`tests.integration` total = pass + fail + skip + blocked + not_testable = 293 = 293 + 0 + 0 + 0 + 0（基线 290 + 新写 3）

通过率 = pass / (pass + fail + blocked) = 293 / 293 = **100%**；契约用例 `tests.integration.test_frontend_contract` 14/14 OK（含 TC-INT-164/165）；新写 3/3 通过 → **本层门控：PASSED**

```
$ (cd <scratch>/backend && <venv python> manage.py test tests.integration --settings=config.test_settings)
Ran 293 tests in 10.726s
OK
Found 293 test(s).
$ (cd <scratch>/backend && <venv python> manage.py test tests.integration.test_frontend_contract --settings=config.test_settings)
Ran 14 tests in 0.689s
OK
```

### 2.1.0 新增用例（DEF-013 回归）

回归思路（不依赖机器速度）：用 `connection.execute_wrapper` 记录每条 SQL 的实际绑定参数个数。每批带全集的实现会让回查 SELECT 的参数数 = 批大小 + 全部姓名数，违反上限；当前实现只带本批 unit_id。

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-INT-312 | AC-094-07、AC-100-07、AC-100-08 | 直接调用 `_create_owners`：1200 单元各 1 位新业主（3 批），预置 1 位计划外同单元业主；断言所有 registry_registryowner 回查 SELECT 单条参数数 ≤ 500（< SQLite 旧上限 999）、回查条数 ≤ ceil(1200/500)=3；结果映射 1200 项、(unit,name)→id 与库一致，计划外业主不入结果 | PASS | — |
| TC-INT-312b | AC-094-01 | 600 单元 × 2 位业主（共 1200）跨批：(unit_key,name) 精确映射 | PASS | —（正确性守卫，修复前后均通过） |
| TC-INT-313 | AC-094-07、AC-100-08 | 经 HTTP 正式导入 1500 行：计数正确（1500/1500/1500，库 1500 业主 1500 手机号）；所有 registry 表查询单条参数数 ≤ 999；owner 回查 SELECT 条数 ≤ 6×ceil(1500/500)，单条参数 ≤ 500 | PASS | — |

**有效性验证（修复前代码上运行）**：scratch 副本 `work_old`，把 `backend/apps/registry/importing.py` 换成 `git show 6fbd24d:backend/apps/registry/importing.py`（每批带全集）后运行同一文件：TC-INT-312 失败（`1700 not less than or equal to 500：回查单条参数数 1700 超过批大小 500`）；TC-INT-313 失败（`2000 not less than or equal to 999：存在参数数 2000 的查询`）；TC-INT-312b 通过（正确性用例，不针对性能）。当前实现 3/3 通过。仓库中的产品代码未被改动。

> 以下为 2.0.0 内容（用例清单未变）。

### 2.0.0 摘要

- 执行时间：1.0.0 为 2026-11-10 23:07–23:08；**1.1.0 缺陷回流复测 2026-11-11 00:28（Asia/Shanghai）**
- 环境：PM venv（Python 3.12.3、Django 5.2.19、openpyxl 3.1.5）；`config.test_settings`（SQLite 内存库、真实 DRF 路由器与 ORM、微信/短信 fake）
- 范围：`backend/tests/integration` 全量 245 个用例 = 基线 237 + 本次新写 8（TC-INT-304 ~ TC-INT-311，文件 `test_registry_import_xlsx_defects.py`）；契约用例 TC-INT-164/165 随全量再次执行
- 命令：`(cd backend && <venv python> manage.py test tests.integration --settings=config.test_settings)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 245 = 245 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 245 / 245 = **100%**

判定模式：INCREMENTAL baseline（零新增失败）；新写用例 8/8 通过 → **本层门控：PASSED**

## 执行输出

```
$ (cd backend && <venv python> manage.py test tests.integration --settings=config.test_settings)
Ran 245 tests in 8.445s
OK
Found 245 test(s).
```

前端组件级用例属单元层（见 unit_test_report TC-UNIT-115/116）；前端全量：

```
$ (cd frontend && npx vitest run --passWithNoTests)
 Test Files  14 passed (14)
      Tests  128 passed (128)
```

有效性验证：新写的集成用例在 `git archive HEAD`（修复前）基线树上运行，TC-INT-305、307、308、309、310 失败（对应 DEF-008、007、009、010、011），TC-INT-304、306、311 在基线树通过（属既有行为保持的回归证据）；修复后树 8/8 通过。

## 分项结果

按集成边界分组（MOD ↔ MOD，接口 IFC-152~164）。

### admin.registry ↔ registry.import_spec / import_template（导入说明与模板）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-101 | AC-092-01 | 管理员读取 spec，字段与页面文案一致 | PASS |
| TC-INT-102 | AC-092-02、AC-093-05、AC-094-04、AC-095-04、AC-097-05、AC-100-06 | 普通用户/游客访问 6 个管理端端点一律拒绝 | PASS |
| TC-INT-103 | AC-092-03 | 20001 数据行 → 400"文件行数超过 20000"，清册不变 | PASS |
| TC-INT-104 | AC-092-04、AC-092-05 | .xls → 400"仅支持 xlsx 或 csv"；>5 MB → 413"文件超过 5 MB" | PASS |
| TC-INT-105 | AC-093-01（csv）、AC-093-02 | csv 模板 BOM、表头、三类示例齐全 | PASS |
| TC-INT-106 | AC-093-06 | 旧 5 列模板整文件拒绝，`details.columns` 列出 3 个缺列 | PASS |

### registry.importing ↔ registry.models（多业主与重复行）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-107 | AC-094-01 | 6 位业主/4 手机号，各自凭手机号可认证 | PASS |
| TC-INT-108 | AC-094-02 | 200 位业主全部登记，无数量上限提示 | PASS |
| TC-INT-109 | AC-094-03 | 分号手机号登记到同一业主 | PASS |
| TC-INT-110 | AC-094-05 | 同姓名同手机号两行合并为 1 业主 1 手机号 | PASS |
| TC-INT-111 | AC-094-08、AC-094-09 | 空手机号成功；空姓名失败"业主姓名不能为空"且不影响其他行 | PASS |
| TC-INT-112 | AC-094-06 | 导入审计只含计数，无姓名/手机号明文 | PASS |

### admin.registry ↔ registry.services（单条业主登记）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-113 | AC-095-01、AC-095-02 | 一次保存 12 位业主，姓名与完整手机号回显 | PASS |
| TC-INT-114 | AC-095-03 | 非法手机号拒绝，原业主不变 | PASS |
| TC-INT-115 | AC-095-07 | 空姓名拒绝，原业主不变 | PASS |
| TC-INT-116 | AC-095-08 | 王芳无手机号可保存并回显 | PASS |
| TC-INT-117 | AC-095-05 | 删除业主后既有 membership 保留；清册中该手机号不再参与比对 | PASS |
| TC-INT-118 | AC-095-06 | `/me` 手机号脱敏，无业主姓名 | PASS |

### registry.importing ↔ import_spec（类型与面积）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-119 | AC-096-01 | 四类型与面积（89.50/60.00/未登记/12.50）按文件登记 | PASS |
| TC-INT-120 | AC-096-02、AC-096-03 | 类型为空或越界均失败并给出原因 | PASS |
| TC-INT-121 | AC-096-04 | abc/-5/0/12.345 分别失败 | PASS |
| TC-INT-122 | AC-096-05、AC-099-06 | 同单元类型冲突 → 该单元全部行失败且不写入 | PASS |
| TC-INT-123 | AC-096-06 | 缺"专有部分类型"列整文件拒绝 | PASS |
| TC-INT-124 | AC-096-07 | 车位空面积失败；住宅空面积成功 | PASS |

### admin.registry ↔ registry.views（单条专有部分）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-125 | AC-097-01 | 新增商铺 120.25；PATCH 面积 → "130.50" | PASS |
| TC-INT-126 | AC-097-02 | 未选类型 → 400"请选择专有部分类型" | PASS |
| TC-INT-127 | AC-097-03 | abc/1.234 → 400"专有部分面积格式不正确"，原值不变 | PASS |
| TC-INT-128 | AC-097-04 | 按车位/未登记筛选 | PASS |
| TC-INT-129 | AC-097-06 | 写 REGISTRY_UNIT_CHANGED 审计，既有认证不受影响 | PASS |
| TC-INT-130 | AC-097-07、AC-097-08 | 车位必填面积；住宅可空且返回 null | PASS |

### registry.services ↔ 用户端逐级选项

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-131 | AC-098-01 | 车库/A-088 → "车库-A-088" | PASS |
| TC-INT-132 | AC-098-02 | 车库下 level=room，skipped=["unit_no","floor"] | PASS |
| TC-INT-133 | AC-098-03 | 混合楼栋无空选项，空单元商铺仍可达（has_empty） | PASS |
| TC-INT-134 | AC-098-04 | 缺楼栋/户号失败；单元楼层为空不报错 | PASS |
| TC-INT-135 | AC-098-05 | 四级齐全单元标识与选择行为不变 | PASS |
| TC-INT-136 | AC-098-06 | 车位一行导入成功，failed=0 | PASS |

### registry.importing ↔ 既有清册（重复导入）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-137 | AC-099-01 | 追加王强，单元计入 updated | PASS |
| TC-INT-138 | AC-099-02 | 同名追加手机号，业主数不变 | PASS |
| TC-INT-139 | AC-099-03 | 类型/面积改为文件值，changes 列出字段 | PASS |
| TC-INT-140 | AC-099-04 | 文件类型/面积为空时既有值不变 | PASS |
| TC-INT-141 | AC-099-05 | 文件未包含的业主与认证保留（只增不删） | PASS |
| TC-INT-142 | AC-099-07 | 手机号属于同单元另一位业主 → 该行失败 | PASS |
| TC-INT-143 | AC-099-08 | "张伟 " 合并、"张伟（二）"新增，共 2 位 | PASS |

### registry.importing dry_run ↔ apply_plan

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-144 | AC-100-01、AC-100-03 | 预检不写库，数字与正式导入逐项一致 | PASS |
| TC-INT-145 | AC-100-02 | 第 7/12/15 行错误原因正确，失败计数 3 | PASS |
| TC-INT-146 | AC-100-04 | 一行多手机号其中一个非法 → 只计 1 次失败 | PASS |

### registry ↔ residency（既有清册兼容）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-147 | AC-101-01 | 空类型单元在 `unit_type=UNSET` 列表可见 | PASS |
| TC-INT-148 | AC-101-02 | 既有单元手机号认证行为不变 | PASS |
| TC-INT-149 | AC-101-03 | 补录类型面积不影响业主与认证 | PASS |
| TC-INT-150 | AC-101-04 | 未登记类型可只改业主 | PASS |

### accounts/identity ↔ residency.auto_bind（自动绑定）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-151 | AC-102-01 | 清册手机号注册即 HEAD/REGISTRY，label"户主" | PASS |
| TC-INT-152 | AC-102-02 | 同号登记 3 单元全部绑定且相互独立 | PASS |
| TC-INT-153 | AC-102-03 | 已有户主时第二位为 OWNER，head_slot 唯一 | PASS |
| TC-INT-154 | AC-102-04 | 清册无此号 → 201，0 身份，不报错 | PASS |
| TC-INT-155 | AC-102-06 | 微信用户首次绑定清册号 → auto_bound 含该单元 | PASS |
| TC-INT-156 | AC-102-07 | 同住人升级为产权业主，不报错 | PASS |
| TC-INT-157 | AC-102-08 | CERTIFY_BY_REGISTRY + origin_label，无姓名/手机号明文 | PASS |
| TC-INT-158 | AC-102-09、AC-104-04 | 清册后补手机号不自动绑定；可手动认证 201 | PASS |
| TC-INT-166 | AC-102-10 | 非微信账号首次绑定清册号 → 自动认证 HEAD 并写审计 | PASS |

### registry.services ↔ 用户端标签/申诉认证

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-159 | AC-103-01、AC-103-02、AC-103-03 | 末级 label 含类型与面积；未登记仅户号；车位标签无姓名手机号 | PASS |
| TC-INT-160 | AC-103-04 | 未登录请求选项被拒绝 | PASS |
| TC-INT-161 | AC-104-01 | 422 PHONE_NOT_IN_REGISTRY + appeal_available | PASS |
| TC-INT-162 | AC-104-03 | 未绑手机号 → 提示先绑定 | PASS |
| TC-INT-163 | AC-104-04 | 管理员补录手机号后同一用户认证 201 HEAD | PASS |

### 1.1.0 缺陷回流新增（xlsx 上传、auto_bind 隔离、dry_run 表单、补填姓名）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-INT-304 | AC-093-04 | xlsx 文本单元格 "0801"/"08"/"13800000000" 经 API 导入后库中 room="0801"、unit_no="08"、phone="13800000000"，specific_part="1-08-8-0801" | PASS | — |
| TC-INT-305 | AC-093-03（DEF-008） | 楼栋 A2:A4 合并单元格跨 3 位业主：rows_total=3、failed=0、owners_created=3，楼栋"1栋" | PASS | — |
| TC-INT-306 | AC-093-03 | 隐藏列 F + 第二工作表含干扰业主：仅导入首表 1 行，干扰业主未入库，面积 89.50 | PASS | — |
| TC-INT-307 | AC-093-01、AC-093-04（DEF-007） | API 下载 xlsx 模板：首表表头 = 8 列，A/B/C/D/H 列 column 与示例行为 "@"，第二表"填写说明" | PASS | — |
| TC-INT-308 | AC-102-02（DEF-009） | 同号 3 专有部分，按单元对 `MembershipService.certify_owner` 打补丁令其中 1 个抛 RuntimeError；注册 201，`auto_bound` 仅另 2 个，库中 2 条 HEAD/REGISTRY membership，失败单元 0 条 | PASS | — |
| TC-INT-309 | AC-100-01（DEF-010） | multipart `dry_run`："false"/"0" 正式导入（写 1 单元，dry_run=False）；"true"/"1"/"TRUE" 预检（库 0 条，imported=1，dry_run=True） | PASS | — |
| TC-INT-310 | AC-099-02（DEF-011） | 既有 name=NULL 业主按同手机号补填"张三"，owners_named=1，updated_at 较 30 天前旧值更新，业主数仍 1 | PASS | — |
| TC-INT-311 | AC-093-01 | 下载的 xlsx 模板不改动回传：4 行 0 失败，2 个专有部分 | PASS | — |

### 前后端契约（frontend / miniprogram ↔ backend）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-164 | AC-092-01、AC-093-01、AC-094-04 | 前端与小程序 api.js 的 4 条新调用（路径+方法）全部可解析到 Django 路由 | PASS |
| TC-INT-165 | AC-100-05、AC-098-02、AC-104-01 | 后端响应键（spec/options/import）与前端读取的字段（rows_total/errors/changes/level/skipped/has_empty/label）一致 | PASS |

## 与基线对比（baseline 模式）

**2.1.0**：后端 integration 基线 290（PM 全量 427 − unit 102 − e2e 29 − smoke 6，推算）→ 本次 293，新增失败 0（+3 新写）；前端全量 131/131、小程序 71/71，无失败，新增失败 0（前端/小程序基线为 PM 复跑口径，本次无失败，不可能有新增）。

2.0.0：

| 项 | 基线（GROUP_C 收尾） | 本次 | 结论 |
|---|---|---|---|
| 后端 integration | 237 OK（PM 2026-11-11 修复前实跑） | 245 OK | 新增失败 0（+8 新写） |
| 后端全量 | 327 OK（unit 62 / integration 237 / e2e 22 / smoke 6） | 342 OK（66 / 245 / 25 / 6） | 新增失败 0（+15 新写） |
| 前端全量 | 126/126（修复前）；修复后 PM 实跑 1 failed（TC-UNIT-114） | 128/128（+2 新写，TC-UNIT-114 已修正） | 新增失败 0 |
| 小程序全量 | 69/69 | 69/69 | 新增失败 0 |

## 失败汇总（需路由给开发）

无。

## 备注

- AC-095-05 中"同号再次比对不通过"因手机号唯一无法新建同号账号，TC-INT-117 以"清册中该手机号已删除 + 既有 membership 保留"作为等价证据。
- xlsx 解析/模板生成：1.0.0 因缺 openpyxl 为 BLOCKED，1.1.0 用 PM venv（含 openpyxl，未安装任何依赖）实际执行 TC-INT-304~307、311；用例带 `skipUnless(openpyxl)` 守卫。
- 20000 行规模（AC-094-07、AC-100-07、AC-100-08）放在 e2e 层执行（TC-E2E-302/303），见 e2e 报告。
- 1.0.0 报告中"前端 2 个既有环境失败"为 Windows 开发机问题，Linux 复测不复现，本版基线按 PM 2026-11-11 实跑的 126/126 口径。
