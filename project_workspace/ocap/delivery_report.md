<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-09T00:20:48+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files><file>phase_status.md</file><file>development/code_review_report.md</file><file>testing/e2e_test_report.md</file><file>deployment/deployment_report.md</file></input_files>
  <phase>PHASE_01,PHASE_02,PHASE_03,PHASE_04,PHASE_05,PHASE_06,PHASE_07,PHASE_08,PHASE_09,PHASE_10,PHASE_11a,PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# ocap 交付报告

## 项目概览
- 需求：业主委员会 Web 应用与微信小程序，包括注册登录、业主清册认证、户主/同住人/游客身份、业委会决议、报销与备用金、收入与报表、投票与调查。
- 模式：FULL_FLOW。本轮（2026-11-08）为 PARTIAL_FLOW 复核与返工，起点是用户要求"review 评审代码，看是否完整实现。然后执行所有测试，重新部署一遍，如果还没有 claude 版本的部署 skill 也写一下"。
- 画像：`.claude/agents/project_profile.md` 1.3.0，以 Trae 画像 1.2.0 为底稿修订。
- 起止：2026-11-07 17:02 至 2026-11-09 00:20；本轮 2026-11-08 12:57 至 2026-11-09 00:20。
- **最终状态：DELIVERED_WITH_ISSUES**。原因有三：存在 5 项待人工验证（含 critical path）；有开放的 conditions；本轮代码改动尚未提交和推送。

## 阶段执行摘要（本轮）

| GROUP | 阶段 | 代理 | 状态 | 门控 | 重试 | 回流 | 完成时间 |
|---|---|---|---|---|---|---|---|
| C | 06 完整性复核 | software-developer | — | GR-C-004 FAIL（4 CRITICAL / 9 MAJOR） | — | — | 11-08 13:08 |
| E1 | 11a Claude 版部署 skill | devops-engineer | APPROVED | GR-E1-002 PASS | 0 | — | 11-08 13:1x |
| C | 05/06 返工 CR-011~024 | software-developer | APPROVED | GR-C-005 PASS_WITH_CONDITIONS | 3（经用户同意超限） | — | 11-08 13:50 |
| D | 07–09 重测（D-6 因限额中断，由 D-7 续跑） | test-engineer | — | GR-D-006 FAIL（11 个 Must Have 无用例；DEF-005） | — | — | 11-08 23:02 |
| C | DEF-005 | software-developer | APPROVED | GR-C-006 PASS_WITH_CONDITIONS | — | 3 | 11-08 23:1x |
| D | 补测 11 个故事 | test-engineer | — | GR-D-007 FAIL（DEF-006 安全缺陷） | — | — | 11-08 23:30 |
| C | DEF-006 + OBS-001 | software-developer | APPROVED | GR-C-007 PASS_WITH_CONDITIONS | — | 4（经用户同意超限） | 11-08 23:3x |
| D | 定稿 | test-engineer | APPROVED | GR-D-008 PASS_WITH_CONDITIONS | 3 | 4 | 11-08 23:4x |
| E1 | 10/11a 计划增量与 systemd timer | devops-engineer | APPROVED | GR-E1-003 PASS_WITH_CONDITIONS | 0 | — | 11-08 23:4x |
| E2 | 11b 测试环境部署 | devops-engineer | APPROVED | GR-E2-002 PASS | 0 | — | 11-09 00:1x |

## 质量指标（threshold 模式，数值均为 PM 亲自复跑结果）

| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 单元通过率 | 74/74 = 100%（后端 42、Web 19、小程序 13） | ≥ 0.80 | ✓ |
| 集成通过率 | 182/182 = 100%（后端 148、Web 17、小程序 17） | ≥ 0.90 | ✓ |
| E2E critical path 通过率 | 16/16 = 100%（另有 5 项 NOT_TESTABLE） | ≥ 1.00 | ✓ |
| Must Have 故事有执行用例 | 69/69 | 全部 | ✓ |
| 代码评审未解决 CRITICAL | 0 | 0 | ✓ |
| 全量回归新增失败 | 0（共 278 个：后端 212、Web 36、小程序 30） | 0 | ✓ |

## 本轮关键结论
1. **完整性复核**发现，远端交付"测试全过"只代表后端 API 正常，前后端契约从未验证过。复核时 REQ-FUNC 共 68 条，其中 28 条 PARTIAL、2 条 MISSING；US 共 73 个，其中 29 个 PARTIAL、3 个 MISSING。
2. 已修复的问题：
   - CR-011~024：账号合并接入、/me identities 契约、报销/核销、投票、收入导入规则、备用金核销计账、季报/年报定时生成、手机号绑定 UI、小程序密码登录等；
   - CR-023：claims/income/ledger 三个 0003 迁移改为手写，AST 与原文件等价；
   - DEF-005：死代码导致的契约失败；
   - **DEF-006**：验证码输错 5 次后仍然有效，属安全缺陷；
   - OBS-001：匿名请求访问管理端时改为返回 401。
3. 新增 11 个前后端契约测试（解析 api.js 并 resolve 到后端路由）。Web 与小程序的 vitest 从 0 个用例增加到 66 个。

## 交付物清单

| 文件 | 生成代理 | 最终版本 | 状态 |
|---|---|---|---|
| requirements/requirements_spec.md | requirement-analyst | 5.0.0 | APPROVED |
| requirements/user_stories.md | requirement-analyst | 3.0.0 | APPROVED |
| architecture/architecture_design.md、module_design.md、tech_stack.md | system-architect | 1.0.0 | APPROVED |
| development/implementation_plan.md | software-developer | 4.0.0 | APPROVED |
| development/code_review_report.md | software-developer | 4.0.0 | APPROVED |
| testing/test_plan.md、unit/integration/e2e_test_report.md | test-engineer | 1.0.0 | APPROVED |
| deployment/cicd_pipeline.md | devops-engineer | 2.0.0 | APPROVED |
| deployment/deployment_plan.md | devops-engineer | 2.0.0 | APPROVED |
| deployment/deployment_report.md | devops-engineer | 2.0.0 | APPROVED |
| `.claude/skills/ocap-deploy/SKILL.md` | devops-engineer | — | GR-E1-003 核验 |
| `deploy/systemd/ocap-run-due-jobs.{service,timer}` | devops-engineer | — | 已部署 |
| `.claude/agents/project_profile.md` | pm-orchestrator | 1.3.0 | APPROVED |

**代码改动尚未提交**：已提交的 eeb6063 与 c0d1f0a 也都还没有推送。c0d1f0a 之后的工作树改动如下，需用户确认后再提交：
- `frontend/src/shared/api.js`（DEF-005）
- `backend/apps/accounts/services.py`、`backend/apps/core/permissions.py`（DEF-006、OBS-001）
- `backend/tests/integration/test_gap_must_have.py`、`backend/tests/e2e/test_gap_journeys.py`、`frontend/tests/login.spec.js`、`miniprogram/tests/pages.spec.js`
- `deploy/systemd/*`、`.claude/skills/ocap-deploy/SKILL.md`
- 各阶段文档、`phase_status.md`、本报告、`pm_escalation_GROUP_D_*.md`
- agent 记忆、`_kb_inbox.jsonl`

## 遗留问题

| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| 24 个 Must Have 故事没有 E2E 旅程，只有单元和集成覆盖（E2E 覆盖 45/69） | GR-D-008-F02 | MINOR | 下一轮补多步旅程 |
| CR-025：部分接口路由和签名与 module_design 不一致（IFC-110/111/112/120/132/133/140） | code_review_report §8 | MINOR | 由架构师决定改设计还是改代码 |
| CR-026：微信头像未迁移（`TODO(IFC-027)` [UNSOURCED]） | code_review_report §9 | MINOR | 需要微信文档出处 |
| CR-027 / A-10：作废后锁定响应中的 retry_after 固定为 1 | GR-C-007-F01 | MINOR | 改为返回剩余锁定时长 |
| D-05：投票截止前查看结果返回 409 NOT_CLOSED，IFC-133 规定为 403 | implementation_plan | MINOR | 架构确认 |
| GR-C-005-F01：管理员可以下载附件（IsMemberOrAdmin），超出原范围 | GR-C-005 | MINOR | 用户确认是否保留 |
| systemd 单元名为 `ocap-run-due-jobs`，architecture 中写的是 `ocap-scheduler`；频率每分钟一次 | GR-E1-003-F01 | MINOR | 更新架构文档，或者改为每小时 |
| 画像 P3/P4 中的计数已过期（"后端 120/120""frontend/tests 与 deploy/systemd 不存在"） | GR-E1-003-F02 | MINOR | PM 下次更新画像 |
| ci.yml 建议：去掉 `--passWithNoTests`，加入 `makemigrations --check` | cicd_pipeline 2.0.0 | MINOR | 用户确认后修改 |
| xlsx 导入在本机未执行（缺 openpyxl），只测了 CSV | GR-D-007-F03 | MINOR | 人工验证 MV-002 |
| AC-006-04 中"30 分钟累计 10 次锁定手机号"未在登录端点上测试 | GR-D-007-F03 | MINOR | 补用例 |
| 0001_initial 迁移仍是 makemigrations 产物（CR-002，已在测试库应用） | code_review_report | MINOR | 保持现状 |
| **超限记录（OVERRIDE）**：GROUP_C retries 2→3；defect_loops 2→3→4；GROUP_D retries 2→3 | 用户 ESC-C/ESC-D 答复 A | — | 已记入审计 |

## 待人工验证
测试报告中的人工验证清单 MV-001 ~ MV-007（见 `testing/e2e_test_report.md`）：
- MV-001：微信扫码 / 小程序一键登录的真实链路
- MV-002：xlsx 导入
- MV-003：Web 浏览器走查
- MV-004：uni 运行时页面与图片上传
- MV-005：开发者工具 / 真机登录与手机号授权
- MV-006：小程序业务流程真机走查
- MV-007：微信头像昵称组件

**critical path 中有 5 项待人工验证**（MV-001、004、005、006、007）。

## 开放 conditions
- GR-D-008：交付报告列出人工验证清单与 24 个没有 E2E 旅程的故事。本报告已列出，此条关闭。
- GR-E1-003：提示用户提交并推送；更新画像 P3/P4 的计数。**仍开放**。

## 部署
- E1 计划：`deployment/deployment_plan.md` 2.0.0；操作手册 `.claude/skills/ocap-deploy/SKILL.md`。
- E2：已执行。目标为测试环境（树莓派，经 `ssh -p 57279` VPS + frp），结论 **DEPLOYED_SUCCESSFULLY**。
  - 部署版本：HEAD c0d1f0a 加工作树上 22 项未提交改动。
  - 回滚锚点：`20261108234853`。
  - 无新迁移；新增 `ocap-run-due-jobs.timer`（每分钟一次）。
  - PM 只读复核：
    - 线上关键文件哈希与本地一致；
    - ocap-backend、nginx 与 timer 均为 active；
    - 外网 `/ocap/` 返回 200；
    - 匿名请求管理端返回 401；
    - 近 30 分钟没有 ERROR；
    - Freeark 未受影响。
- 授权：用户本轮原话"Q2:a"，对应 PM 的部署摘要，只对本次有效。

## 安全事件摘要
- 没有注入或越权事件。
- DEF-006 是产品安全缺陷，已修复并部署。
- CR-024：去掉了 SECRET_KEY 的固定默认值，ALLOWED_HOSTS 不再默认为 `*`。
- 本报告与各产物中都没有凭据。
