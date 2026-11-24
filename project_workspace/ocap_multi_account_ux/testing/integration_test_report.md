<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-24T23:21:23+08:00</timestamp>
  <project_name>ocap_multi_account_ux</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_multi_account_ux/testing/test_plan.md</file><file>project_workspace/ocap_multi_account_ux/development/implementation_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

## 摘要

- 执行时间：2026-11-24 23:15（Asia/Shanghai）
- 环境：Windows / Python 3.14.6 / Django 6.0.6 / `config.test_settings`（SQLite 内存库）；Node / vitest（Web 与小程序）
- 命令：
  - 后端：`python manage.py test tests.integration --settings=config.test_settings`（`backend/`）
  - Web：`npx vitest run --passWithNoTests`（`frontend/`）
  - 小程序：`npm test`（`miniprogram/`）
- 后端计数：total = pass + fail + skip + blocked + not_testable = 911 + 0 + 1 + 0 + 0 = 912；通过率 = 911/911 = 100.00%；**本层门控：PASSED**
- 客户端计数：Web 607/607 通过（57 文件）；小程序 154/154 通过（22 文件）
- 判定模式：INCREMENTAL / baseline（零新增失败）
- 新写用例：后端集成 12（TC-INT-2001～TC-INT-2008，含契约 5 个）、Web 12、小程序 3，全部通过。

## 执行输出

```
python manage.py test tests.integration --settings=config.test_settings
Found 912 test(s).
System check identified no issues (0 silenced).
Ran 912 tests in 90.137s
OK (skipped=1)
```

```
npx vitest run --passWithNoTests   # frontend/
 Test Files  57 passed (57)
      Tests  607 passed (607)
```

```
npm test                            # miniprogram/
 Test Files  22 passed (22)
      Tests  154 passed (154)
```

## 分项结果

### 后端集成边界

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-2001 | AC-411-02、AC-412-01 | 收入批量导入提交 account_id 后草稿归属账户；已提交审批的同内容在同账户判重、跨账户不判重；停用账户 409 ACCOUNT_UNAVAILABLE 且不建草稿 | PASS | — | — |
| TC-INT-2002 | AC-413-02 | 报销提交 account_id，审批通过后台账仅记该账户，默认账户余额不变 | PASS | — | — |
| TC-INT-2003 | AC-415-02、AC-416-01、AC-416-02 | 历史支出按账户导入：审批前批次/行 PENDING、台账 0；审批后仅成功行入账到所选账户，重复行不入账，列表 posted_rows 正确 | PASS | — | — |
| TC-INT-2004 | AC-416-03、AC-416-04、AC-422-01、AC-422-02 | 驳回后状态 REJECTED、posted_rows=0、无台账；同文件重新导入生成新批次，仅新批次入账，原批次保持 REJECTED | PASS | — | — |
| TC-INT-2005 | AC-416-03 | 审批中批次撤回为 WITHDRAWN 且无台账；重复撤回与作废均 409 INVALID_STATE | PASS | — | — |
| TC-INT-2006 | AC-419-01、AC-420-02 | `/ledger/reports` 带 account_id 时收入/支出/结余为该账户口径并与详情一致；无 account_id 保持全组织口径；非法 400、不存在 404 | PASS | — | — |
| TC-INT-2007 | AC-411-02、AC-413-02 | 收入草稿/报销响应返回 account_id 与 account_name，客户端可直接渲染账户名 | PASS | — | — |
| TC-INT-2008 | AC-410-01、AC-411-02、AC-412-01、AC-415-01～03、AC-416-04、AC-418-01～03、AC-419-02、AC-420-01/02、AC-421-01～03、AC-423-01/02、AC-424-01/02（契约） | Web/小程序新增调用（账户摘要、收入导入、历史导入与撤回、报表列表/详情、报销/备用金）全部可解析到后端路由且视图支持对应方法；客户端字段（account_id/approval_flow_id）与后端读取字段一致；响应字段（account_id、account_name、posted_rows、approval_instance_id、decided_at）齐全；报表详情源码无账户下拉；小程序领取启用账户并提交 account_id | PASS | — | — |

### 客户端集成/页面组件

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-WEB-2001 | AC-410-01、AC-410-02 | 账户操作列为 el-button（无 el-link），默认账户“设为默认”禁用 | PASS | — | — |
| TC-WEB-2002/2003 | AC-411-01～03 | 逐条录入默认选默认账户并提交 account_id；无账户提示“暂无可用账户”且保存禁用不发请求 | PASS | — | — |
| TC-WEB-2004 | AC-412-01、AC-412-02 | 未选账户导入被拦截；已选账户 FormData 携带 account_id 与文件 | PASS | — | — |
| TC-WEB-2005/2006 | AC-413-01/02、AC-414-01/02 | 报销与备用金默认账户、提交 account_id；未选账户提示且不发请求 | PASS | — | — |
| TC-WEB-2007/2008 | AC-415-01/03、AC-416-04、AC-422-01 | 历史支出默认账户、未选账户不导入、FormData 携带 account_id/approval_flow_id；状态文案“审批中/已入账/已驳回”，撤回仅 PENDING、整批作废仅 IMPORTED | PASS | — | — |
| TC-WEB-2009 | AC-417-01～03、AC-418-01～03、AC-419-02 | 卡片逐张渲染（3/8 个）、默认选中唯一、点击切换携带 account_id、筛选条件与账户同时保留、合计区在卡片滚动容器外、停用账户不出现 | PASS | — | — |
| TC-WEB-2010 | AC-420-01/02、AC-421-01～03 | 详情无账户下拉、按选中账户请求；收入/支出与指标卡 is-income/is-expense 区分；仅支出与空明细形态正确 | PASS | — | — |
| TC-MP-2001 | AC-423-01、AC-424-01 | 小程序仅请求启用账户、默认选中默认账户、备用金沿用同一选中账户 | PASS | — | — |
| TC-MP-2002 | AC-423-02、AC-424-02 | 切换账户后报销/备用金均提交 account_id；无账户时 toast“请选择入账账户”且不发申请请求 | PASS | — | — |

## 与基线对比（baseline 模式）

- 后端集成：基线（开发阶段全量记录）无已知失败；本次 912 用例 `OK (skipped=1)`，新增失败 0。
- Web：基线 595 用例；本次 607（+12 新写），失败 0。
- 小程序：基线 151 用例；本次 154（+3 新写），失败 0。
- 既有失败：0；无“既有/新增”歧义条目。

## 失败汇总（需路由给开发）

无。
