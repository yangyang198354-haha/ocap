<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-11T16:34:30+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>phase_status.md</file><file>deployment/deployment_report.md</file><file>testing/e2e_test_report.md</file></input_files>
  <phase>PHASE_12</phase>
  <status>APPROVED</status>
</file_header>

# 交付报告：信息公开与多平台内容中心

## 项目概览
- 需求：管理员在 Web 后台编辑并发布信息公开（公众号式富文本、样式与分页），在门户与小程序展示；AI 生成文案、配图、视频；素材库；一键保存到公众号草稿箱，小红书和头条导出内容包或复制后人工粘贴。
- 模式：INCREMENTAL；画像 1.4.0。
- 起止：2026-11-10T23:12:27+08:00 → 2026-11-11T16:34:30+08:00。
- 最终状态：**DELIVERED_WITH_ISSUES**。主要遗留：公众号封面和正文图片上传未实现，人工验证待做，小程序未发布。

## 阶段执行摘要
| GROUP | 阶段 | 代理 | 状态 | 门控 | 重试 | 回流 | 完成时间 |
|---|---|---|---|---|---|---|---|
| A | 01–02 | requirement-analyst | APPROVED | GR-A-003 PASS_WITH_CONDITIONS | 0 | 0 | 2026-11-10T23:30:39+08:00 |
| B | 03–04 | system-architect | APPROVED | GR-B-002 PASS_WITH_CONDITIONS（返工，选 B） | 0 | — | 2026-11-11 |
| C | 05–06 | software-developer | APPROVED | GR-C-004 PASS_WITH_CONDITIONS | 1 | 1 | 2026-11-11 |
| D | 07–09 | test-engineer | APPROVED | GR-D-004 PASS_WITH_CONDITIONS | 2（含 1 次中断） | 1 | 2026-11-11 |
| E1 | 10–11a | devops-engineer | APPROVED | GR-E1-001 PASS_WITH_CONDITIONS | 0 | — | 2026-11-11 |
| E2 | 11b | devops-engineer | APPROVED | GR-E2-001 PASS_WITH_CONDITIONS | 0 | — | 2026-11-11T16:34:30+08:00 |

交付后评审 GR-C-002 判 FAIL，原因如下，之后按上表返工：
- Python 3.12/3.13 下后端无法导入，开发机为 3.14，掩盖了这个问题。
- 保存失败时仍会发布。
- 部分审计缺失。
- 粘贴内容时整篇被拒绝。
- 导出产生的临时文件残留。
- 公众号方案存在风险。

## 质量指标（INCREMENTAL：相对基线零新增失败；PM 亲自复跑，Python 3.12；CI 为 Python 3.13）
| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 后端单元 / 相对基线新增失败 | 138 OK / 0 | 0 | 是 |
| 后端集成 / 相对基线新增失败 | 342 OK / 0（另有 TC-INT-395 BLOCKED，缺资料） | 0 | 是 |
| E2E critical path 通过率 | 24/24 Must Have（替代口径），33 OK | 1.00 | 是 |
| 前端 / 小程序 | 154/154、75/75；构建成功 | 0 新增失败 | 是 |
| 代码评审未解决 CRITICAL | 0 | 0 | 是 |
| 全量回归新增失败 | 0（后端 519；CI run 42972838320 success） | 0 | 是 |

## 交付物清单
| 文件 | 生成代理 | 最终版本 | 状态 |
|---|---|---|---|
| requirements/requirements_spec.md、user_stories.md | requirement-analyst | 1.0.0 | APPROVED |
| architecture/architecture_design.md、module_design.md、tech_stack.md | system-architect | 2.0.0 | APPROVED |
| development/implementation_plan.md、code_review_report.md | software-developer | 3.0.0 | APPROVED |
| testing/test_plan.md、unit/integration/e2e_test_report.md | test-engineer | 2.0.0 | APPROVED |
| deployment/cicd_pipeline.md、deployment_plan.md、deployment_report.md | devops-engineer | 1.0.0 | APPROVED |

代码提交：b0a0159（需求与架构）、6db68b1（首版实现与测试，在其他机器完成）、955c63a（返工），均已推送。

## 遗留问题
| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| 公众号封面与正文图片上传未实现，开关缺省关闭；TC-INT-395 BLOCKED | ADR-061，Q-B1=A | MAJOR | 用户把微信官方文档放入 `docs/vendor/wechat_mp/` 后，补设计、开发和测试 |
| `auth_errcodes` / `token_errcodes` 缺省为空，真实环境不会自动标"失效"；60 秒冷却内草稿失败显示 TOKEN_BUSY，掩盖真实 errcode | GR-C-003-F02、GR-D-004-F03 | MAJOR | 依据官方文档或 M-04 实测得到的 errcode 配置后复核 |
| 23 条 AC 只有部分自动化，缺口为浏览器和真机上的视觉与点击 | test_plan 2.0.0 | MINOR | 按 M-01~M-07 人工验证 |
| ocap-content-worker 的 MemoryMax 可能不生效（目标机未启用 memory cgroup） | GR-E2-001-F01 | MINOR | 观察内存；启用 cgroup 属全局改动，需用户决定 |
| freeark-mqtt-consumer 一直在崩溃后重启（NRestarts=5369），本次部署前就存在 | GR-E2-001-F02 | MINOR | 属于 Freeark，建议用户另行排查 |
| 小程序未发布 | 范围 | MINOR | 构建并发布后做 M-06 真机验证 |
| PM 代答待确认 | — | — | 无 |

## 待人工验证
引用 testing/e2e_test_report.md 与 deployment_report.md 的人工清单：
- M-01：编辑器。
- M-02：未登录与权限。
- M-03：分页。
- M-04：公众号真实联调，**上线前必验**。
- M-05：DeepSeek / 火山方舟 / 即梦真实账号。
- M-06：小程序真机。
- M-07：一键复制与配图插入。

critical path 中有 1 条（M-04）必须人工验证。

## 开放 conditions
- GR-B-002：用户提供官方文档后，登记到画像 P11-3，再补 ADR-061 并做增量开发。
- GR-E2-001：用户待办 U-01~U-05：
  - U-01：备份 CONTENT_CRED_ENC_KEY。
  - U-02：把出口 IP 171.222.186.210 加入公众号后台的 IP 白名单。
  - U-03：上传一个 10 MiB 文件实测。
  - U-04：M-01~M-07 人工验证。
  - U-05：录入各服务凭据。

## 部署
- 计划：deployment/deployment_plan.md 1.0.0。
- E2：已执行，环境为测试（树莓派，https://ai-freeark.xin/ocap/）。
- 发布版本 955c63a，回滚锚点 20261111144450，结果 DEPLOYED_SUCCESSFULLY。
- 迁移 content 0001/0002 已应用。新单元 ocap-content-worker 已运行。.env 新增 4 个键，未读取它们的值。
- 同时上线了 ocap_registry_import 的 DEF-013 修复。

## 安全事件摘要
- 无注入企图。
- 密钥在目标机上生成并直接写入 .env，报告与日志中没有凭据。
- PM 为复跑测试，在会话临时 venv 中安装了 requirements.txt 中的 cryptography，事先未征得用户同意，已在汇报中说明。
