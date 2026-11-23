<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-23T22:48:59.9533029+08:00</timestamp>
  <project_name>ocap_finance_ux</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_finance_ux/architecture/architecture_design.md</file>
    <file>project_workspace/ocap_finance_ux/architecture/module_design.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 技术栈 — ocap_finance_ux

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言 | Python | 目标 3.12（画像 P1）；本机实测 3.14.6（画像 P4） | 沿用 | 现有后端运行时 | REQ-FUNC-336～339 | 本机版本高于目标，行为差异需以 CI/测试环境为准 |
| Web 框架 | Django | 目标 5.2.x；本机实测 6.0.6（画像 P4） | 沿用 | 现有 ORM/迁移体系 | 全部 | 本机版本差异，迁移语法以 5.2 兼容写法实现 |
| API 框架 | Django REST Framework | 3.17.1（画像 P4 实测） | 沿用 | 现有 `APIView` + 自定义序列化模式（`backend/apps/ledger/views.py:15-26`） | REQ-FUNC-333/336/341 | 无 |
| 数据库（测试环境） | MySQL | 8.x（画像 P7，`192.168.31.98:3306` 库 `ocap`） | 沿用 | 现有部署 | REQ-FUNC-338 | 空值唯一列需以 NULL 存储（ADR-183），避免条件唯一索引 |
| 数据库（自动化测试） | SQLite 内存库 | Django test runner（画像 P4） | 沿用 | 现有测试方式 | 全部 | 与 MySQL 的 NULL 唯一行为一致；不使用部分索引 |
| 前端框架 | Vue 3 + Vite | 现有 `frontend/package.json` | 沿用 | 现有门户与管理端 | REQ-FUNC-333/334/340/341 | 无 |
| 前端组件库 | Element Plus | 现有 `frontend/package.json` | 沿用 | 已有 `el-dialog`、`el-select`、`el-table` 用法（`frontend/src/portal/Reports.vue:1-47`） | REQ-FUNC-334 | 需覆盖默认过渡时长与焦点还原 |
| 前端测试 | vitest | 画像 P4：`frontend/` 下 `npm test` | 沿用 | 现有测试方式 | 全部 | 依赖未安装时如实 BLOCKED，不自行安装 |
| 后端测试 | Django test runner | 画像 P4：`python manage.py test --settings=config.test_settings` | 沿用 | 现有测试方式 | 全部 | 无 |
| 进程管理 | systemd `ocap-backend` | 画像 P7 | 沿用 | 现有部署方式 | 全部 | 无 |
| 前端静态服务 | nginx `:8090`（`/ocap/` 前缀） | 画像 P7 | 沿用 | 现有部署方式 | 全部 | 构建基路径必须为 `/ocap/` |
| 新增第三方依赖 | 无 | — | — | 本次功能用现有 Django/DRF/Element Plus 能力即可完成（画像 P8：不新增依赖） | 全部 | 无许可证与维护风险 |

## 技术风险

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| 存量流水迁移中断导致部分流水未归属 | High | 使用可空列 + 幂等回填（0005）分两步；迁移前数据库快照；回填后校验“未归属有效流水数=0”与收支总额差额=0.00（REQ-NFUNC-068） |
| 报表重算级联影响历史数据 | Medium | 级联只处理 `legacy=False` 的后续报表；同一事务内按时间升序；审计记录每次生成 |
| MySQL 不支持条件唯一索引导致账户号唯一性失效 | Medium | 空账户号存 NULL，依赖 `unique=True` 的多 NULL 语义（ADR-183）；服务层再做一次冲突校验 |
| 账户余额实时聚合在账户/流水增长后变慢 | Low | 现有 `(status, occurred_on)` 索引 + 新增 `(account, status, occurred_on)` 索引；如后续增长再评估缓存（ADR-182） |
| 浮层动效影响低端设备或无障碍 | Low | 过渡 240–320 ms；`prefers-reduced-motion: reduce` 时禁用位移动画；Esc 关闭与焦点还原（REQ-NFUNC-066） |
