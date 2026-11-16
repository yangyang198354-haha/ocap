<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-16T22:34:23+08:00</timestamp>
  <project_name>ocap_fix_defb_def024</project_name>
  <version>2.0.0</version>
  <input_files><file>phase_status.md</file><file>development/implementation_plan.md (1.0.0)</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

## 实现概览
缺陷修复（PARTIAL_FLOW，无 MOD 设计）：DEF-024（1.0.0，committee）+ DEF-025（本版，同类 parse_date / parse_datetime 未保护调用，共 5 个文件 6 处）。DEF-B 归 GROUP_D，未触碰。

## 同类调用全仓排查（git grep parse_date|parse_datetime|fromisoformat|strptime，排除 tests/migrations）
| 位置 | 输入来源 | 结论 |
|---|---|---|
| committee/views.py:70 | 请求体 | DEF-024 已修（1.0.0） |
| accounts/views.py:249 birthday | 请求体 | 已修（DEF-025），并兼顾非字符串入参 TypeError |
| claims/views.py:95 occurred_on | 请求体 | 已修（DEF-025） |
| claims/views.py:125 expected_settle_on | 请求体 | 已修（DEF-025） |
| polls/views.py:47 deadline（parse_datetime） | 请求体 | 遗漏项，已修并登记（DEF-025）：2026-02-30T10:00 同样 ValueError → 500 |
| resolutions/views.py:214 vote_deadline（parse_datetime） | 请求体 | 遗漏项，已修并登记（DEF-025） |
| income/views.py:38 strptime | 导入文件，_parse_date 已自行转换并由调用方处理 | 无需改 |
| registry/shops.py:219-220、underground.py:376-377 fromisoformat | 内部存储的快照时间戳，非外部输入 | 无需改 |
| content/ai_jobs.py:294 fromisoformat | 内部任务状态时间戳 | 无需改 |

## 改动清单
| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | committee（既有） | backend/apps/committee/views.py:69-74 | 修改 | 无 | L | DEF-024：捕获 ValueError → None → 原 400 INVALID_VALUE | DONE |
| 2 | accounts（既有） | backend/apps/accounts/views.py:248-254 | 修改 | 无 | L | DEF-025：捕获 (TypeError, ValueError) → None → 原 400「生日格式不正确」 | DONE |
| 3 | claims（既有） | backend/apps/claims/views.py:95-100、128-133 | 修改 | 无 | L | DEF-025：两处捕获 ValueError → None → 原 400「请填写费用发生日期」/「预计核销日期须晚于今日」 | DONE |
| 4 | polls（既有） | backend/apps/polls/views.py:47-52 | 修改 | 无 | L | DEF-025：捕获 ValueError → None → 原 400「截止时间格式不正确」 | DONE |
| 5 | resolutions（既有） | backend/apps/resolutions/views.py:213-219 | 修改 | 无 | L | DEF-025：捕获 ValueError → None → 原 400「半数同意决议须填写投票截止时间」 | DONE |

## 需求追溯
| 缺陷 | 验收 | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| DEF-024 | term_start 为不存在日期 → 400 INVALID_VALUE | committee/views.py:69-74 | DONE | 1.0.0 已验证 |
| DEF-025 | birthday / occurred_on / expected_settle_on 为 2026-02-30 → 400 INVALID_VALUE，沿用各处原错误码与消息 | accounts/views.py:248-254；claims/views.py:95-100、128-133 | DONE | 在 venv 中确认 parse_date('2026-02-30') 抛 ValueError、parse_date(123) 抛 TypeError；未发 HTTP 级复现（回归用例由 test-engineer 补） |
| DEF-025（排查新增） | polls deadline、resolutions vote_deadline 为 2026-02-30T10:00 → 400 INVALID_VALUE | polls/views.py:47-52；resolutions/views.py:213-219 | DONE | parse_datetime 同样抛 ValueError（已确认） |

## 迁移
无

## 架构偏差
无

## 开放问题
- [ASSUMPTION] accounts birthday 额外捕获 TypeError（非字符串入参，如数字），同样返回 400「生日格式不正确」；其余位置入参已 str() 化，只捕获 ValueError。
- 回归用例需 test-engineer 补：accounts PATCH profile、claims reimbursement/advance、polls 创建、resolutions 创建（HALF_MAJORITY）的不存在日期各一条。
