<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-10T22:02:14+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.2.0 DRAFT)</file>
    <file>architecture/module_design.md (0.2.0 DRAFT)</file>
    <file>../ocap/architecture/tech_stack.md (基线)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：业主清册导入增强（INCREMENTAL）

> 增量原则：沿用画像 P1 技术栈，**不新增任何第三方依赖**（后端、Web 前端、小程序均无）。画像 P8 禁用项（Docker、pscp、makemigrations 产物、改 Freeark）均未出现在选中方案中。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 / 后端框架 | Python + Django 5.2.x + DRF 3.x | `Django>=5.2,<6.0`（`backend/requirements.txt:1`）、`djangorestframework>=3.15,<4.0`（`:2`）；测试机实测 Django 5.2.19（画像 P4） | 沿用 | 既有栈；迁移须用 5.2.x 生成/校验，不得用 6.x（画像 P4、CR-023） | 全部 | 低 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | `mysqlclient>=2.2`（`requirements.txt:7`） | 沿用 | 新增 `RegistryOwner` 表与 `RegistryUnit` 两列；约束设计避开 MySQL 忽略条件索引的问题（ADR-035） | REQ-FUNC-087/088/089 | 中：R4（迁移）、R10（大小写） |
| 金额/面积类型 | `DecimalField(max_digits=10, decimal_places=2)` | Django 内置 | 沿用 | 面积平方米 2 位小数，避免浮点误差（ADR-036） | REQ-FUNC-089 | 低 |
| 文件解析 | `openpyxl` read_only 模式 + 标准库 `csv` | `openpyxl>=3.1,<4.0`（`requirements.txt:5`）；PyPI 最新 3.1.5，MIT 许可证 `[WEB: https://pypi.org/pypi/openpyxl/json，2026-11-10]`；本机未安装，实际版本以目标机 `pip show` 为准（未知） | 沿用（已在用，`views.py:198-209`） | 流式读取控制内存；同一库生成模板；无需 pandas（ADR-039） | REQ-FUNC-083、REQ-NFUNC-013/015 | 低：R6 |
| 模板生成 | `openpyxl` `Workbook`（含文本格式列、数据验证）+ 标准库 `csv` | 同上 | 沿用 | 后端单一来源，按需生成（ADR-041） | REQ-FUNC-085 | 低：R8 |
| 批量写入 | Django ORM `bulk_create` / `bulk_update` / `filter(__in)` 分批 | Django 内置 | 沿用 | 在 MySQL 与 SQLite 上行为一致；不使用 MySQL 专有 `LOAD DATA`（ADR-038） | REQ-NFUNC-015 | 中：R3（实测未做） |
| 超时控制 | `time.monotonic()` 软期限 + 单事务回滚 | 标准库 | 沿用 | ADR-040 | REQ-NFUNC-015 | 高：R1 |
| 后端接口 | DRF `APIView` + `ApiError` 统一错误体 | `backend/apps/core/errors.py:6-31` | 沿用 | 与全部既有接口一致 | — | 低 |
| 鉴权 | `IsAdmin`（管理端）、`IsMember`（用户端） | `backend/apps/core/permissions.py:19-24`、`registry/views.py:28` | 沿用 | 新接口全部沿用，无新权限 | REQ-FUNC-084/085 | 低 |
| 审计 | `AuditService.record`，动作 `REGISTRY_IMPORTED`、`REGISTRY_UNIT_CHANGED`、`CERTIFY_BY_REGISTRY` | `backend/apps/core/audit.py:11-15` | 沿用 | 动作白名单已含所需动作，**不新增动作** | REQ-NFUNC-014 | 低 |
| Web 前端 | Vue 3 + Vite + Element Plus + axios | `vue ^3.5.13`、`element-plus ^2.8.7`、`axios ^1.7.9`、`vite ^6.0.1`（`frontend/package.json:13-16,23`） | 沿用 | 导入对话框、表格、下载均可用既有库完成；Blob 下载用浏览器原生 API | REQ-FUNC-083~085/093/095 | 低 |
| 小程序 | uni-app (Vue 3) + Pinia | `@dcloudio/uni-app ^3.0.0-4060620250520001`、`vue ^3.5.13`（`miniprogram/package.json:13,17`） | 沿用 | 仅改既有两页 | REQ-FUNC-091/096/097 | 中：R9 |
| 测试 | 后端 Django test runner（SQLite）；前端/小程序 vitest | 画像 P4 | 沿用 | 新增用例位置遵循画像 P3：`backend/tests/{unit,integration,e2e}/`、`frontend/tests/*.spec.js`、`miniprogram/tests/*.spec.js` | 全部 | 低 |
| 进程管理 | systemd `ocap-backend`（gunicorn）、nginx | 画像 P7；gunicorn `>=22.0`（`requirements.txt:8`） | 沿用 | 无新服务、无新进程、无队列（同步处理，Q-RI-22=A） | REQ-NFUNC-015 | 高：R1、R2 |
| CI/CD | GitHub Actions `.github/workflows/ci.yml`（只测试与构建） | 画像 P7 | 沿用 | 无变更 | — | 低 |
| 部署方式 | 物理机：tar → scp → 迁移 → systemd 重启；不用容器 | 画像 P7；`.claude/skills/ocap-deploy/SKILL.md` | 沿用 | 增加 nginx/gunicorn 超时与体积核实步骤（E1 阶段） | REQ-NFUNC-015 | 高：R1 |
| 新增依赖 | **无** | — | — | pandas、SheetJS、任务队列均已评估并排除（ADR-039、041、040） | — | — |

## 数值与精度（面积）

画像 P11-2（领域算法）为"无"，不适用算法精度预算；本项目只有面积的存储精度：`Decimal`，2 位小数，输入拒绝超过 2 位小数的值而不是四舍五入（AC-096-04）；上限为列定义边界 99,999,999.99。

## 技术风险

### High

| 编号 | 风险 | 缓解 |
|---|---|---|
| R1 | **目标机超时与体积配置未核实**（不在仓库内）：gunicorn 默认 `--timeout` 30 秒会在 30 秒时杀掉 worker；nginx 默认 `proxy_read_timeout` 60 秒、`client_max_body_size` 1m，会使 5 MB 文件得到 413、接近 60 秒的导入得到 504。外网入口（VPS nginx + frp、Freeark nginx `^~ /ocap/`）另有同类配置，**不在本次范围，列为已知限制**（Q6=B） | **GROUP_E1 须**：(1) 在 deployment_plan 列出只读核实清单（`ocap-backend.service` 的 `ExecStart` 中 `--timeout`/`--workers`/worker 类型；ocap 站点 8090 的 `client_max_body_size`、`proxy_read_timeout`、`proxy_send_timeout`），(2) 给出调整方案（目标：gunicorn `--timeout 90`；nginx `proxy_read_timeout 90s` / `proxy_send_timeout 90s` / `client_max_body_size 6m`；改前备份，`nginx -t` 后 `reload`，含验证与回滚），(3) 范围仅限画像 P7 允许的 `ocap-backend` 单元与 ocap 站点 8090，**不得触碰 Freeark 的服务、端口、nginx 配置**。子代理不得 ssh（P9），只读核实由 PM 只读 ssh 或 E2 预检执行，调整仅在 E2 经用户授权后执行；软期限（60 秒）小于外层（90 秒）保证友好提示。验收只在内网入口 `http://192.168.31.51:8090/ocap/` |
| R2 | gunicorn worker 数与类型未知：若仅 1 个同步 worker，一次最长 60 秒的导入会让整个后端对其他用户无响应；Q-RI-23 默认"单管理员无并发"若被改为有并发，60 秒指标需重估 | 同 R1，E1 的核实清单必须包含 `--workers`，建议 ≥2（树莓派 4 GB，每 worker 内存按实测）；前端导入期间禁用重复提交；服务端并发导入以唯一约束兜底并返回 `IMPORT_CONFLICT`；导入限定管理员，频率低 |

### Medium

| 编号 | 风险 | 缓解 |
|---|---|---|
| R3 | 20000 行/60 秒仅为估算（约 25 秒，`[ESTIMATE]`），尚无实测；MySQL 延迟决定写入耗时 | 开发阶段在 SQLite 上断言总查询数 ≤ 300（防止算法退化为逐行 ORM）；GROUP_D / E1 在测试环境用合成的 20000 行文件（含 10% 失败行，AC-100-07/08）实测并记录耗时；若余量 < 2 倍则调大批次或优化 |
| R4 | 迁移风险：MySQL 的 DDL 不可事务回滚；加宽 `specific_part` 唯一索引列；回填脚本逐条创建业主，既有手机号行数未知；撤销迁移丢失新数据 | 拆为 3 个小迁移；回填逻辑写成可直接调用的函数并单测（测试环境不跑迁移）；迁移前 `mysqldump` 三张 registry 表；回滚标 `[MANUAL_ROLLBACK_REQUIRED]`；部署前 `makemigrations --check --dry-run` 无漂移（SKILL §4 第 7 项） |
| R5 | 库中存在 `name IS NULL` 的业主（ADR-037，迁移遗留；PM 落地口径待用户确认）：所有读写路径都要处理；导入的"吸收"规则是额外分支 | 序列化器输出 `name: null`，前端显示"（未登记姓名）"；不提供补名界面，统一上传即补名；吸收规则（补名、并入、删除空业主）单独单测；用户若改口径为 B，仅改 0003 回填与吸收规则 |
| R9 | 小程序 `picker` 无搜索，车库类楼栋下户号可达数千，末级选择体验差；Web 用 `filterable` 缓解但小程序无法 | 先按需求交付；测试阶段记录；后续可把末级改为输入过滤（需求外，建议单独立项） |
| R11 | 既有测试大量直接构造 `RegistryPhone`/调用 `/phones`，需同步修改（module_design"既有测试影响"清单），否则基线出现新增失败 | GROUP_C 先改夹具 `tests/support.py` 再改用例；PM 复跑全量，目标仍为零新增失败 |

### Low

| 编号 | 风险 | 缓解 |
|---|---|---|
| R6 | xlsx "解压炸弹"：5 MB 压缩文件展开后可能很大；`read_only` 的 `dimensions` 元数据有时不准 | 只用 `iter_rows` 流式遍历，读满 20001 个数据行即停；限制读取的列数（仅前 N 列）；总处理受 60 秒软期限约束 |
| R7 | Excel 中文版另存的"CSV（逗号分隔）"为 GBK，解码失败 | "填写说明"与页面格式说明提示选择"CSV UTF-8"，或直接用 xlsx；错误提示"文件无法解析"后附该提示 |
| R8 | 管理员忘记删除模板示例行就上传，示例数据进入清册 | 说明页首行提示；预检结果展示将新增的专有部分数，便于发现异常；示例使用明显虚构的编号与手机号 |
| R10 | MySQL 默认排序规则大小写不敏感，而 Python 比较默认敏感，可能导致批量写入撞唯一约束 | 计划阶段的键统一 `casefold()`（architecture_design A-3）；撞约束时回滚并返回 `IMPORT_CONFLICT`，不产生脏数据 |
| R12 | 逐级选择接口参数语义变化（空串 = "选了无"） | 已有客户端只传非空值，不受影响；契约测试 `test_frontend_contract.py` 覆盖路径与方法；新增用例覆盖空串语义 |
