<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-27T09:01:31.6049532+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录技术栈

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言 | Python | 目标 3.12（画像 P1）；开发机实测 3.14.6（画像 P4） | 沿用 | 现有 Django 项目运行时 | REQ-FUNC-385、388 | 开发机与目标大版本存在差异，须运行现有测试 |
| 后端框架 | Django | `>=5.2,<6.0`（`backend/requirements.txt:1`） | 沿用 | 使用现有 ORM 查询和事务数据，无 schema 变更 | REQ-FUNC-385～389 | 低 |
| HTTP API | Django REST Framework | `>=3.15,<4.0`（`backend/requirements.txt:2`） | 沿用 | 复用 APIView、权限与 Response | REQ-FUNC-385～389 | 低 |
| 数据存储 | MySQL / SQLite 测试库 | 具体版本未知；用途见画像 P1/P4 | 沿用 | 只读查询现有审批和申请记录 | REQ-FUNC-385～389 | 不同数据库上的去重与排序须由集成测试覆盖 |
| Web 前端 | Vue | `^3.5.13`（`frontend/package.json:23`） | 沿用 | 在现有 Tasks/UnitsReview 组件内增量实现 | REQ-FUNC-385～389 | 条件渲染不得留下历史写操作入口 |
| UI 组件 | Element Plus | `^2.8.7`（`frontend/package.json:21`） | 沿用 | 复用现有列表、标签、分页和对话框 | REQ-FUNC-385～388 | 低 |
| 前端状态/请求 | Pinia、Axios | `^2.1.7`、`^1.7.9`（`frontend/package.json:20,22`） | 沿用 | 复用 housing store 与 `shared/api.js` | REQ-FUNC-388、389 | 不扩大现有 store 的数据范围 |
| 后端测试 | Django test runner | 随 Django；命令见画像 P4 | 沿用 | SQLite 内存库真实执行权限、筛选与契约用例 | REQ-FUNC-385～389 | 必须区分既有失败与本批新增失败 |
| 前端测试 | Vitest | `^2.1.9`（`frontend/package.json:31`） | 沿用 | 验证视图切换、空态、字段与只读性 | REQ-FUNC-385～389 | API mock 不得替代后端权限测试 |
| CI/CD | GitHub Actions | 工作流 `.github/workflows/ci.yml`，分支 `main`（画像 P7） | 沿用 | 只跑测试和构建，不部署 | 全部 | 不新增部署触发 |
| 部署方式 | tar 物理机发布 + systemd + nginx | 无新增版本；画像 P7 | 沿用 | 符合现有树莓派测试环境；本轮只出计划 | 全部 | 需用户另行授权后才可执行 |
| 新增依赖 | 无 | 不适用 | — | 现有框架足以实现 | 全部 | 无新增许可证或维护风险 |

## 技术风险

### High

| 风险 | 缓解措施 |
|---|---|
| 已处理查询误用审批人名单或整单处理人，导致未操作记录混入或越权 | 强制以 `ApprovalAction.actor + action` 过滤；覆盖“仅被指定”“只有他人操作”“多步前序已办”和直接详情 403 用例 |
| 同住人历史使用 `decided_by` 代替当前产权，离任或产权变更后泄露记录 | 每次请求从有效 `HEAD`/`OWNER` Membership 计算专有部分集合，并验证非产权用户不可见 |

### Medium

| 风险 | 缓解措施 |
|---|---|
| 同一实例多次本人动作造成重复行或摘要不是最近动作 | 实例去重、明确最近动作排序键，并以双动作/分页用例验证总数与无重复 |
| handled 分支改变缺省待办行为 | 缺省和显式 `view=todo` 均执行回归测试；待办响应字段与操作入口保持不变 |
| 申请人和审批人列表共用序列化时误改本人记录范围 | 仅共享字段序列化，不共享查询集；保留 `applicant=request.user` 的独立回归用例 |

### Low

| 风险 | 缓解措施 |
|---|---|
| 历史列表数据量增长导致查询或分页缓慢 | 使用关系过滤、去重和必要预取；本批不新增未评估的索引，若后续出现实际性能指标再单独设计 |
| 工作区已有收入表等未提交改动，编辑共享 `api.js` 时可能覆盖 | 只做局部追加，门控逐项比较 diff，不回退或重排无关内容 |
