<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-14T00:11:53+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（INCREMENTAL）

> 本批**不新增任何第三方依赖**，不改变技术栈。版本出处均为仓库依赖清单（`文件:行`）或画像（P1/P4）；未联网查询（既有栈沿用、无新依赖，协议 §L-7 不要求）。"未知"表示仓库只给了范围、未锁定具体版本。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | CI 3.13（`.github/workflows/ci.yml:31`）；开发机 3.12（画像 P4）；测试机版本未知 | 沿用 | 新代码避免 3.13 专有语法；类静态方法不取内建类型名（M-SA-008，如 `list`/`dict`） | 全部 | 低：新增类型注解仅用 `TypedDict`、`X \| None` |
| Web 后端框架 | Django + DRF | `Django>=5.2,<6.0`（`backend/requirements.txt:1`），测试机实测 5.2.19（画像 P4）；`djangorestframework>=3.15,<4.0`（`:2`） | 沿用 | 既有视图/服务模式；新增 `MyHousingView`、`SystemLimitsView` 等沿用 `APIView` + `permission_classes` | REQ-FUNC-143 ~ 149/155/161 | 迁移不得用 Django 6.x 生成（画像 P4，CR-023）；本批迁移手写 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | 画像 P1、P7 | 沿用 | 迁移 `residency.0002_closed_status` 仅 `choices` 元数据，无 SQL；"有效记录唯一"仍用 `pending_slot` 可空槽位列（M-SA-001） | REQ-FUNC-155 | 低：回滚前须确认无 `CLOSED` 行（仅显示影响） |
| 系统配置 | `core.SystemConfig`（键值，JSON 值） | `backend/apps/core/config.py` | 沿用 | 复用 `claim.amount_max` 与可编辑端点，不建新表（ADR-085）；金额以两位小数字符串存储 | REQ-FUNC-161 | 低：读取处统一经 `SystemConfigService.amount_max()` 转 `Decimal`，损坏值回退默认 |
| 前端（Web） | Vue 3 + Vite + Element Plus + Pinia + vue-router + axios | `vue ^3.5.13`、`element-plus ^2.8.7`、`pinia ^2.1.7`、`vue-router ^4.4.5`、`axios ^1.7.9`、`vite ^6.0.1`（`frontend/package.json`，锁定的具体版本未知） | 沿用 | 确认框用 `ElMessageBox.confirm`、翻页用 `el-pagination`、日期选择 `el-date-picker`，均为已用组件（内容中心 `AdminContentPosts.vue:63-79`、清册/审计页） | REQ-FUNC-142 ~ 160 | 中：新增组合函数与公共组件需遵守主题守护测试（`ui_blocks.spec.js:98`、`qa_unit_theme.spec.js:273`） |
| 前端（小程序） | uni-app (Vue 3) + Pinia | `@dcloudio/uni-app ^3.0.0-4060620250520001`、`vue ^3.5.13`、`pinia ^2.1.7`（`miniprogram/package.json`） | 沿用 | 确认用 `uni.showModal`；选择器沿用 `picker`；加载更多用按钮 + `page/page_size` | REQ-FUNC-142 ~ 149/152/159 | 中：小程序包须人工提交体验版（画像 P7 之外的微信后台步骤）；`showModal` 不支持富文本，后果文案用换行 |
| 测试（后端） | Django test runner | 随 Django 5.2.x（画像 P4） | 沿用 | 单元/集成/E2E 位置 `backend/tests/{unit,integration,e2e}/`；远程 HTTP E2E 位 `backend/tests/remote/`，文件名 `remote_*.py` 不被默认命令收集 | REQ-NFUNC-028 | 中：远程用例须只读公开入口、只用 `e2e_` 账号（画像 P4-1） |
| 测试（前端/小程序） | vitest + @vue/test-utils + jsdom | `vitest ^2.1.9`、`@vue/test-utils ^2.4.6`、`jsdom ^25.0.1`（两个 `package.json`） | 沿用 | 新增 `frontend/tests/product_review_*.spec.js`、`miniprogram/tests/product_review_*.spec.js` | REQ-NFUNC-028 | 低 |
| HTTP 客户端（仅测试用） | `requests` | `requests>=2.31`（`backend/requirements.txt:3`） | 沿用（已在依赖清单） | 远程 E2E 用它发 HTTP 请求，避免新增依赖 | 画像 P4-1 | 低：仅在 `tests/remote/` 使用，默认命令不触发 |
| 进程管理 | systemd（`ocap-backend`、`ocap-content-worker`、`ocap-run-due-jobs.timer`） | 画像 P7 | 沿用 | 不新增服务；夹具是一次性管理命令 | — | 低 |
| CI/CD | GitHub Actions（只测试与构建，不部署） | `.github/workflows/ci.yml` | 沿用 | 新增测试文件被现有命令收集 | REQ-NFUNC-028 | 低 |
| 部署方式 | 物理机：tar 打包 → scp → 解包 → 迁移 → systemd 重启 | 画像 P7；`.claude/skills/ocap-deploy/SKILL.md` | 沿用 | 禁用 Docker、pscp 逐文件上传（画像 P8） | — | 迁移由部署流程在目标机执行 `migrate`，不在目标机生成迁移 |
| 新增依赖 | 无 | — | — | — | — | — |

## 精度/领域说明

画像 P11-2（领域算法）为"无"，本批无数值类型、定点格式或精度预算要求；金额沿用 `DecimalField(max_digits=14, decimal_places=2)`（`backend/apps/claims/models.py:14`、`ledger/models.py:10`），上限配置的取值范围与该列一致（≤ 999999999999.99，两位小数）。

## 技术风险

### High

| 风险 | 缓解措施 |
|---|---|
| 同住人链路重写 `Units.vue`（234 行）与小程序 units 页，回归面大；既有用例 mount 这些页面 | 先抽出 `UnitCascader`/`UnitPicker` 并保持既有选择行为用例通过，再叠加新功能；MOD-086 已列出需同步的既有用例；GROUP_C 在 implementation_plan 中逐页列改动前/后行为 |
| 报销/备用金创建视图权限收紧（`IsMember` → `IsCommitteeMember`）可能使既有 16 处测试调用失败，且管理员令牌由 403 变 401 | GROUP_C 先 `git grep` 逐处复核，发起人一律用 `make_seat` 造委员；契约测试已将 `IsCommitteeMember` 归入成员专属（无新增失败）；在 implementation_plan 记录管理员 401 语义变化 |
| E2E 夹具直接写 `Membership`/`Seat` 并在测试期间占用真实专有部分的户主槽位、改变"在任人数"（半数分母）；清理不彻底会污染测试环境 | 双条件护栏（昵称前缀 + 预留号段）、dry-run 默认、`status` 校验清册行数与配置默认值、账本分录保护（退出码 2）、`OCAP_E2E_FIXTURE=1` 门闩；E2E 用例约定不推进审批到通过；部署前 E2 向用户确认号段与房屋（Q-B-03） |

### Medium

| 风险 | 缓解措施 |
|---|---|
| `identity_labels` 改为取最高房屋身份，多户用户新写入的申请人/发起人快照可能与旧快照不同 | 只影响多户且角色不同的用户，方向为修正；旧记录不回填；用单元测试固化 `identity_labels` 与 `identity_view` 一致 |
| 报表明细支出行 `summary` 脱敏改变既有 API 响应值（Q-B-01 [ASSUMPTION]） | 字段保留、值置 `null`；GROUP_C 先 `git grep` 既有断言；若用户不认可，回退为仅客户端不渲染 |
| 12 个 Web 页面接入 `usePaging`、4 个小程序页接入加载更多，改动面广 | 组合函数对"数组/分页对象"两种返回都容错；页面保持 `data.results || data || []` 兼容；E2E 以 N > 20 的数据核对页合计 = 总数、无重复 |
| `GET /me/housing` 对产权业主首页多一次请求，且既有首页测试用路由表 mock | 首页对该请求 `catch` 静默；仅产权业主触发；GROUP_D 在 mock 路由表补默认值 |
| 前后端契约：新增两份 api.js 函数必须与后端路由、权限类一致（`test_frontend_contract.py`） | 所有新增调用为字面量路径、无 `?`；用户端只调 `IsMember` 族、管理端只调 `IsAdmin` 族；追加字段级契约用例（US-178） |
| 头像经 blob 显示，`URL.createObjectURL` 若不释放会泄漏 | `AuthImage` 在卸载与 `src` 变化时 `revokeObjectURL`；用例断言 |
| `claim.amount_max` 属全局配置，远程 E2E 修改它超出 P4-1 "仅 e2e_ 数据"边界 | 远程 E2E 不写全局配置，只验证默认边界；若用户要求，须明确授权放宽（Q-B-02） |

### Low

| 风险 | 缓解措施 |
|---|---|
| 迁移 `residency.0002` 若被 `makemigrations` 产物替换或在目标机生成 | 手写、文件头注明；`makemigrations --check --dry-run` 用 Django 5.2.x 检查"No changes"（画像 P4/P6/P8） |
| `POST /resident-applications` 现无限流，入口面向全体注册用户后调用量上升（Q-B-06） | 沿用"同人同房一条待审"唯一约束；下一批评估限流，本批不扩范围 |
| user_directory 与 admin_polish 的 IFC-243 ~ 246 编号重复（旧文档） | 本批引用旧接口一律带批次前缀；不改前批文档（C-41） |
| 小程序包需人工提交体验版，部署自动化覆盖不到 | 在 E1 部署计划中列为人工步骤；Web 与后端可先部署，小程序新页面在后端先行时对旧包无影响（后端只增字段、不删字段） |
