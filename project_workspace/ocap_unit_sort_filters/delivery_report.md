<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-16T14:32:35+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files><file>phase_status.md</file><file>deployment/deployment_report.md</file><file>testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_01,PHASE_02,PHASE_03,PHASE_04,PHASE_05,PHASE_06,PHASE_07,PHASE_08,PHASE_09,PHASE_10,PHASE_11a,PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 交付报告：选房数字自然排序、地下车位归属修正、后台清册多过滤器

## 项目概览
- 需求：选房四级与已认证房屋列表统一按数字自然顺序；负一/负二层车位从"1栋"移到楼栋级"地下车位"，并修正测试库、生成新导入文件；后台业主清册增加中文过滤器。
- 模式：INCREMENTAL；画像版本 1.5.0
- 起止：2026-11-16T11:00:21+08:00 → 2026-11-16T14:32:35+08:00
- 最终状态：**DELIVERED_WITH_ISSUES**（有待人工验证项与开放条件，见下）

## 阶段执行摘要
| GROUP | 阶段 | 代理 | 状态 | 门控 | 重试 | 回流 | 完成时间 |
|---|---|---|---|---|---|---|---|
| A | 01–02 | requirement-analyst | APPROVED | GR-A-001/002 PASS_WITH_CONDITIONS（用户确认） | 0（按用户答复修订 1 次） | — | 11:16 |
| B | 03–04 | system-architect | APPROVED | GR-B-001 PASS_WITH_CONDITIONS | 0 | — | 11:52 |
| C | 05–06 | software-developer | APPROVED | GR-C-001 PASS_WITH_CONDITIONS | 0 | — | 12:10 |
| D | 07–09 | test-engineer | APPROVED | GR-D-001 PASS_WITH_CONDITIONS | 0 | 0 | 12:40 |
| E1 | 10–11a | devops-engineer | APPROVED | GR-E1-001 PASS_WITH_CONDITIONS | 0 | — | 12:55 |
| E2 | 11b（A~E 五段，逐段授权） | devops-engineer | APPROVED | GR-E2-001~004 | 0 | — | 14:30 |

## 质量指标（baseline 模式，PM 亲自复跑）
| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 单元层相对基线新增失败 | 0（后端 185 OK） | 0 | ✅ |
| 集成层相对基线新增失败 | 0（576 OK） | 0 | ✅ |
| E2E critical path 通过率 | 后端 e2e 55 OK；Must Have 10/10 有已执行用例 | 1.00 | ✅ |
| 代码评审未解决 CRITICAL | 0 | 0 | ✅ |
| 全量回归新增失败 | 0（后端 822、前端 259、小程序 97 全通过；CI run 43807677398 success，Python 3.13） | 0 | ✅ |
| 测试环境远程 E2E | 22：19 PASS / 2 FAIL（既有 DEF-B）/ 1 SKIP | 本批新增失败 0 | ✅ |

## 交付物清单
| 文件 | 生成代理 | 最终版本 | 状态 |
|---|---|---|---|
| requirements/requirements_spec.md、user_stories.md | requirement-analyst | 1.0.0 | APPROVED |
| architecture/architecture_design.md、module_design.md、tech_stack.md | system-architect | 1.0.0 | APPROVED |
| development/implementation_plan.md、code_review_report.md | software-developer | 1.0.0 | APPROVED |
| testing/test_plan.md、unit/integration/e2e_test_report.md | test-engineer | 1.0.0 | APPROVED |
| deployment/cicd_pipeline.md、deployment_plan.md | devops-engineer | 1.0.0 | APPROVED |
| deployment/deployment_report.md | devops-engineer | 4.0.0 | APPROVED |
| 仓库根 registry_import_underground_parking.xlsx（含个人信息，0600，.gitignore 忽略，不入库） | devops-engineer（导出） | — | 本地文件 |

代码：提交 15ea79e（已推送 origin/main）。待提交：本目录本次之后更新的 phase_status.md、deployment/、delivery_report.md 及 agent 记忆、_kb_inbox.jsonl（需用户确认）。

## 测试环境变更记录
- 代码：ANCHOR_TS=20261116130503 快照可回滚。
- 数据：1391 个车位 楼栋 "1栋" → "地下车位"（负1 1119、负2 272）；总数 5742、业主 7862、手机号 4301、有效绑定 2 前后不变；id=4347（1栋负1层1139号 商铺）按用户决定保留。
- 备份（目标机 snapshots/，0600，含个人信息，用户决定保留 7 天，2026-11-23 后删除，删除需经 ssh 写操作，届时由用户发起）：ocapdb-registry-20261116134900.sql、underground-20261116134900.jsonl。

## 遗留问题
| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| DEF-B：远程用例期望"户主"，产品显示"产权业主" | ocap_product_review 上报 | MINOR | 用户决定下一批修：修正 backend/tests/remote/remote_cases.py:77、114 期望；DEF-A（排序）已由本批 US-192 关闭 |
| 远程套件缺 units/options 逐级顺序用例 | GR-E2-004 | MINOR | 下批补 |
| E1 事故：本机 / 下两个空归档 | GR-E1-001-F01 | MAJOR（流程） | 已于 2026-11-16T14:52:30+08:00 经用户授权删除 |
| 文件头 timestamp 估算值（deployment_report 3.1.0） | GR-E2-004-F01 | MINOR | 下次严格取 date 输出 |

## 待人工验证
- MV-03：MySQL 下 apply 期间并发导入的事务保护（未执行，需用户另行指示）
- MV-04：后台业主清册六个过滤器与中文占位、空状态"暂无数据"——用户 2026-11-16 人工核对通过
- MV-05：Web 与小程序真机"选择房屋"四级顺序一致、地下车位最后——用户人工核对通过

## 开放 conditions
- GR-E2-004：DEF-B、远程顺序用例、MV-03/04/05。

## 部署
- 计划：deployment/deployment_plan.md；E2 已执行，环境：测试；阶段 A~E 均经用户当轮逐段授权；结果 DEPLOYED_SUCCESSFULLY。

## 安全事件摘要
- 导出文件含业主姓名与手机号：仅存于仓库根本地（0600，已 gitignore）；仓库为 PUBLIC，用户选择不提交。
- 无凭据写入任何文档。
