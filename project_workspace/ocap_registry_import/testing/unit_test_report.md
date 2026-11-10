<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-10T23:08:49.4033974+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（PHASE_07）

## 摘要

- 执行时间：2026-11-10 23:07–23:08（Asia/Shanghai）
- 环境：Python 3.14.6、Django 6.0.6；`config.test_settings`（SQLite 内存库、迁移置空、外部服务 fake）；Node + vitest
- 范围：`backend/tests/unit`（62 个用例，含本次新写 10 个）+ `frontend/tests/registry_import.spec.js`（4 个用例，全部本次新写）
- 命令：
  - `python manage.py test tests.unit --settings=config.test_settings`
  - `npx vitest run tests/registry_import.spec.js`（`frontend/`）

**metrics**：total = pass + fail + skip + blocked + not_testable = 66 = 66 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 66 / 66 = **100%**

判定模式：INCREMENTAL baseline（零新增失败）；新写用例 14/14 通过 → **本层门控：PASSED**

## 执行输出

```
$ python manage.py test tests.unit --settings=config.test_settings
Found 62 test(s).
System check identified no issues (0 silenced).
Ran 62 tests in 0.302s
OK
```

```
$ npx vitest run tests/registry_import.spec.js
 Test Files  1 passed (1)
      Tests  4 passed (4)
```

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

### 现有相关用例（回归，未改）

`backend/tests/unit` 其余 52 个用例（含 `test_registry_import_smoke.py` 等）全部通过，无新增失败。

## 与基线对比（baseline 模式）

| 失败用例 | 归类 | 依据 |
|---|---|---|
| 无 | — | 本层基线为全绿（GROUP_C 门控实测 backend 247 OK），本次运行 62/62 OK |

## 失败汇总（需路由给开发）

无。

## 备注

- 单元层外的前端全量运行存在 2 个既有环境失败（`theme.spec.js` Windows 路径、`theme_build.spec.js` 行尾），与本次改动无关，详见集成报告"与基线对比"。
- xlsx 解析/模板生成未执行（本机缺 `openpyxl`，画像 P4 禁止自行安装），详见 test_plan 不可测项与 e2e 报告人工验证清单。
