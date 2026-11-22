<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-22T21:37:18+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_approval_flow/phase_status.md</file>
    <file>project_workspace/ocap_approval_flow/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_approval_flow/testing/e2e_test_report.md</file>
    <file>project_workspace/ocap_approval_flow/deployment/deployment_report.md</file>
  </input_files>
  <phase>PHASE_12</phase>
  <status>APPROVED</status>
</file_header>

# 交付报告 — 审批流程多步化与或/与签（ocap_approval_flow）

## 交付摘要

| 项 | 内容 |
|---|---|
| 模式 | INCREMENTAL（画像 1.2.0） |
| 阶段 | GROUP_A~E2 全部 APPROVED；GR-A-001、GR-B-001、GR-C-001、GR-D-001、GR-E1-001、GR-E2-001 均 PASS |
| 提交 | `30d9f27`，已推送 `origin/main` |
| 部署 | 测试环境（树莓派 `192.168.31.51`，内网 8090 / 外网 `https://ai-freeark.xin/ocap/`），`DEPLOYED_SUCCESSFULLY`，停机约 77 秒 |
| 数据库 | 仅应用 `approval.0003_approval_steps`；新表 3 张、加字段 2 张；回填 2 个指定负责人流程为 1 步 |

## 需求实现

1. **或签 / 会签**：流程每一步可设 `ANY`（任一通过）或 `ALL`（全部同意）。或签部分拒绝不终局、全部拒绝才失败；会签任一拒绝即该步失败。
2. **多步流程**：管理后台可创建最多 50 步（防御上限），每步可命名、设策略与审批人；旧流程迁移后折算为 1 步，保持兼容。
3. **审批过程可见**：新增只读时间线 `GET /approval/instances/{id}`，展示每步名称/策略/到达时间、审批人、动作与批准备注；权限为管理员、发起人、当前及历史步骤审批人。

覆盖端：Web 管理后台、Web 用户端、微信小程序。

## 质量结果

| 层 | 结果 |
|---|---|
| 后端 | `Ran 1186 tests`（+19 新写）→ `OK (skipped=2)`；原预存在失败 `test_tc_int_964` 已随 f7316cb 页面拆分同步修复 |
| Web 前端 | `52 files / 581 tests passed`（+13）；`npm run build` 成功 |
| 小程序 | `21 files / 151 tests passed`（+13）；`build:mp-weixin` 设 `UNI_INPUT_DIR` 后成功 |
| critical path | 11/11 Must Have 故事有已执行用例（100%） |
| 缺陷 | DEF-001（MAJOR，时间线模板旧常量）已修复并复测 |
| 部署验证 | V-01~V-11 全 PASS；日志无新错误；新路由 401；Web/外网 200 |

## 部署与回滚

- 回滚锚点：`TS=20261122213109`（后端/Web 快照、4 张审批表转储、迁移计划、nginx 备份），另保留 `web/ocap.old`。
- 回滚安全条件实测：多步流程 0、`step_order>1` 0、`ALL` 步骤 0。部署后如用户创建多步/会签流程，反向迁移转人工（`[MANUAL_ROLLBACK_REQUIRED]`）。
- 计划偏差：DEPLOY-003 一次文件名笔误（无目标机变更后重跑）；PRE-07 迁移门控应在代码覆盖后执行（R-01）。已记录在部署报告。

## 遗留与后续

| 编号 | 事项 | 责任方 |
|---|---|---|
| O-01 | 人工验证 MV-01~MV-06（含双窗口并发会签） | 用户 |
| O-02 | 小程序在微信开发者工具确认后上传体验版 | 用户 |
| O-03 | GitHub Actions 对 `30d9f27` 的结果确认（本地门控已通过） | 用户/CI |
| O-04 | 验收后清理 `web/ocap.old` 与快照（建议保留 ≥ 7 天） | 运维 |
| O-05 | 后续批次修订 PRE-07 措辞：预检记录基线，迁移门控放 DEPLOY 阶段 | 流程改进 |

## 产物索引

- 需求：[requirements_spec.md](requirements_spec.md)、[user_stories.md](requirements/user_stories.md)
- 架构：[architecture_design.md](architecture/architecture_design.md)、[module_design.md](architecture/module_design.md)、[tech_stack.md](architecture/tech_stack.md)
- 开发：[implementation_plan.md](development/implementation_plan.md)、[code_review_report.md](development/code_review_report.md)
- 测试：[test_plan.md](testing/test_plan.md)、[unit_test_report.md](testing/unit_test_report.md)、[integration_test_report.md](testing/integration_test_report.md)、[e2e_test_report.md](testing/e2e_test_report.md)
- 部署：[cicd_pipeline.md](deployment/cicd_pipeline.md)、[deployment_plan.md](deployment/deployment_plan.md)、[deployment_report.md](deployment/deployment_report.md)
- 状态：[phase_status.md](phase_status.md)
