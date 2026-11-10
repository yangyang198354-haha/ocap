<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T00:35:27+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/unit_test_report.md（1.0.0）</file><file>testing/test_plan.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（PHASE_07）

## 摘要

- 执行时间：1.0.0 为 2026-11-10 23:07–23:08；**1.1.0 缺陷回流复测 2026-11-11 00:28–00:34（Asia/Shanghai）**
- 环境：PM venv（Python 3.12.3、Django 5.2.19、openpyxl 3.1.5）；`config.test_settings`（SQLite 内存库、迁移置空、外部服务 fake）；Node + vitest
- 范围：`backend/tests/unit`（66 个用例：基线 62 + 本次新写 4）+ 前端 `registry_import.spec.js`（4 个，其中 TC-UNIT-114 本次修正）+ `registry_import_dialog.spec.js`（2 个，本次新写）
- 命令：
  - `(cd backend && <venv python> manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run tests/registry_import.spec.js tests/registry_import_dialog.spec.js)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 72 = 72 + 0 + 0 + 0 + 0（后端 66 + 前端 6）

通过率 = pass / (pass + fail + blocked) = 72 / 72 = **100%**

判定模式：INCREMENTAL baseline（相对基线零新增失败，新写用例全部通过）；新写/修正用例 7/7 通过（TC-UNIT-307~310、TC-UNIT-115~116 新写 6 + TC-UNIT-114 修正 1）→ **本层门控：PASSED**

## 执行输出

```
$ (cd backend && <venv python> manage.py test tests.unit --settings=config.test_settings)
Ran 66 tests in 0.650s
OK
Found 66 test(s).
```

```
$ (cd frontend && npx vitest run tests/registry_import.spec.js tests/registry_import_dialog.spec.js)
 Test Files  2 passed (2)
      Tests  6 passed (6)
```

有效性验证（用例能抓住缺陷）：把新写的 3 个后端测试文件复制到 `git archive HEAD` 导出的修复前基线树（`<scratchpad>/base/backend`）运行，`tests.unit.test_registry_import_defects` 中 TC-UNIT-307、TC-UNIT-308（RuntimeError 与 ApiError 两轮）、TC-UNIT-309 失败，修复后全部通过。

## 分项结果

### MOD-030 清册字段规则与导入规格（`apps/registry/import_spec.py`）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-101 | AC-096-01、AC-093-04 | 面积 "89.50"/"0.5"/"60" 可解析，两位小数保形 | PASS | — |
| TC-UNIT-102 | AC-096-04 | abc/-5/0/12.345 分别给出"大于 0""最多 2 位小数"文案；空值视为未填 | PASS | — |
| TC-UNIT-103 | AC-096-03 | 住宅/公寓/商铺/车位/其他 → 代码映射；越界值给出允许范围 | PASS | — |
| TC-UNIT-104 | AC-098-04 | 楼栋、户号必填；单元与楼层可空，错误字段顺序稳定 | PASS | — |
| TC-UNIT-105 | AC-093-04 | `cell_text` 对 int/float/Decimal/date/bool 归一，不出现 "3.0" | PASS | — |
| TC-UNIT-106 | AC-098-01、AC-098-05 | `build_specific_part` 跳过空层级；四级齐全与旧规则一致 | PASS | — |
| TC-UNIT-107 | AC-092-01 | spec payload 含文件类型、5 MB、20000 行、首工作表与 8 列规则 | PASS | — |
| TC-UNIT-108 | AC-092-01 | 列规则表覆盖全部 8 列，每列有允许取值与示例 | PASS | — |
| TC-UNIT-109 | AC-094-07 | 时间预算可由设置覆盖，非法值回落 60 秒 | PASS | — |
| TC-UNIT-110 | AC-093-01、AC-093-02 | csv 模板 UTF-8 BOM、8 列表头、4 个示例（同单元 3 行/空手机号/车位） | PASS | — |

### MOD-038 前端导入辅助（`frontend/src/admin/registryImport.js`）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-111 | AC-100-05 | `formatImportResult` 输出纯文字摘要，不含 JSON 原文 | PASS | — |
| TC-UNIT-112 | AC-100-07 | `ECONNABORTED`/`ETIMEDOUT` → "导入超时，请缩小文件后重试" | PASS | — |
| TC-UNIT-113 | AC-100-02 | `errorsCsv` 表头"行号,字段,原因"，引号转义 | PASS | — |
| TC-UNIT-114 | AC-100-02 | `downloadText` 使用 BOM + createObjectURL/click/revoke | PASS | — |

### 1.1.0 缺陷回流新增 / 修正（DEF-007~012）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-307 | AC-093-04（DEF-007） | `build_xlsx`：A/B/C/D/H 列 column 与示例行单元格为 "@"，E/F/G 为 General | PASS | — |
| TC-UNIT-308 | AC-102-02（DEF-009） | 同号 3 个专有部分，对 `MembershipService.certify_owner` 按单元打补丁（RuntimeError、ApiError 各一轮），真实 `AutoBindService`：其余 2 个仍绑定为 HEAD，失败单元无 membership | PASS | — |
| TC-UNIT-309 | AC-093-03（DEF-008） | `read_rows`：楼栋 A2:A4 合并，3 行均读到"1栋"；隐藏列 E、第二工作表不影响 | PASS | — |
| TC-UNIT-310 | AC-093-04 | `read_rows`：文本 "08"/"0801"/"13800000000" 原样；数值 3.0→"3"、801→"801" | PASS | — |
| TC-UNIT-114（修正） | AC-100-02（DEF-012） | `downloadText`：fake timers，click 后未 revoke，999 ms 未 revoke，累计 1000 ms 后 revoke 一次；finally 恢复真实计时器 | PASS | —（GR-C-002-F01 已处理） |
| TC-UNIT-115 | AC-100-01、AC-100-05 | `RegistryImportDialog`：打开读 spec；无文件时预检/确认禁用；预检请求 `dry_run:1`，文案含"（预检结果，尚未写入）"，确认导入可用；确认后请求无 dry_run，显示结果、emit `imported` | PASS | — |
| TC-UNIT-116 | AC-100-02 | 预检含失败行：出现"下载错误清单"，点击生成 text/csv Blob，文件名 `registry_import_errors.csv`；无失败行时无此按钮（TC-UNIT-115 断言） | PASS | — |

### 现有相关用例（回归，未改）

`backend/tests/unit` 其余 52 个用例（含 `test_registry_import_smoke.py` 等）全部通过，无新增失败。

## 与基线对比（baseline 模式）

| 失败用例 | 归类 | 依据 |
|---|---|---|
| 无 | — | 本层基线（PM 2026-11-11 修复前）backend unit 62 OK；本次 66/66 OK（+4 新写）。前端基线 registry_import.spec.js 4/4；修复后 TC-UNIT-114 因 DEF-012 失败（GR-C-002-F01，用例过时，非产品缺陷），已修正，本次 6/6 |

## 失败汇总（需路由给开发）

无。

## 备注

- 1.0.0 中前端 `theme.spec.js`/`theme_build.spec.js` 的 2 个失败是 Windows 开发机的环境问题；本次在 Linux 复测前端全量 128/128 通过，无失败（详见集成/E2E 报告）。
- xlsx 解析/模板生成：1.1.0 已用 PM venv 的 openpyxl 实际执行（TC-UNIT-307/309/310），1.0.0 的 BLOCKED 已解除。
