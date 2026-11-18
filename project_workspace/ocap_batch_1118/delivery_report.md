<file_header>
  <author_agent>pm-orchestrator</author_agent>
  <timestamp>2026-11-18T14:18:58+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files><file>phase_status.md</file><file>deployment/deployment_report.md</file><file>testing/e2e_test_report.md</file><file>development/code_review_report.md</file></input_files>
  <phase>PHASE_01,PHASE_02,PHASE_03,PHASE_04,PHASE_05,PHASE_06,PHASE_07,PHASE_08,PHASE_09,PHASE_10,PHASE_11a,PHASE_11b</phase>
  <status>APPROVED</status>
</file_header>

# 交付报告：ocap_batch_1118

## 项目概览
- 需求（8 条）：
  - 认证申诉改为点击"提交申诉"时一次性提交（选文件不再即时上传）；
  - 专有部分下拉可输入检索；
  - "我的身份与房屋"显示真实姓名与共有产权人；
  - 公开决议卡片显示发起人、规则、截止、状态与参与进度条，详情页列出参与人（昵称、头像）；
  - 投票/决议卡片整卡可点并有动效；
  - 左侧导航二级菜单有动效；
  - 后台清册默认按楼栋/单元/楼层/房号升序，表头可切换排序；
  - 席位授予清册产权业主（未注册亦可），注册认证后自动生效。
  - 另：修复到期任务的 UTC 日期时区缺陷。
- mode：INCREMENTAL；画像版本 1.6.0
- 起止：2026-11-17T23:59:33+08:00 ～ 2026-11-18T14:18:58+08:00
- 最终状态：**DELIVERED_WITH_ISSUES**（人工验证 M-1~M-6、M-8 待用户完成，其中 M-1~M-3 属于 critical path；另有遗留问题）

## 阶段执行摘要
| GROUP | 阶段 | 代理 | 状态 | 门控 | 重试 | 回流 |
|---|---|---|---|---|---|---|
| A | 01–02 | requirement-analyst | APPROVED | PASS_WITH_CONDITIONS（GR-A-001/002） | 0（按用户答复定稿 1 次） | — |
| B | 03–04 | system-architect | APPROVED | PASS_WITH_CONDITIONS（GR-B-001） | 0 | — |
| C | 05–06 | software-developer | APPROVED | PASS_WITH_CONDITIONS（GR-C-001） | 0 | — |
| D | 07–09 | test-engineer | APPROVED | PASS_WITH_CONDITIONS（GR-D-001） | 0 | 0 |
| E1 | 10–11a | devops-engineer | APPROVED | PASS_WITH_CONDITIONS（GR-E1-001） | 0 | — |
| E2 | 11b | devops-engineer | APPROVED（测试环境） | PASS（GR-E2-001） | 0 | — |

## 质量指标（baseline 模式，PM 在 GR-D-001 亲自复跑）
| 指标 | 值 | 目标 | 达标 |
|---|---|---|---|
| 后端（单元+集成+E2E）相对基线新增失败 | 0（Ran 1119 OK；基线 1025，含 1 条时段相关既有失败 TC-INT-504，已修复） | 0 | 是 |
| 前端 vitest 相对基线新增失败 | 0（45 文件 531/531） | 0 | 是 |
| 小程序 vitest 相对基线新增失败 | 0（18 文件 135/135） | 0 | 是 |
| E2E critical path 通过率（自动化部分） | 全部通过；M-1~M-3 待人工 | 100% | 部分（待人工） |
| 代码评审未解决 CRITICAL | 0 | 0 | 是 |
| 全量回归新增失败（CI run 44246022429） | 0（三个 job 均 success） | 0 | 是 |

## 交付物清单
| 文件 | 生成代理 | 最终版本 | 状态 |
|---|---|---|---|
| requirements/requirements_spec.md | requirement-analyst | 1.0.0 | APPROVED |
| requirements/user_stories.md（US-244~259，93 条 AC） | requirement-analyst | 1.0.0 | APPROVED |
| architecture/architecture_design.md（ADR-136~146） | system-architect | 1.0.0 | APPROVED |
| architecture/module_design.md（MOD-139~152） | system-architect | 1.0.0 | APPROVED |
| architecture/tech_stack.md | system-architect | 1.0.0 | APPROVED |
| development/implementation_plan.md | software-developer | 1.0.0 | APPROVED |
| development/code_review_report.md | software-developer | 1.0.0 | APPROVED |
| testing/test_plan.md、unit/integration/e2e_test_report.md | test-engineer | 1.0.0 | APPROVED |
| deployment/cicd_pipeline.md、deployment_plan.md | devops-engineer | 1.0.0 | APPROVED |
| deployment/deployment_report.md | devops-engineer | 1.0.0 | APPROVED |

代码改动已提交为 c0b16be 并推送到 main。本报告、phase_status 与 agent 记忆的变更还没有提交（需用户确认）。

## 遗留问题
| 问题 | 来源 | 级别 | 建议 |
|---|---|---|---|
| claims/services.py:19,40 的 decided_at.date() 使用 UTC 日期，北京时间 0–8 点审批的单子日期会早一天（CR-012） | GR-D-001-F02 | MINOR | 下一批修（用户 Q4=A） |
| 未注册业主的待绑定席位计入表决分母（Q-B18-21=B）：待绑定席位数 ≥ ceil(N/2) 时，半数同意类决议无法通过 | 用户决策 | 提示 | 用户已知悉；必要时管理员调整席位 |
| 回滚时若存在 user 为空的待绑定席位，会触发 MANUAL_ROLLBACK_REQUIRED | deployment_plan ROLLBACK-005 | 提示 | 回滚前人工处理 |
| 代码评审 MINOR OPEN 10 条（设计取舍、既有写法、观察） | code_review_report | MINOR | 按需排期 |
| 目标机全量测试未在部署前复跑，以 CI 结果代替 | GR-E2-001-F01 | MINOR | 可接受 |
| 上一批（ocap_identity_property）遗留：认证成功提示显示"身份：户主"；CR-003 小程序匹配卡片在 onShow 时不刷新；人工验证 MV-01~03 待做 | 上批交付报告 | MINOR | 下一批 |
| 画像 P4 基线待更新为 1119/531/135 | PM | 提示 | 需用户同意 |

## 待人工验证（测试环境 https://ai-freeark.xin/ocap/）
引用 deployment_report.md:125-127 与 e2e_test_report 中的人工验证清单。共 7 项待做，其中 critical path 3 项（M-1~M-3）：
- M-1：三套主题下卡片与导航的动效（critical path）
- M-2：系统开启"减少动态效果"后的表现（critical path）
- M-3：整张卡片任意位置可点进正文（critical path）
- M-4：键盘操作
- M-5：读屏软件
- M-6：真实浏览器一次提交 5 个约 10MB 的申诉附件（服务端证据 V-16/V-17 已通过）
- M-8：选好文件后刷新或关闭页面，不应发出附件请求
- M-7：迁移往返已在部署中完成，不需要人工做

## 开放 conditions
无。各门控条件都已在后续门控中核对关闭；E1 条件（用户本轮授权、提交、推送、CI 通过）已满足。

## 部署
- E1 计划：deployment/deployment_plan.md（DEPLOY-001~014）
- E2：已执行，环境为测试，提交 c0b16be；DEPLOY-001~011 完成，可选的 DEPLOY-012~014 未获授权、未执行；V-01~V-21 全部通过；结果 DEPLOYED_SUCCESSFULLY。
- 回滚锚点：TS=20261118135444
- ocap 站点 nginx client_max_body_size 已由 20m 改为 60m（有备份，已 reload）；Freeark 配置未改。

## 安全事件摘要
无。报告中不含凭据、真实姓名或手机号；mysqldump 的口令通过环境变量传递，没有出现在命令行参数里。
