<file_header>
  <author_agent>sdlc-test-engineer</author_agent>
  <timestamp>2026-11-07T23:57:31+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>0.3.0</version>
  <input_files><file>testing/test_plan.md</file><file>requirements/user_stories.md</file><file>architecture/module_design.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

> 复跑说明（ocap-GROUP_D-2）：DEF-001~004 修复后复跑，原 6 条失败全部转绿。

## 摘要

- 执行时间：2026-11-07 23:56 ~ 23:57（Asia/Shanghai，复跑）。
- 环境：Windows，Python 3.14.6，Django 6.0.6，DRF 3.17.1，`config.test_settings`，SQLite `:memory:`，短信 / 邮件 / 微信均为 fake。
- 命令：`python manage.py test tests.integration --settings=config.test_settings -v 1`（工作目录 `backend/`）。
- total = pass + fail + skip + blocked + not_testable = 72 = 72 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 72/(72+0+0) = 100.00%。
- 判定模式与阈值：FULL_FLOW threshold，integration_pass ≥ 0.90。
- **本层门控：PASSED**（100% ≥ 90%）；DEF-001~004 已修复。

## 执行输出

```
python manage.py test tests.integration --settings=config.test_settings -v 1
Ran 72 tests in 0.825s

OK
```

## 分项结果

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-001~009 | AC-001/003/004/005/008/009/069 | 注册、重复手机号、错码锁定、重发限流、验证码登录、密码登录与锁定、登出、小程序降级 | PASS（9） | — | — |
| TC-INT-010~014 | AC-007/017/030/031 | 资料修改与字段保护、昵称长度、头像、邮箱验证与登录、注销 | PASS（5） | — | — |
| TC-INT-015~017 | AC-011/034 | 管理员登录与审计、错误密码、越权拦截 | PASS（3） | — | — |
| TC-INT-018~023 | AC-018/019/020/021/022/023/026 | 清册选项、CSV 导入、手机号维护、认证 HEAD/OWNER、422/409/404 | PASS（6） | — | — |
| TC-INT-024~025 | AC-026 | 申诉凭证、管理员核准 / 拒绝理由 | PASS（2） | — | — |
| TC-INT-026~028 | AC-024/029 | 同住人申请、审批、移除、主动离开 | PASS（3） | — | — |
| TC-INT-029 | AC-027/036 | 撤销户主晋升与席位失效 | PASS（1） | — | — |
| TC-INT-030~033 | AC-037/038/040 | 席位授予、上限校验、撤销、超额提示 | PASS（4） | — | — |
| TC-INT-034~036 | AC-043/045/046 | 审批流程配置校验与可见性 | PASS（3） | — | — |
| TC-INT-037 | AC-045/047 | 指定审批通过后公开详情 | PASS（1） | — | — |
| TC-INT-038 | AC-047 | 审批结束后公开列表对任意登录用户可见 | PASS | — | DEF-001 已修复 |
| TC-INT-039~042 | AC-044/045/048 | 审批中详情隔离、非审批人拦截、待办、撤回重提 | PASS（4） | — | — |
| TC-INT-043~046 | AC-046/065 | 投票窗口、委员投票与重复、到期判定、过期拦截 | PASS（4） | — | — |
| TC-INT-047~054 | AC-048/049/050/051/064/067 | 报销金额、审批、自批拦截、豁免重提、备用金权限、越权、管理端列表 | PASS（8） | — | — |
| TC-INT-055~060 | AC-058/059/060 | 收入导入、权限、错误率、缺列、提交审批与作废、空表拦截 | PASS（6） | — | — |
| TC-INT-061 | AC-063 | 已生效收入表对所有登录用户可见 | PASS | — | DEF-002 已修复 |
| TC-INT-062 | AC-061 | 台账金额与精度 | PASS（1） | — | — |
| TC-INT-063 | AC-063 | 台账报表对所有登录用户可见 | PASS | — | DEF-002 已修复 |
| TC-INT-064 | AC-062 | 同期手动重新生成台账 | PASS | — | DEF-003 已修复 |
| TC-INT-065 | AC-061 | 非业委会成员不可生成台账 | PASS（1） | — | — |
| TC-INT-066~069 | AC-052/055/056 | 投票创建权限、窗口、委员应答与重复、选项校验 | PASS（4） | — | — |
| TC-INT-070 | AC-054/056 | 产权业主参与调查 | PASS | — | DEF-004 已修复 |
| TC-INT-071 | AC-052/053 | 业主代表参与代表投票 | PASS | — | DEF-004 已修复 |
| TC-INT-072 | AC-057 | 截止后结果汇总与截止前拦截 | PASS（1） | — | — |

## 与基线对比

FULL_FLOW / greenfield，无既有基线。复跑后 72/72 全部通过，原 6 条缺陷失败已转绿，无回退、无新增失败。

## 缺陷复核（原失败项）

| TC | 原现象 | 修复验证 | DEF | 状态 |
|---|---|---|---|---|
| TC-INT-038 | 普通登录用户 GET `/resolutions?scope=public` 返回 403 | 读写权限分离后返回 200 | DEF-001 | FIXED |
| TC-INT-061 | 普通登录用户 GET `/income/sheets` 与 `/income/sheets/{id}` 返回 403 | 读接口改 `IsMember` 后返回 200 | DEF-002 | FIXED |
| TC-INT-063 | 普通登录用户 GET `/ledger/reports` 返回 403 | 列表 GET 改 `IsMember` 后返回 200 | DEF-002 | FIXED |
| TC-INT-064 | 同期二次生成台账返回 409 `LEDGER_LOCKED` | 覆盖原行且版本 +1，返回 201 | DEF-003 | FIXED |
| TC-INT-070 | 产权业主应答调查返回 403 | 按调查范围校验后返回 201 | DEF-004 | FIXED |
| TC-INT-071 | 业主代表应答投票返回 403 | 参与人快照 + 代表身份校验后返回 201 | DEF-004 | FIXED |
