<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-14T09:45:35+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>requirements/product_review.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file><file>development/code_review_report.md</file><file>phase_status.md</file><file>testing/test_plan.md</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告：产品评审修正（0.3.0）

## 摘要

> 0.3.0（缺陷回流 2/2 后的最终重测）。0.2.0 的 TC-UNIT-586/587（DEF-021/022）已随 GROUP_C-005 的修复转绿；本版新增 TC-UNIT-590 ~ 601（12 条，`frontend/tests/product_review_rework2.spec.js`）。已冻结用例断言未改。

- 执行时间：2026-11-14T09:35:41 ~ 09:39（+08:00，最后一次执行）；环境：`PY=/tmp/claude-0/-root-myproject-ocap/0130fd24-0fdc-48ac-9199-c3a574e51a0e/scratchpad/venv/bin/python`（Python 3.12.3、Django 5.2.19）；前端 vitest 2.1.9、小程序 vitest（Node v22.23.3）。
- 命令：
  - `(cd backend && $PY manage.py test tests.unit --settings=config.test_settings)`
  - `(cd frontend && npx vitest run --passWithNoTests)`
  - `(cd miniprogram && npx vitest run --passWithNoTests)`
- total = pass + fail + skip + blocked + not_testable = 500 = 500 + 0 + 0 + 0 + 0
  - 后端 `tests.unit` 162 = 162 + 0；前端 244 = 244 + 0（232 既有/0.2.0 + 12 新写）；小程序 94 = 94 + 0。162 + 244 + 94 = 500。
- 通过率 = pass / (pass + fail + blocked) = 500 / 500 = 1.0000
- 判定模式：baseline（零新增失败，新写用例全部通过）。基线：PM GROUP_C-005 后复跑 后端 710 OK（unit 层 162）、前端 232/232、小程序 94/94；本次前端 +12（全为新写，全部通过）、其余不变。既有用例新增失败 0；新写 12 条全部通过。
- **本层门控：PASSED**（零新增失败；新写用例全部通过；TC-UNIT-586/587 转绿）。

## 执行输出

```
$ (cd backend && $PY manage.py test tests.unit --settings=config.test_settings)
Ran 162 tests in 1.485s
OK

$ (cd frontend && npx vitest run --passWithNoTests)
 Test Files  23 passed (23)
      Tests  244 passed (244)

$ (cd miniprogram && npx vitest run --passWithNoTests)
 Test Files  13 passed (13)
      Tests  94 passed (94)
```

补充检查（集成层后一并执行）：`python -m compileall -q backend` 退出 0；`manage.py check` → `System check identified no issues (0 silenced).`；`manage.py makemigrations --check --dry-run` → `No changes detected`。

## 分项结果

### 回流 2 新增（TC-UNIT-590 ~ 601，`frontend/tests/product_review_rework2.spec.js`）

PM 指令 2：DEF-021/022 关闭由 TC-UNIT-586/587 证明（见下表 586、587 行，PASS）；回流 2 同类扫描另修的 8 处补页面级用例如下。GR-C-003 condition：adminText.js 四张映射守护。

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-590 | AC-167-02、REQ-FUNC-158 | InfoDetail 发布时间为"2026-11-13 20:30"，不含 T、时区、秒 | PASS | — | — |
| TC-UNIT-591 | AC-167-03、REQ-FUNC-158 | AdminAudit：主体（成员/管理员/系统）、结果（成功/拒绝/失败）为中文；时间无 T 与时区；动作与对象保持原值 | PASS | — | — |
| TC-UNIT-592 | AC-167-03、REQ-FUNC-158 | AdminFinance：类型 3 种（报销/备用金/核销）、状态 4 种（审批中/已通过/未通过/已撤回）全中文，表格无英文代码 | PASS | — | — |
| TC-UNIT-593 | AC-167-02、REQ-FUNC-158 | AdminMemberships：认证时间"2026-11-13 20:30"，身份"户主" | PASS | — | — |
| TC-UNIT-594 | AC-167-02、REQ-FUNC-158 | AdminContentPosts：发布时间、更新时间"年-月-日 时:分"，状态"已发布" | PASS | — | — |
| TC-UNIT-595 | AC-167-02、REQ-FUNC-158 | AdminContentEditor"保存历史"对话框：时间"年-月-日 时:分"，状态无 FAILED 原文 | PASS | — | — |
| TC-UNIT-596 | REQ-FUNC-158 | Tasks 标题回退：无 subject_title 时标题为"财务（报销/备用金）""收入表"，无 EXPENSE/INCOME | PASS | — | — |
| TC-UNIT-597 | REQ-FUNC-158、GR-C-003 | adminText.js 恰好导出 4 张登记表；小程序 labels.js 不含；不混入 Web labels.js | PASS | — | — |
| TC-UNIT-598 | REQ-FUNC-158、GR-C-003 | 四张映射的键集合与后端枚举（claims.models TYPES/STATUSES、core.models ACTOR_TYPES/RESULTS）完全一致（不多不少）；期望来自模型常量，不用前端输出 | PASS | — | — |
| TC-UNIT-599 | REQ-FUNC-158、GR-C-003 | 四张映射取值均含中文、不含 3 个以上连续大写字母 | PASS | — | — |
| TC-UNIT-600 | REQ-FUNC-158、GR-C-003 | 四张映射均被页面实际使用（AdminFinance 用 CLAIM_*，AdminAudit 用 AUDIT_*） | PASS | — | — |
| TC-UNIT-601 | ADR-092、GR-C-003-F01 | 登记范围守护：shared/ 下除 labels.js、adminText.js 外没有"全大写键→中文值"的导出映射表；adminText 表名不与 labels.js 重名 | PASS | — | — |

**用例有效性（变异检验，scratchpad 副本，非仓库）**：(1) 把 7 个页面还原为 `git show HEAD` 版本：TC-UNIT-590 ~ 596、600 共 8 条失败（修复后全部通过）；(2) 在 adminText.js 副本中给 CLAIM_STATUS_TEXT 增加不存在的键、把 AUDIT_ACTOR_TEXT 的 SYSTEM 值改成英文：TC-UNIT-591、598、599 失败。

**TC-UNIT-588"恰好三张 Web 专有表"是否应纳入 adminText.js（GR-C-003-F01 评估）**：不应纳入，也不改冻结用例。理由：TC-UNIT-588 的口径是"labels.js 内非 `_LABELS` 导出恰为已登记的三张（与小程序共享区的边界）"；adminText.js 是独立的"Web 管理端专有映射"文件，放入它既不触发 588，也不应放宽 588。真正的缺口是"新映射不在任何守护范围内"，由新增 TC-UNIT-597 ~ 601 补上：597 锁定 adminText.js 的导出集合（再新增映射需同步修改守护，属于有意的变更闸门）、598 键与后端枚举一致、599 值为中文、600 防死代码、601 防止新的枚举映射表出现在 labels.js / adminText.js 之外而逃过检查。

观察项（不判缺陷）：OBS-9 AdminAudit 的时间列用 `datetime()`（含秒，"2026-11-13 20:30:45"），REQ-FUNC-158 写的是统一"年-月-日 时:分"；实现计划（回流 2 命中清单）说明"审计需要秒"，满足 AC-167-02 的形式（无 T、无时区后缀），TC-UNIT-591 只断言到分钟与无 ISO；若用户要求严格到分钟，需开发改为 `formatDateTime`。OBS-10 AdminFinance 筛选下拉的选项为"通过/拒绝"，表格列为"已通过/未通过"，措辞不统一，不违反 AC（审计与报销状态中文措辞为开发自拟，GR-C-003-F02 已登记待用户确认）。

### 回流 1 新增（TC-UNIT-579 ~ 589，`frontend/tests/product_review_rework1.spec.js`，用例文件未改动）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-579 | AC-167-03、REQ-FUNC-158（DEF-020） | AdminFlows 适用/方式/启用列显示"决议/财务（报销/备用金）/收入表""半数人员同意/指定负责人审批""是/否"，页面无内部代码 | PASS | — | — |
| TC-UNIT-580 | REQ-FUNC-158（DEF-020） | Tasks 待办：中文类别 + "2026-11-13 20:30"，无 ISO/秒/时区 | PASS | — | — |
| TC-UNIT-581 | REQ-FUNC-158（DEF-020） | ResolutionDetail 审批方式：半数人员同意 / 指定负责人审批，无英文代码 | PASS | — | — |
| TC-UNIT-582 | REQ-FUNC-158（DEF-020） | Income 6 种状态显示中文（草稿/审批中/已生效/未通过/已撤回/已作废） | PASS | — | — |
| TC-UNIT-583 | REQ-FUNC-158（DEF-020） | InfoList 发布时间为 "2026-11-13 20:30" | PASS | — | — |
| TC-UNIT-584 | AC-060-04、AC-060-10（DEF-019 Web 侧） | 5 行（已生效+can_void / 已生效 can_void=false / 审批中 / 已作废 / 已生效缺 can_void）只有第 1 行有"作废"，确认后 POST `/admin/income/sheets/1/void` | PASS | — | — |
| TC-UNIT-585 | AC-060-04 | 作废确认取消时不发请求 | PASS | — | — |
| TC-UNIT-586 | REQ-FUNC-158 同类扫描（DEF-021） | 业委会成员首页"待办"卡片：类别中文、时间"年-月-日 时:分" | PASS（回流 2 修复后） | — | — |
| TC-UNIT-587 | REQ-FUNC-158 同类扫描（DEF-022） | 决议详情"表决截止：2026-11-13 20:30" | PASS（回流 2 修复后） | — | — |
| TC-UNIT-588 | ADR-092、GR-C-002-F01 | Web 专有映射（非 `_LABELS` 导出）恰为 FLOW_SCOPE/APPROVAL_MODE/INCOME_STATUS 三个；小程序 labels.js 不含；键与后端模型枚举一致 | PASS | — | — |
| TC-UNIT-589 | REQ-FUNC-158 | 三个映射表取值均含中文、不含 3 个以上连续大写字母 | PASS | — | — |

验证用例有效性：把 TC-UNIT-579 ~ 585 放到"页面还原为 HEAD 版本"的临时副本中运行（scratchpad 副本，非仓库），7 条全部失败，修复后 7 条通过（586、587 在回流 2 修复前失败、修复后通过）。

> 以下为 0.1.0 已有的分项（本次全部复跑通过，描述未改）。

（0.1.0 口径，本次其余用例复跑均通过）新写 57 条（后端 17、Web 31、小程序 9）、接管 17 条（Web 8、小程序 9）均 PASS；其余为既有用例（后端 145、Web 182、小程序 76），全部 PASS。下表只列本阶段新写与接管的用例。

### 后端 unit（单元：规则/配置/身份/限制）

| TC | AC | 描述 | 来源 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| TC-UNIT-505 | AC-170-01、AC-170-04 | 合法值规范化为两位小数字符串。 | 新写 | PASS | — | — |
| TC-UNIT-506 | AC-170-04 | 0、负数、非数字、布尔、None、三位小数、超列范围、NaN 均拒绝（INVALID_VALUE）。 | 新写 | PASS | — | — |
| TC-UNIT-507 | AC-170-02 | claim.amount_max 可编辑且有校验器；默认 1,000,000.00；上限 999999999999.99。 | 新写 | PASS | — | — |
| TC-UNIT-508 | AC-170-01、AC-170-02 | _parse_amount 带 limit：边界值通过、超 0.01 失败并带 details。 | 新写 | PASS | — | — |
| TC-UNIT-509 | AC-170-05 | 收入金额解析与按行解析遵循显式 limit。 | 新写 | PASS | — | — |
| TC-UNIT-510 | AC-155-01、AC-155-03 | client 缺省 web；web/miniapp 合法；其余非法（含非字符串）。 | 新写 | PASS | — | — |
| TC-UNIT-511 | AC-155-01~03 | miniapp 或 remember_me → EXTENDED；Web 缺省 IDLE；配置关闭 miniapp 延长时回到 IDLE。 | 新写 | PASS | — | — |
| TC-UNIT-512 | AC-157-01~03 | 职务 > 户主 > 产权业主 > 同住人 > 游客；过期席位不计；同级取认证最早。 | 新写 | PASS | — | — |
| TC-UNIT-513 | AC-157-04 | 目录与 residency 服务使用同一角色排序（管理端与本人汇总同源）。 | 新写 | PASS | — | — |
| TC-UNIT-514 | AC-157-02 | identity_labels 与 identity_view 最高身份一致（多户取最高，不取第一条）。 | 新写 | PASS | — | — |
| TC-UNIT-515 | AC-164-01、AC-164-03、AC-164-04 | 只关闭 PENDING、释放唯一槽、不改驳回原因；无待处理项返回 0。 | 新写 | PASS | — | — |
| TC-UNIT-516 | AC-164-01 | CLOSED 是两个模型的合法状态；两个关闭审计动作已登记。 | 新写 | PASS | — | — |
| TC-UNIT-517 | AC-172-01、AC-173-01、AC-173-02、AC-170-02 | 规则限制常量与 current_limits 键/值。 | 新写 | PASS | — | — |
| TC-UNIT-518 | 画像 P4-1 | 夹具前缀 e2e_ 与预留号段 1990000；两者不得为空或过短（双条件护栏的前提）。 | 新写 | PASS | — | — |
| TC-UNIT-519 | AC-167-01~03（ADR-092） | Web 与小程序 labels.js 的 *_LABELS 键与取值逐项相同。 | 新写 | PASS | — | — |
| TC-UNIT-520 | AC-167-01、AC-167-03 | 中文映射表的取值不含 HEAD/OWNER/ACTIVE/true/false 等英文代码。 | 新写 | PASS | — | — |
| TC-UNIT-521 | AC-178-01 | 新增后端模块可解析，且迁移 0002 为手写（无 "Generated by Django"）。 | 新写 | PASS | — | — |

### Web 前端（页面/组件，HTTP 层 mock）

| TC | AC | 描述 | 来源 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| TC-UNIT-522 | AC-150-01 | 页面没有任何"专有部分 ID"或内部编号输入框；逐级选择组件存在 | 新写 | PASS | — | — |
| TC-UNIT-523 | AC-150-01 | 选定房屋后点"申请成为同住人"只提交 {unit_id}，并提示"申请已提交，等待产权业主审批" | 新写 | PASS | — | — |
| TC-UNIT-524 | AC-167-01、§8 推断 1 | 认证成功提示为中文身份（户主 / 产权业主），不出现 HEAD / OWNER | 新写 | PASS | — | — |
| TC-UNIT-525 | AC-153-04、AC-158-03 | 移除同住人——取消不发请求；确认后 DELETE /units/1/residents/9 | 新写 | PASS | — | — |
| TC-UNIT-526 | AC-153-04 | 同住人"退出"——取消不发请求；确认后 POST /units/{id}/leave | 新写 | PASS | — | — |
| TC-UNIT-527 | AC-152-01~03、AC-156-01~04 | 我的申请/申诉：状态中文、时间"年-月-日 时:分"、驳回原因原文、空态文案 | 新写 | PASS | — | — |
| TC-UNIT-528 | AC-157-03 | 游客显示"游客"与"暂无已认证房屋"，不显示同住人名单 | 新写 | PASS | — | — |
| TC-UNIT-529 | AC-151-01 | 待审批列表显示申请人昵称、房屋名与提交时间，不含手机号明文 | 新写 | PASS | — | — |
| TC-UNIT-530 | AC-157-01、AC-157-05 | 身份卡列出汇总身份与每套房屋（户主），全部中文且没有编辑身份的控件 | 新写 | PASS | — | — |
| TC-UNIT-531 | AC-165-03 | 更换头像处提示"jpg/png，不超过 2 MB"，选择器仅允许 jpg/png；超大或错误格式在上传前被拒 | 新写 | PASS | — | — |
| TC-UNIT-532 | AC-165-01 | 保存生日提交 YYYY-MM-DD；留空提交 null（选填） | 新写 | PASS | — | — |
| TC-UNIT-533 | AC-165-02 | 头像通过鉴权下载（/attachments/<id>/download，blob）并显示为图片 | 新写 | PASS | — | — |
| TC-UNIT-534 | AC-158-04 | 注销账号——取消确认不发验证码校验请求；确认后才调用 /me/cancel | 新写 | PASS | — | — |
| TC-UNIT-535 | AC-163-01 | 密码登录输入框提示为"账号或手机号"，不含"邮箱" | 新写 | PASS | — | — |
| TC-UNIT-536 | AC-169-02 | 详情失败时提示"内容不存在或已下线"，"返回列表"链接指向信息公开列表 | 新写 | PASS | — | — |
| TC-UNIT-537 | AC-167-02 | 投票状态为"进行中/已结束"，截止时间为"2026-11-13 20:30"，无 T 与时区后缀 | 新写 | PASS | — | — |
| TC-UNIT-538 | AC-172-01 | 主任/副主任打开发起页，预先显示"最多 50 道题；单选/多选题选项 2 ~ 10 个；表决窗口不少于 60 分钟" | 新写 | PASS | — | — |
| TC-UNIT-539 | AC-161-01、AC-161-04 | 决议列表显示总条数；总数不超过 20 时无翻页控件，超过时有 | 新写 | PASS | — | — |
| TC-UNIT-540 | AC-158-01 | 撤销认证——取消不发请求且没有新增调用；确认后才 POST /admin/memberships/revoke，确认框写明后果 | 新写 | PASS | — | — |
| TC-UNIT-541 | AC-159-02 | 赋予席位对话框没有"用户 ID"输入框；搜索选中后显示昵称与最高身份并提交 user_id | 新写 | PASS | — | — |
| TC-UNIT-542 | AC-158-03 | 撤销席位、删除审批流程——取消不发请求 | 新写 | PASS | — | — |
| TC-UNIT-543 | AC-167-03 | 席位页与账号页的状态、启用列显示中文，布尔显示"是/否"，页面文字无 ACTIVE / true / false | 新写 | PASS | — | — |
| TC-UNIT-544 | AC-160-02 | 账号页带关键词翻到第 2 页，请求仍携带同一关键词与 page=2 | 新写 | PASS | — | — |
| TC-UNIT-545 | AC-162-03、AC-162-05 | 版式模板页——名称为空保存被拦（提示"模板名称不能为空"、不发请求）；内置模板无编辑/删除入口；被引用数显示 | 新写 | PASS | — | — |
| TC-UNIT-546 | AC-162-04 | 删除被引用的模板——确认后后端 STYLE_IN_USE，提示"被 K 条内容引用"；取消不发请求 | 新写 | PASS | — | — |
| TC-UNIT-547 | AC-170-01、AC-170-04 | 金额上限配置卡显示当前值；非法输入显示后端文案并回读原值；合法值保存后按两位小数显示 | 新写 | PASS | — | — |
| TC-UNIT-548 | AC-158-01、AC-158-03、AC-158-04 | 11 个确认键都在页面中被使用，且每处调用都是"确认失败即 return"的写法 | 新写 | PASS | — | — |
| TC-UNIT-549 | AC-150-01、AC-159-02 | 页面源码中不再有"专有部分 ID"或"用户 ID"的手输控件 | 新写 | PASS | — | — |
| TC-UNIT-550 | AC-157-05、AC-167-01 | 用户端页面不再直接显示 role 原始代码（模板中的 {{ x.role }} 均经 label） | 新写 | PASS | — | — |
| TC-UNIT-577 | AC-154-04、AC-166-01 | 顶部导航——非成员无"报销/备用金""收入表""待办"；委员三者可见 | 新写 | PASS | — | — |
| TC-UNIT-578 | AC-159-04 | 无匹配时显示"无匹配用户"；匹配超过一页时出现翻页控件并按页请求（page_size=10） | 新写 | PASS | — | — |

### 小程序（页面，uni 桩）

| TC | AC | 描述 | 来源 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| TC-UNIT-551 | AC-150-04 | 逐级选房，页面没有任何文本输入框；选定后申请只提交 {unit_id} 并提示"申请已提交，等待产权业主审批" | 新写 | PASS | — | — |
| TC-UNIT-552 | AC-151-05、AC-152-04 | 产权业主在小程序看到待审批并通过；我的申请显示状态与"年-月-日 时:分" | 新写 | PASS | — | — |
| TC-UNIT-553 | AC-153-05 | 同住人退出——取消不发请求；确认后 POST /units/{id}/leave | 新写 | PASS | — | — |
| TC-UNIT-554 | AC-156-05 | 我的申诉显示状态、处理时间与驳回原因；空态"暂无申诉" | 新写 | PASS | — | — |
| TC-UNIT-555 | AC-151-05、AC-151-04 | 产权业主首页显示"待审批同住人申请：2"并进入我的房屋待审批区；无待审时不显示 | 新写 | PASS | — | — |
| TC-UNIT-556 | AC-166-01、AC-154-04、AC-166-03 | 非成员首页不请求待办、无待办卡与"报销"快捷入口，但仍见待审批提示；委员有待办卡 | 新写 | PASS | — | — |
| TC-UNIT-557 | AC-157-01、AC-168-03 | 我的页列出每套房屋与身份（中文）；无已生成报表时显示"暂无已生成报表" | 新写 | PASS | — | — |
| TC-UNIT-558 | AC-161-03 | 决议列表点"加载更多"追加下一批（请求 page=2），到底后显示"没有更多了，共 N 条" | 新写 | PASS | — | — |
| TC-UNIT-559 | AC-161-03（边界） | 总数不超过 20 时无"加载更多"，直接显示"没有更多了，共 N 条" | 新写 | PASS | — | — |

### Web 前端（公共件/页面）

| TC | AC | 描述 | 来源 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| TC-UNIT-560 | AC-167-01~03 | 中文映射：状态、角色、布尔值 | 接管 | PASS | — | — |
| TC-UNIT-561 | AC-167-01~03 | 键集合与小程序 labels.js 一致（ADR-092） | 接管 | PASS | — | — |
| TC-UNIT-562 | AC-158-03、AC-158-04 | confirmDanger：确认 → true，取消/关闭 → false；注销列出 4 项后果 | 接管 | PASS | — | — |
| TC-UNIT-563 | AC-160-02、AC-161-02 | usePaging：数组与分页对象两种返回；翻页保持筛选条件 | 接管 | PASS | — | — |
| TC-UNIT-564 | AC-154-04 | 非成员：Claims 页无“新建申请” | 接管 | PASS | — | — |
| TC-UNIT-565 | AC-154-04 | 成员：Claims 页有“新建申请” | 接管 | PASS | — | — |
| TC-UNIT-566 | AC-151-01、AC-151-04、AC-166-03 | 产权业主首页显示“待审批同住人申请：2”；非成员不请求待办；无待审时不显示 | 接管 | PASS | — | — |
| TC-UNIT-567 | AC-169-01、AC-169-02 | InfoDetail：请求失败显示“内容不存在或已下线”与返回列表 | 接管 | PASS | — | — |

### 小程序（utils/页面）

| TC | AC | 描述 | 来源 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|---|
| TC-UNIT-568 | AC-178-02、AC-150-04、AC-153-05、AC-168-01 | 路径、方法、请求体 | 接管 | PASS | — | — |
| TC-UNIT-569 | AC-167-01 | statusLabel 中文映射 | 接管 | PASS | — | — |
| TC-UNIT-570 | AC-153-05 | confirmDanger：确认 true、取消 false | 接管 | PASS | — | — |
| TC-UNIT-571 | AC-161-03 | usePaging：加载更多追加不重复，到底后 hasMore 为 false | 接管 | PASS | — | — |
| TC-UNIT-572 | AC-153-05、AC-156-05、AC-157-01 | 我的房屋：汇总身份、同住人名单；取消移除不发请求；确认后 DELETE | 接管 | PASS | — | — |
| TC-UNIT-573 | AC-150-04 | 我的房屋：未选房屋申请同住人给出提示且不发请求 | 接管 | PASS | — | — |
| TC-UNIT-574 | AC-168-01 | 报表明细：合计与明细行，不显示支出事由 | 接管 | PASS | — | — |
| TC-UNIT-575 | AC-154-04、AC-168-01 | 我的：报表可点击进入明细；非成员无“报销 / 备用金”按钮；成员有 | 接管 | PASS | — | — |
| TC-UNIT-576 | AC-154-01、AC-154-04 | 报销页：非成员显示“需要业委会成员身份”且无新建表单 | 接管 | PASS | — | — |

## 与基线对比（baseline 模式）

| 项 | 基线（GROUP_C-005 后，PM 复跑） | 本次 | 差异 |
|---|---|---|---|
| 后端 `tests.unit` | 162 通过 | 162 通过 | 0 |
| 前端 vitest | 232 / 232 | 244 / 244 | +12 新写，全部通过；既有失败 0 |
| 小程序 vitest | 94 / 94 | 94 / 94 | 0 |

失败清单：无。既有失败：无（0.2.0 的 TC-UNIT-586/587 已转绿）。

## 失败汇总（需路由给开发）

无。

## 缺陷关闭核对

| DEF | 判定 | 依据 |
|---|---|---|
| DEF-017 / 018 / 019 | 关闭（0.2.0 已核对，本次后端全量 712 OK 未回退） | TC-INT-512/513/514、539 ~ 543 通过 |
| DEF-020（REQ-FUNC-158 同类页面） | 关闭 | TC-UNIT-579 ~ 583 通过 |
| DEF-021（Home.vue 待办卡片） | 关闭 | TC-UNIT-586 PASS；TC-UNIT-596 另验 Tasks 标题回退 |
| DEF-022（ResolutionDetail 表决截止） | 关闭 | TC-UNIT-587 PASS |
| 回流 2 另修 8 处（InfoDetail、AdminAudit、AdminFinance、AdminMemberships、AdminContentPosts、AdminContentEditor、Tasks 标题回退） | 全部有页面级用例 | TC-UNIT-590 ~ 596，变异检验确认能失败 |

## 说明与限制

- 前端/小程序用例挂载真实页面并走真实 `api.js`/store，仅 mock HTTP 层（前端）或 `uni` 桩（小程序）；`uni` 桩不代表微信真机行为，小程序 `uni build` 未运行（GR-C-001-F02，环境限制，列入人工验证清单）。
- 同类扫描不是完备证明：TC-UNIT-601 只覆盖"全大写键→中文值"形态的映射表；通过 `v-bind`/`:label`/`el-table-column prop=` 直出的列需逐页核对（回流 2 已逐一枚举 `prop=`，见 implementation_plan 3.0.0 命中清单）；审计"动作"码列与"对象类型"按设计保持原值。
- TC-UNIT-581/587 通过 `vi.mock('vue-router')` 固定 `useRoute().params.id`；TC-UNIT-590/595 同法（`globalThis.__routeId`）。
- 0.1.0 的说明（TC-UNIT-533 jsdom 桩、541 防抖、版式模板页删除确认用 `ElMessageBox.confirm`）仍成立。
