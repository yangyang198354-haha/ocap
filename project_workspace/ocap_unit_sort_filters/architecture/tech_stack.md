<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T11:51:55+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
    <file>architecture/module_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：逐级选房排序统一、地下车位归属修正与后台清册过滤器（INCREMENTAL）

> INCREMENTAL：全部沿用画像 P1 技术栈与现有依赖，**不新增任何第三方依赖**，因此未联网查询（协议 §L-7 / 角色规则 11：不引入新依赖时通常不需要联网）。版本均取自仓库依赖清单；"实际安装版本"以画像 P4 记录为准，未另行实测。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | CI 3.13 [REPO .github/workflows/ci.yml，见画像 P4]；本机 3.12（画像 P4） | 沿用 | 无新语言特性要求；注意 M-SA-008：类内静态方法不得取内建类型名，避免 3.12/3.13 导入期错误 | 全部 | 低 |
| 后端框架 | Django + DRF | `Django>=5.2,<6.0`（`backend/requirements.txt:1`）、`djangorestframework>=3.15,<4.0`（:2）；测试机实测 Django 5.2.19（画像 P4） | 沿用 | 过滤用 ORM `Exists`/`filter`、`values_list` 即可；management command 为 Django 内置机制；不得用 Django 6.x 校验（画像 P4） | REQ-FUNC-173~184、REQ-NFUNC-032/033 | 低 |
| 排序实现 | 纯 Python 比较键（`registry/ordering.py`，仅标准库 `re`、`typing`） | 无版本（标准库） | 新增代码、无新依赖 | 一处定义、MySQL/SQLite 行为一致、可穷举单元测试（ADR-097）；不引入 `natsort` 等第三方库——该库不识别"负一"与"地下车位"分层，仍要自写规则，且新增依赖与许可证审查 | REQ-FUNC-173/174/184 | 中：规则细则（中文数字范围 0~99、保留名）要由单元测试守护 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | 测试机 MySQL 版本：未知（画像 P4/P7 未记录）；SQLite 随 Python | 沿用 | 无表结构变更、无迁移；新增查询均为通用 ORM（`Exists`、`icontains`、`select_for_update`），在两种后端行为一致；`select_for_update` 在 SQLite 上被忽略（Django 行为），故并发保护只在 MySQL 生效，测试不依赖它 | REQ-FUNC-179、REQ-NFUNC-032 | 低 |
| 数据操作载体 | Django management command ×2 | 随 Django | 沿用先例 `registry_specific_part_preview` | ADR-101：不被部署流程自动触发、可 `call_command` 测试、参数可强制 dry-run 与备份 | REQ-FUNC-178/179、C-51 | 中：依赖人工按授权执行，误操作靠参数门槛缓解 |
| 备份格式 | JSON Lines（标准库 `json`、`hashlib`） | 标准库 | 新增代码、无新依赖 | 仅含记录列、无个人信息；可在 SQLite 测试库中验证"还原后差异 0" | REQ-NFUNC-032 | 低 |
| 导出文件生成 | `openpyxl`（xlsx）、标准库 `csv` | `openpyxl>=3.1,<4.0`（`backend/requirements.txt:5`），目标机/CI 实际版本：未知 | 沿用（既有导入模板同库） | 复用 `import_template.py` 的文本列格式，保证前导零；不新增库 | REQ-FUNC-178 | 低：openpyxl 在目标机已装（导入功能依赖） |
| 前端（Web） | Vue 3 + Vite + Element Plus + Pinia + axios | `vue ^3.5.13`（`frontend/package.json:23`）、`element-plus ^2.8.7`（:21）、`vite ^6.0.1`（:30）、`axios ^1.7.9`（:20） | 沿用 | 过滤器用现有 `el-select`/`el-input`；中文占位逐控件设置（ADR-105），不引入全局 locale 包 | REQ-FUNC-180/183 | 低 |
| 前端（小程序） | uni-app（Vue 3）+ Pinia | `vue ^3.5.13`（`miniprogram/package.json:17`） | 沿用，**无源码改动** | 顺序由服务端提供，客户端不排序 | REQ-FUNC-175 | 低 |
| 测试 | Django test runner（后端）、vitest（前端/小程序） | `vitest ^2.1.9`（`frontend/package.json:31`、`miniprogram/package.json:25`） | 沿用 | 位置遵守画像 P3：`backend/tests/{unit,integration,e2e}`、`frontend/tests/*.spec.js`；两条数据命令只用 SQLite 合成数据 | 全部 | 低 |
| 进程管理 / 部署 | systemd `ocap-backend`；tar→scp→解包→迁移→重启（无容器） | 画像 P7 | 沿用 | 无新服务；本批**无迁移**；两条命令不进入部署脚本 | — | 低 |
| CI/CD | GitHub Actions（只测试与构建） | 画像 P7 | 沿用 | 不改 `.github/workflows/ci.yml` | — | 低 |
| 新增依赖 | 无 | — | — | 角色规则：INCREMENTAL 尽量不新增 | — | — |

## 数值与数据口径

| 项 | 口径 | 依据 |
|---|---|---|
| 数字比较 | 任意长度整数，Python `int`（无溢出）；中文数字仅解析 0~99 | ADR-098 |
| 文字比较 | Unicode 码位序（Python `str` 比较），不做拼音/笔画排序 | REQ-FUNC-174 "文字段按字符顺序" |
| 面积导出 | 按库内 `Decimal(10,2)` 的字符串原样输出，不做浮点转换 | AC-187-01（逐单元格一致） |
| 计数一致 | 导出文件与库的专有部分数、有名业主数、去重手机号数逐项相等（差 0） | REQ-NFUNC-032 |

## 技术风险

### High
无。

### Medium
| 风险 | 说明 | 缓解 |
|---|---|---|
| R1 负层写法未被识别导致 AUTH-02 漏改 | 规则只识别 "-1"、"负1"、"负一"、"负一层" 及其数值等价写法；`B1`、`地下1层` 等不识别（OQ-02） | dry-run 输出车位类全部楼层写法及识别结果（Q-SF-02b-2）；授权后由用户核对再 `--apply`；如有未识别写法，回 GROUP_B 补规则 |
| R2 库内存在模板无法表达的记录 | 无有名业主的专有部分、姓名为 NULL 的遗留业主，导出文件放不下（OQ-01），会使"导出与库差 0"不成立 | 默认停止导出并报告 id 与计数；用户决定接受差异（`--allow-gaps`）或先补登 |
| R3 导出文件含个人信息且需求口径冲突 | Q-SF-13=B（放仓库根并提交）与已批准 C-55/AC-187-06（不得入库）字面冲突，仓库为公开仓库（OQ-03） | 本设计不含 git 操作；请 PM 先收敛需求口径；命令侧缓解：0600 权限、只写计数不写姓名手机号；建议用户在提交前再次确认 |
| R4 两条命令靠人工授权执行 | 无技术手段阻止拥有 shell 的人运行 | dry-run 默认、`--apply` 需 `--backup`+`--expect-changes`；不加入部署脚本；执行记录写审计（AUTH-02）与运维日志 |
| R5 自然顺序规则的排序在两处"已认证房屋"与旧测试断言不一致 | `test_identity_display.py:118-125` 等按旧文本序断言 | module_design"既有测试影响"清单，GROUP_C 同步更新 |

### Low
| 风险 | 说明 | 缓解 |
|---|---|---|
| R6 排序与过滤在内存/`icontains` 上的开销 | 清册为千行级、上限 20000 行 `[ESTIMATE]`，Q-SF-12=A 不设性能指标 | 不需处理；规模显著增长时再评估 |
| R7 MySQL 精确匹配不区分大小写与尾空格 | `building="A"` 也命中 `a` | 楼栋、单元多为数字，可接受（ADR-100 已列） |
| R8 "-1" 与 "负一" 并存 | 下拉出现两个相邻项 | 不合并（避免改数据）；数据核对时由用户决定是否另行规范化 |
| R9 其他页面仍有 Element Plus 英文内置文案 | 本批只处理新增/调整的过滤器 | OQ-04，另立需求 |
