<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T17:25:22+08:00</timestamp>
  <project_name>ocap_history_expense_import</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_history_expense_import/architecture/architecture_design.md</file><file>project_workspace/ocap_history_expense_import/architecture/module_design.md</file></input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 历史支出批量导入 — 技术栈

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 | Python | 3.12（PM 环境）；CI 3.13（`.github/workflows/ci.yml`） | 沿用 | 现有后端运行时 | 全部 | 低 |
| Web 框架 | Django | `>=5.2,<6.0`（`backend/requirements.txt`） | 沿用 | 现有后端；不得用 6.x 生成迁移 | 全部 | 低 |
| API | Django REST Framework | `>=3.15,<4.0`（`backend/requirements.txt`） | 沿用 | 现有 API 层与权限类 | 全部 | 低 |
| 文件解析 | openpyxl | `>=3.1,<4.0`（`backend/requirements.txt`） | 沿用 | 收入表导入已在用；支持 xlsx 读取与模板生成 | REQ-FUNC-342/334 | 低 |
| CSV | Python 标准库 `csv` | 3.12 标准库 | 沿用 | 无新增依赖 | REQ-FUNC-343 | 低 |
| 数据库 | MySQL（测试环境）/ SQLite 内存（测试） | 画像 P7、`config/test_settings.py` | 沿用 | 现有台账与报表存储 | 全部 | 低 |
| 前端 | Vue 3 + Vite + Element Plus | `frontend/package.json` | 沿用 | 现有前端 | REQ-FUNC-342~350 | 低 |
| 前端测试 | vitest | `frontend/package.json` | 沿用 | 现有测试基线 | 全部 | 低 |
| 后端测试 | Django test runner | Django 5.2 | 沿用 | 现有测试基线 | 全部 | 低 |
| 部署 | tar + scp + systemd + nginx | 画像 P7 | 沿用 | 现有测试环境部署方式；无容器 | 全部 | 低 |

## 技术风险

| 级别 | 风险 | 缓解措施 |
|---|---|---|
| Medium | 5000 行导入在树莓派上的内存与耗时 | 逐行解析流式处理（CSV/xlsx read_only）、单事务写入、限制文件 5MB/5000 行；测试覆盖上限附近的行数 |
| Medium | 重复判定随历史数据增长变慢 | 对 `HistoricalExpenseRow(status="IMPORTED")` 建 `(batch,status)` 索引，按批次与日期范围先缩小候选，再在 Python 内比较四元组 |
| Medium | 作废后报表未及时刷新 | 复用 `void_by_source` 的 `_mark_reports_stale`；测试覆盖“作废后重新生成报表金额减少” |
| Low | 日期/金额格式因 Excel 单元格类型不同被误读 | 统一用字符串解析并兼容 `YYYY/MM/DD`；错误行提示行号，不静默改写 |
| Low | 历史导入绕过审批引发权限争议 | 后端统一 `IsIncomeMember`；审计记录操作人/批次；需求 C-377/C-378 已在页面文案中说明边界 |
| Low | 新表迁移在目标机执行失败 | 迁移手写、单 app；部署前本地 `makemigrations --check` 与测试库验证；目标机不生成迁移 |

无新增第三方依赖，因此无新增许可证/维护风险。
