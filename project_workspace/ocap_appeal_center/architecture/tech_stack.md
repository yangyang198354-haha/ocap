<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-22T09:43:33+08:00</timestamp>
  <project_name>ocap_appeal_center</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_appeal_center/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_appeal_center/requirements/user_stories.md</file>
    <file>project_workspace/ocap/architecture/tech_stack.md</file>
    <file>.trae/sdlc/project_profile.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型 — 申诉与同住人申请记录中心（增量）

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | 3.12（画像 P1/P4；本机兼容性以既有后端为准） | 沿用 | 无变更 | 全部 | 低 |
| 后端框架 | Django | 5.2.x（画像 P1；`backend/` 现有配置） | 沿用 | 仅在既有 app 内新增字段与视图 | 全部 | 低 |
| API 框架 | Django REST Framework | 沿用现有（画像 P1/P4） | 沿用 | 既有 APIView 模式（`views.py`） | 全部 | 低 |
| 数据存储（生产/测试） | MySQL 8 / SQLite 内存库 | 沿用（画像 P1/P7；`config.test_settings`） | 沿用 | 只做字段新增与长度扩展；无新表 | 全部 | 低：`status` 长度 8→12 为 `AlterField`；反向迁移可能截断 `WITHDRAWN`（已标 `[MANUAL_ROLLBACK_REQUIRED]`） |
| 数据迁移 | 手写 scoped 迁移 | `backend/apps/residency/migrations/0006_appeal_center.py`（新建） | 沿用（画像 P6） | 单 app、无 `makemigrations` 全量产物（P8） | 全部 | 低 |
| 前端框架 | Vue 3 + Vite + Element Plus | 沿用现有 `frontend/package.json`（画像 P1） | 沿用 | 双 Tab 用 Element Plus `el-tabs`；无新组件库 | 全部 | 低 |
| 前端状态 | Pinia | 沿用现有 `frontend/src/stores/housing.js` | 沿用 | 记录列表与侧栏共用状态 | 全部 | 低 |
| 前端测试 | vitest + @vue/test-utils | 沿用（画像 P3/P4：`frontend/tests/*.spec.js`、`npm test`） | 沿用 | 为双 Tab、撤回/重提、实名校验补充用例 | 全部 | 低 |
| 后端测试 | Django test runner + SQLite | 沿用（画像 P4） | 沿用 | 覆盖撤回/备注/实名/聚合字段 | 全部 | 低 |
| 新增第三方依赖 | **无** | — | — | 本次仅用标准库、Django/DRF 与现有 Element Plus 能力 | — | 低 |
| 容器化 | **不使用** | — | — | 画像 P8 禁用 Docker/容器化 | — | — |
| 部署方式 | 物理机：迁移 + systemd 重启 + 前端静态产物替换 | 画像 P7 | 沿用 | 不新增运行单元 | — | 低 |

## 技术风险

### High

无。

### Medium

| 风险 | 缓解措施 |
|---|---|
| `status` 字段长度回退风险：反向迁移改回 `varchar(8)` 时 `WITHDRAWN` 可能被截断（MySQL 非严格模式）或报错（严格模式） | 迁移文件反向操作标注 `[MANUAL_ROLLBACK_REQUIRED]`；回滚前先把 `WITHDRAWN` 记录导出或改写；E1 的 ROLLBACK 步骤明确该前置检查 |
| 同住申请驳回原因改为可选，与申诉“驳回原因必填”口径不同（ADR-163/A-01） | 前端在驳回对话框提示“可填写原因”，后端同时接受旧调用；若用户要求强制必填，作为独立需求变更 |
| Element Plus Tab 切换若使用懒加载会丢失表单状态（AC-291-02/AC-295-02） | 宿主组件不使用 `lazy`，两个面板首次渲染后保持挂载；前端测试显式断言切换后已选房屋与文件仍在 |

### Low

| 风险 | 缓解措施 |
|---|---|
| 历史同住人无实名数据 | 统一显示“—”（REQ-NFUNC-060），不做数据回填 |
| 撤回记录增多导致列表截断（最近 100 条） | 沿用 `MINE_LIMIT`；空态与截断行为在测试中固定 |
| 审计 detail 中写入备注可能含敏感信息 | 备注仅用户输入文本，不写手机号/凭据；沿用 `AuditService.scrub()` |
