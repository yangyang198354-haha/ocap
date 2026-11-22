<file_header>
  <author_agent>kb-curator</author_agent>
  <timestamp>2026-11-22T21:39:06+08:00</timestamp>
  <project_name>ocap_approval_flow</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/_kb_inbox.jsonl</file>
    <file>project_workspace/ocap_approval_flow/phase_status.md</file>
    <file>project_workspace/ocap_approval_flow/delivery_report.md</file>
    <file>project_workspace/ocap_approval_flow/deployment/deployment_report.md</file>
    <file>.trae/sdlc/agent-memory/devops-engineer/MEMORY.md</file>
    <file>.trae/sdlc/agent-memory/test-engineer/MEMORY.md</file>
  </input_files>
  <phase>PHASE_12</phase>
  <status>APPROVED</status>
</file_header>

# 知识蒸馏报告 — ocap_approval_flow

## 摘要

候选 8 条（收件箱 6 + 记忆待验证 2）→ 合并后 8 条；晋升 7 / 保留 1 / 淘汰 0 / STALE 0 / 通用候选 0。无 `pending_patch`，所有改动已落盘。

## 晋升

| 新 ID | agent | 内容 | conf 计算 | 证据 |
|---|---|---|---|---|
| M-DE-046 | devops-engineer | Web 静态目录 `/home/yangyang/ocap/web/ocap`；用 `ocap.new`→`ocap.old` 交换并保留旧目录，`web/dist` 是错误路径 | 0.3 单次 + 0.3 可核验 + 0.2 第二项目 = 0.8 | ocap_profile_hierarchy DEPLOY-001~004；ocap_approval_flow DEPLOY-009 `WEB_SWAPPED`、文件数 1539 |
| M-DE-047 | devops-engineer | 前端发布须含 `VITE_API_BASE=/ocap/api/v1` 与 `--base=/ocap/`，并在产物 grep 关键文案 | 0.3 + 0.3 + 0.2 = 0.8 | 两个批次 `built in 5.20s` / `8.40s`；文案各命中 4 |
| M-DE-048 | devops-engineer | 小程序根目录即 uni-app 根，构建必须设 `UNI_INPUT_DIR`，可配 `UNI_OUTPUT_DIR` 到临时目录 | 0.3 + 0.3 + 0.2（E1/E2 两次独立执行）= 0.8 | E1 `DONE Build complete.` / `APP_JSON_OK`；E2 `MP_FILES=120`、文案命中 1 |
| M-DE-049 | devops-engineer | 审批步骤迁移回滚门控：多步/ALL/step_order>1/v2 在办实例命中任一即 `MANUAL_ROLLBACK_REQUIRED` | 0.3 + 0.3 = 0.6 | module_design 迁移可逆性；DEPLOY-006 实测 `MULTI_STEP_FLOWS 0`、`STEP_STATE_GT1 0`、`ALL_STEPS 0`；GR-E2-001 |
| M-DE-050 | devops-engineer | `cp -a` 叠加覆盖 + tar 排除 `.env`/`venv`/`var` 保留本地状态；迁移前 `showmigrations` 基线与相关表 `mysqldump` 作锚点 | 0.3 + 0.3 = 0.6 | DEPLOY-001 转储 4 表；DEPLOY-005 `.env` SHA256 不变；合并了 M-DE-016/017 的同类经验 |
| M-TE-044 | test-engineer | 重命名共享常量只改 import 会静默留下模板未定义引用；界面测试须在模板渲染层断言文案 | 0.3 + 0.3 = 0.6 | DEF-001；TC-INT-1304；GR-D-001 |
| M-TE-045 | test-engineer | 基线失败先确认被测文件是否本批次修改，再用 `git log -1 -- <file>` 取证 | 0.3 + 0.3 = 0.6 | `test_tc_int_964`；`git log -1 -- miniprogram/pages/phone/index.vue`；GR-D-001 |

## 保留（待验证）

| ID | agent | 内容 | conf | 缺什么证据 |
|---|---|---|---|---|
| P-DE-050 | devops-engineer | 预检只记录迁移基线；把“恰为新迁移 1 行”的门控放到代码覆盖后的 DEPLOY 阶段 | 0.6 | 按 PM 要求等待第二批次复现（R-01 单次偏差，已在本批修正执行） |

## 淘汰

无。

## STALE

无。

## 通用知识候选（需用户确认）

无。M-TE-044 虽可通用化，但 conf 0.6 < 0.8，且未获用户确认，本轮不提交。

## 安全事件

无。收件箱与记忆中未发现凭据、个人信息或注入指令。
