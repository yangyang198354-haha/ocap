<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-16T12:10:07+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告

## 摘要
- `git diff --stat -- backend frontend .gitignore`：9 files changed, 154 insertions(+), 32 deletions(-)；另新建 5 个后端文件（ordering.py、underground.py、exporting.py、两个 management command）。
- 五维平均分：Correctness 8.86、Security 9.43、Performance 8.86、Maintainability 8.57、Testability 8.57；总平均 (8.86+9.43+8.86+8.57+8.57)/5 = 8.86（与下方 35 个评分之和 310/35 一致）。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 4。

## 文件 → MOD/IFC 映射
| 文件 | MOD / IFC |
|---|---|
| backend/apps/registry/ordering.py（新） | MOD-104 / IFC-285~287 |
| backend/apps/registry/services.py | MOD-105 / IFC-288 |
| backend/apps/identity/services.py、backend/apps/residency/housing.py | MOD-106 / IFC-289、290 |
| backend/apps/registry/views.py、urls.py | MOD-107 / IFC-291、292 |
| frontend/src/admin/AdminRegistry.vue、frontend/src/shared/api.js | MOD-108 / IFC-293 |
| backend/apps/registry/underground.py、commands/relocate_underground_parking.py（新） | MOD-109 / IFC-294、295 |
| backend/apps/registry/exporting.py、commands/export_registry_import_file.py（新）、import_template.py | MOD-110 / IFC-296~298 |
| .gitignore | GR-B-001 条件 |

## 自验证结果
环境：venv Python 3.12 + Django 5.2.19；工作目录仓库根。

| 命令 | 输出尾部 |
|---|---|
| `python3 -m compileall -q backend` | 无错误（compiled） |
| `(cd backend && python manage.py check --settings=config.test_settings)` | System check identified no issues (0 silenced). |
| `(cd backend && python manage.py makemigrations --check --dry-run --settings=config.test_settings)` | No changes detected |
| `(cd backend && python manage.py test --settings=config.test_settings)` | Ran 723 tests in 62.902s — OK（基线 723 OK，零新增失败；含 test_frontend_contract.py） |
| `(cd frontend && npx vitest run --passWithNoTests)` | Test Files 24 passed (24)；Tests 248 passed (248) |
| `(cd frontend && npm run build -- --base=/ocap/)` | ✓ built in 53.91s（仅 chunk 体积警告，既有） |
| `(cd miniprogram && npx vitest run --passWithNoTests)` | Test Files 14 passed (14)；Tests 97 passed (97)（小程序无源码改动，按要求运行） |
| `git check-ignore -v registry_import_underground_parking.xlsx registry_import_underground_parking.csv`（先 touch 后删除） | `.gitignore:14:registry_import_underground_parking.xlsx` / `.gitignore:15:registry_import_underground_parking.csv`，均命中 |

补充冒烟（scratch 复制的 backend、合成数据，已删除，不入库）：自然顺序（1,1栋,2,10,11,地下车位；负二,-1,负一,1,2,10,B1；5,A2,A10）；dry-run → 导出（修正前 would_create_units=2/owners=2/phones=1，rows_failed=0，roundtrip_mismatches=0）→ apply（备份 0600）→ 再导出（would_create=0）→ 重复 apply expect 0（moved=0）→ restore dry-run（differences=2）→ restore apply（differences=0，标识还原）→ 备份已存在退出码 3。均通过。

未验证：两条命令对真实 MySQL 数据的行为（P8/P9/C-51，授权前不执行）；`select_for_update` 在 SQLite 被忽略，并发保护仅在 MySQL 生效；小程序 uni build（无源码改动）。

## 按模块评审
### MOD-104
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 10/10 | 9/10 | 10/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-105
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无（响应结构不变；room 级在内存排序，量级千行） | — |

### MOD-106
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-107
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MINOR | views.py:80 `_apply_unit_filters` | 过滤参数 strip 后再校验（ASSUMPTION，纯空白视为未设置）；与设计"空串不限制"一致但未明写 | OPEN（已在 plan 登记） |

### MOD-108
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 7/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MINOR | AdminRegistry.vue:13-37 | 无组件测试覆盖（现有前端测试不涉及本页）；Testability 7 对应此项，新测试 `registry_filters.spec.js` 由 test-engineer 编写 | OPEN |

### MOD-109
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MINOR | underground.py:131 `plan_relocation` | 冲突只报告含被改记录的重复组（ASSUMPTION，见 plan 开放问题）；`select_for_update` 在 SQLite 无效，并发保护仅 MySQL | OPEN |

### MOD-110
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-004 | MINOR | exporting.py:verify_export | 存在 gaps（--allow-gaps）时计数差仅报告不判失败（ASSUMPTION）；两条新命令暂无自动化测试，由 GROUP_D 编写 | OPEN |

## 未解决的 CRITICAL
无。

## 遗留 MAJOR
无（0 条）。

## 缺陷修复
不适用（非缺陷修复模式）。

## 现有测试调整
无调整。`test_identity_display.py` tc_int_506 在新排序口径下原断言仍成立，未改动；未删除或跳过任何用例。
