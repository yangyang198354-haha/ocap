<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T12:35:35+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>development/implementation_plan.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告

## 摘要

- 执行时间：2026-11-16T12:26:22+08:00 ~ 12:28:00（+08:00）；环境：venv Python 3.12 + Django 5.2.19（后端，SQLite 内存库，`config.test_settings`）；vitest 2.1.9 + jsdom（前端）。
- 命令（工作目录仓库根，`PY=/tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python`）：
  - `(cd backend && $PY manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run tests/registry_filters.spec.js)`（该文件含 10 条 TC-UNIT-640~649 与 1 条 TC-E2E-515；后者计入 E2E 报告）
- 本层范围：后端 `tests.unit` 全部 185 条（既有 162 + 新写 23）+ 前端新写单元类 10 条 = 195 条。
- **total = pass + fail + skip + blocked + not_testable = 195 = 195 + 0 + 0 + 0 + 0**
- 通过率 = pass / (pass + fail + blocked) = 195 / (195 + 0 + 0) = 1.00
- 判定模式：INCREMENTAL baseline（零新增失败、新写用例全部通过）。基线 162 条后端单元用例全部通过（基线总数 723 = 162 + 505 + 50 + 6）；新增失败 0；新写 33 条（后端 23 + 前端 10）全部通过。
- **本层门控：PASSED**

## 执行输出

```
$ (cd backend && $PY manage.py test tests.unit --settings=config.test_settings)
Ran 185 tests in 1.596s
OK

$ (cd backend && $PY manage.py test tests.unit.test_registry_ordering tests.unit.test_underground_rules tests.unit.test_registry_export_rows --settings=config.test_settings)
Ran 23 tests in 0.027s
OK

$ (cd frontend && npx vitest run tests/registry_filters.spec.js)
 ✓ tests/registry_filters.spec.js (11 tests)
 Test Files  1 passed (1)
      Tests  11 passed (11)
```

变异验证（M-TE-012，scratchpad 副本，不改仓库）：纯规则单元用例由 `ordering.py` 直接断言；排序接入点回退到 HEAD 后集成/E2E 用例 12 条失败（见 integration_test_report）。

## 分项结果

### MOD-104 `registry/ordering.py`（`tests/unit/test_registry_ordering.py`，13 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-610 | AC-183-06 | parse_integer_text：负一/-1/负1=-1，负二=-2，十一=11，全角数字 | PASS | — | — |
| TC-UNIT-611 | AC-183-01 | 后缀 “10栋”“负一层”“1单元” 只去一次，仅后缀不解析 | PASS | — | — |
| TC-UNIT-612 | AC-183-04 | 非数字（A2、B1、地下车位、>99 的中文数字、None）返回 None 不抛异常 | PASS | — | — |
| TC-UNIT-613 | AC-183-01 | 楼栋 1/2/10/11 → [1,2,10,11] | PASS | — | — |
| TC-UNIT-614 | AC-183-01 | “1栋/2栋/10栋”与“1”混排按数值，全部保留 | PASS | — | — |
| TC-UNIT-615 | AC-183-02 | 单元 [1,2,10]，户号 [101,902,1001] | PASS | — | — |
| TC-UNIT-616 | AC-183-03 | 楼层 [-1,1,2,10] | PASS | — | — |
| TC-UNIT-617 | AC-183-04 | 户号 A10/A2/5 → [5,A2,A10]，去重 | PASS | — | — |
| TC-UNIT-618 | AC-183-06、AC-186-01 | 负二 < 负一≈-1≈负1 < 1 < 2，全部保留 | PASS | — | — |
| TC-UNIT-619 | AC-184-03、AC-185-01 | “地下车位”仅楼栋级排最后（含非数字楼栋“A区”），其他层级为普通文字 | PASS | — | — |
| TC-UNIT-620 | AC-183-05 | 空值键层级最低，不丢弃 | PASS | — | — |
| TC-UNIT-621 | IFC-285 | 混合输入键两两可比较（无 int/str 混比） | PASS | — | — |
| TC-UNIT-622 | AC-192-01 | unit_sort_key 四级 + unit_id 并列：2栋 < 10栋 < 地下车位 | PASS | — | — |

### MOD-109 `registry/underground.py` 纯规则（`tests/unit/test_underground_rules.py`，8 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-623 | AC-187-01 | is_negative_floor：负一/负二/-1/负1/负一层 真，1/B1/空/0 假 | PASS | — | — |
| TC-UNIT-624 | AC-188-01 | 只识别“车位且负层”，负层住宅、正层车位、B1 不改；写法清单标注 B1 未识别 | PASS | — | — |
| TC-UNIT-625 | AC-188-01 | 新标识由 build_specific_part 生成；旧楼栋分布统计 | PASS | — | — |
| TC-UNIT-626 | AC-188-01 | 非 1/1栋 楼栋下的被改记录单独计数 | PASS | — | — |
| TC-UNIT-627 | AC-188-04 | 已在地下车位的负层车位不进 moves（幂等） | PASS | — | — |
| TC-UNIT-628 | AC-188-03 | 改后标识冲突：specific_part 与 tuple 两类冲突，含两条 id | PASS | — | — |
| TC-UNIT-629 | CR-003 | 与被改记录无关的重复组（仅大小写不同）不报冲突 | PASS | — | — |
| TC-UNIT-630 | CR-003 | 重复组含被改记录（casefold 相同）仍报冲突 | PASS | — | — |

首轮 3 条（625、628、630）因测试期望值写错失败（中文楼层“负一”不补“层”；room 为 “1” 时标识带“号”；冲突同时产生 tuple 类），属测试问题，已按 `build_specific_part` 实际规则（ADR-064）修正后通过；未触及产品代码。

### MOD-110 导入文件生成函数（`tests/unit/test_registry_export_rows.py`，2 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-631 | AC-187-01、AC-187-04 | `build_data_xlsx`：表头=模板 8 列；“0801”“13800000000” 文本单元格（data_type "s"），read_rows 回读逐格相等 | PASS | — | — |
| TC-UNIT-632 | AC-187-01、AC-187-04 | `build_data_csv`：UTF-8 BOM，表头一致，前导零与多手机号原样 | PASS | — | — |

### MOD-108 前端过滤器（`frontend/tests/registry_filters.spec.js`，10 条新写）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-640 | AC-191-01、AC-189-09 | 占位文字恰为 标识搜索/楼栋/单元/户号/全部类型/产权业主姓名/产权业主电话；无“楼层”；可见文字与 aria/title 不含 select（不区分大小写） | PASS | — | 首轮：测试漏取 el-select 占位（在 `.el-select__placeholder`），已修测试 |
| TC-UNIT-641 | AC-191-02 | 类型下拉选项依次为 全部类型、未登记类型、住宅、公寓、商铺、车位、其他，无英文 | PASS | — | — |
| TC-UNIT-642 | AC-191-03、AC-189-06 | 空结果表格空状态“暂无数据”，无 No Data，总数 0 | PASS | — | — |
| TC-UNIT-643 | AC-191-01 | 楼栋/单元/类型下拉 no-data-text 为“暂无数据” | PASS | — | — |
| TC-UNIT-644 | AC-189-08 | 首次加载空条件不传参；请求一次 filter-options；选项顺序 = 服务端顺序（含“地下车位”最后） | PASS | — | — |
| TC-UNIT-645 | AC-189-01~05、AC-190-02 | 六个过滤器 + 标识搜索各以对应参数名传给 `admin.registryUnits`，回到第 1 页（完整参数对象 toEqual） | PASS | — | — |
| TC-UNIT-646 | AC-189-05 | 电话过滤只保留数字（“13a8-00”→“13800”），maxlength=11 | PASS | — | — |
| TC-UNIT-647 | AC-189-08 | “重置”清空全部条件，重新查询无任何过滤参数，总数恢复 | PASS | — | — |
| TC-UNIT-648 | MOD-108、CR-002 | filter-options 失败不阻塞列表 | PASS | — | — |
| TC-UNIT-649 | IFC-293 | `registryFilterOptions` 为管理端 GET `/admin/registry/units/filter-options`；`registryUnits` 透传 params | PASS | — | — |

## 与基线对比（baseline 模式）

| 项 | 基线（PM 实跑，开发后） | 本次 | 差异 |
|---|---|---|---|
| 后端 `tests.unit` 既有用例 | 162 通过 | 162 通过（185 − 新写 23） | 新增失败 0 |
| 失败清单 | 无 | 无 | 既有失败 0 / 新增失败 0 |

## 失败汇总（需路由给开发）

无。
