<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T18:50:10+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>backend/requirements.txt</file>
    <file>frontend/package.json</file>
    <file>miniprogram/package.json</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_03,PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈 — 审批流程多步化与或/与签（ocap_approval_flow）

本批次为 INCREMENTAL，不引入任何第三方依赖，技术栈全部沿用现有项目。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言 | Python | 3.12（画像 P1；本机实测 3.14.6，画像 P4 记录） | 沿用 | 现有后端运行时 | 全部 | 本机与目标版本差异见风险 H-01 |
| 后端框架 | Django | `>=5.2,<6.0`（`backend/requirements.txt:1`；画像 P1 目标 5.2.x） | 沿用 | 现有 ORM/迁移/事务与 `select_for_update` 能力满足 REQ-NFUNC-064 | 全部 | 本机 Django 6.0.6 与约束不一致（风险 H-01） |
| API 框架 | Django REST Framework | `>=3.15,<4.0`（`backend/requirements.txt:2`） | 沿用 | 现有视图/权限/分页模式 | IFC-402~407 | 无 |
| 数据库 | MySQL（测试环境） | `mysqlclient>=2.2`（`backend/requirements.txt:7`）；画像 P7 MySQL 192.168.31.98 | 沿用 | 行锁语义按 InnoDB 设计 | REQ-NFUNC-064 | 测试用 SQLite 内存库，行锁语义弱（风险 M-01） |
| Web 前端框架 | Vue 3 | `^3.5.13`（`frontend/package.json:23`） | 沿用 | 现有管理后台与用户端 | REQ-FUNC-325、330 | 无 |
| Web UI 组件 | Element Plus | `^2.8.7`（`frontend/package.json:21`） | 沿用 | 现有表格、弹窗、表单；步骤编辑继续使用 `el-table`/`el-dialog` | REQ-FUNC-325 | 无 |
| Web HTTP | axios | `^1.7.9`（`frontend/package.json:20`） | 沿用 | 现有 `shared/api.js` 封装 | IFC-402~407 | 无 |
| 小程序框架 | uni-app (Vue 3) | `@dcloudio/uni-app ^3.0.0-4060620250520001`（`miniprogram/package.json:13`） | 沿用 | 现有小程序 | REQ-FUNC-331 | 新增页面需在 `pages.json` 注册（风险 L-01） |
| 前端测试 | vitest + @vue/test-utils | `vitest ^2.1.9`（`frontend/package.json:31`、`miniprogram/package.json:25`） | 沿用 | 画像 P4 命令 `npm test` | 全部 AC | 无 |
| 后端测试 | Django test runner | Django 内置（画像 P4：`python manage.py test --settings=config.test_settings`） | 沿用 | 现有测试体系 | REQ-NFUNC-064~065 | SQLite 并发测试需用线程/事务模拟（风险 M-01） |
| 进程管理 | systemd + gunicorn | `gunicorn>=22.0`（`backend/requirements.txt:8`）；画像 P7 | 沿用 | 现有部署 | E1/E2 | 重启窗口内审批不可用（风险 L-02） |
| 部署方式 | 物理机 tar 部署（scp → 解包 → migrate → systemd 重启） | 画像 P7 | 沿用 | 既有环境 | E1/E2 | 迁移回滚需人工（风险 M-02） |
| 容器化 | 不使用 | 画像 P8 禁用 Docker | 沿用 | 禁用项 | — | 无 |

## 技术风险

### High

| 编号 | 风险 | 缓解措施 |
|---|---|---|
| H-01 | 本机 Django 6.0.6 与 `requirements.txt` 约束 `<6.0` 不一致，可能导致本地测试通过但目标机 5.2 行为差异（尤其事务/JSONField 行为） | GROUP_C/D 记录实测版本；目标机为 Django 5.2.x；差异写入开发/测试报告；不自行降级或安装（画像 P4） |

### Medium

| 编号 | 风险 | 缓解措施 |
|---|---|---|
| M-01 | 测试环境使用 SQLite 内存库，`select_for_update` 与真实 MySQL 行锁语义不同，并发用例可能无法真实复现 | 单元测试用 `transaction.atomic` + 线程模拟并断言“只有一个推进”；E2 部署后人工并发冒烟（两名审批人同时通过）写入验证清单 |
| M-02 | 数据回填不可完全逆（多步流程回滚丢步骤数据） | 迁移前备份四张审批表；E1 部署计划标注 `[MANUAL_ROLLBACK_REQUIRED]`；回填按 flow 分批 200 |
| M-03 | 历史 `ApprovalAction` 无步骤归属，时间线归属可能不准确 | 回填 `step_order=1` 并返回 `legacy=true`；只影响升级前动作，不影响新实例 |

### Low

| 编号 | 风险 | 缓解措施 |
|---|---|---|
| L-01 | 小程序新增页面未在 `pages.json` 注册会导致构建后页面不可达 | MOD-190 明确修改 `pages.json`；GROUP_C 构建后运行小程序测试并在测试清单核对路由 |
| L-02 | 后端重启期间审批请求失败 | 沿用现有维护窗口；E2 部署后执行快速验证（登录、待办、决策） |
| L-03 | 步骤数量防御上限 50 与“无业务上限”表述有差异 | 在接口文档与错误提示中说明为安全上限；如用户要求可调整常量 |
