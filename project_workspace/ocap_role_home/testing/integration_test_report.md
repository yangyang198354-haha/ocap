<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-25T13:03:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_role_home/testing/test_plan.md</file>
    <file>frontend/tests/home_role.spec.js</file>
    <file>miniprogram/tests/home_role.spec.js</file>
    <file>frontend/tests/layout_contract.spec.js</file>
    <file>miniprogram/tests/approval_flow_contract.spec.js</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告 — ocap_role_home

## 摘要

- 执行时间：2026-11-25 12:56–13:03（Asia/Shanghai；含 PM 门控复核 13:01–13:02）；环境：vitest 组件级挂载（HTTP/`uni.request` 替身，不连真实后端）。
- 命令与计数：
  - `cd frontend && npx vitest run tests/home_role.spec.js` → 1 file / 6 tests passed。
  - `cd miniprogram && npx vitest run tests/home_role.spec.js` → 1 file / 3 tests passed。
  - 契约：`cd frontend && npx vitest run tests/layout_contract.spec.js` → 6 passed；`cd miniprogram && npx vitest run tests/approval_flow_contract.spec.js` → 3 passed。
- 新增用例计数：total = pass + fail + skip + blocked + not_testable = 9 = 9 + 0 + 0 + 0 + 0。
- 通过率 = pass/(pass+fail+blocked) = 9/9 = 100.0%。
- 判定模式：INCREMENTAL baseline（零新增失败）；**本层门控：PASSED**。

## 执行输出

```
✓ tests/home_role.spec.js (6 tests)
Test Files  1 passed (1)
     Tests  6 passed (6)

✓ tests/home_role.spec.js (3 tests)
Test Files  1 passed (1)
     Tests  3 passed (3)

✓ tests/layout_contract.spec.js (6 tests)
     Tests  6 passed (6)
✓ tests/approval_flow_contract.spec.js (3 tests)
     Tests  3 passed (3)
```

## 分项结果

### 集成边界 A：Web Home ↔ auth 仓库 ↔ api.js ↔ HTTP

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-WEB-601 | AC-354-01/02 | 游客无房屋/任务/管理，不请求 `/me/housing`、`/approval/tasks`；财务仅合计；决议在投票前并带来源 | PASS |
| TC-WEB-602 | AC-357-01/02/03 | 代表“待我表决 · 2”，已投票/未投票、无参与率；详情仅 `/polls/21`、`/polls/22`；普通调查不混入；已截止 REP_VOTE 进公开决议 | PASS |
| TC-WEB-603 | AC-358-01/02/03、AC-359-01 | 委员兼户主：待办审批 · 4 仅列 3 条 + “全部”；待办审批→待我处理→财务→管理；仅一张待我处理卡 | PASS |
| TC-WEB-604 | AC-355-01/02/03 | 同住人：房屋→投票→决议→信息→财务；不请求 housing/tasks；保留逐账户明细；含业主代表来源 | PASS |
| TC-WEB-605 | AC-356-02/03、AC-359-03 | 内容类空态保留（投票/决议/信息）；待我处理 0 隐藏；非委员不请求审批 | PASS |
| TC-WEB-606 | AC-357-03、AC-359-02 | 代表兼户主：待我表决→待我处理 · 1→投票→决议→财务→信息；无待办审批/管理快捷，不请求 `/approval/tasks` | PASS |

### 集成边界 B：小程序 Index ↔ store ↔ api ↔ `uni.request`

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-601 | AC-354-01/02/03 | 游客无房屋/任务/管理，不请求 housing/tasks；财务仅合计；公开决议在投票前并带来源 | PASS |
| TC-INT-602 | AC-357-01/02 | 代表“待我表决 · 2”，已投票/未投票、无参与率；详情仅 2 条；普通调查不混入 | PASS |
| TC-INT-603 | AC-358-01、AC-359-01 | 委员兼户主：待办审批→待我处理 · 2→财务→管理；仅一张待我处理卡 | PASS |

### 集成边界 C：客户端 API 调用 → 后端路由（契约，既有用例，已执行）

| TC | 描述 | 结果 |
|---|---|---|
| TC-INT-924 / TC-INT-925（`frontend/tests/layout_contract.spec.js`） | 从 `api.js` 实际调用取路径，静态解析 `backend/**/urls.py` 全部可对应；本次补充首页实际调用：`/approval/tasks`、`/polls`、`/polls/{id}`、`/ledger/accounts/summary`、`/info/posts` | PASS（6/6） |
| `miniprogram/tests/approval_flow_contract.spec.js` TC-INT-1310~1312 | 小程序审批/报销请求路径与字段契约 | PASS（3/3） |
| `backend/tests/integration/test_frontend_contract.py` | 双端 `api.js` 全量解析 → Django 路由 + 首页字段契约 | BLOCKED：本机未安装 Django（`ModuleNotFoundError: No module named 'django'`），环境限制；由上方静态契约替代，人工清单 M-04 在测试环境补跑 |

## 与基线对比（baseline 模式）

- 基线（GROUP_C）：Web 57 files / 607 tests；小程序 22 files / 154 tests，均为零失败。
- 本层新增：Web +1 file / +6 tests；小程序 +1 file / +3 tests。
- 相对基线新增失败数：0。既有 13 个 spec 的调整为预期行为变化（删除统计卡/宫格、标题与文案、任务 0 隐藏），逐条原因见 `code_review_report.md`「现有测试调整」。

## 失败汇总（需路由给开发）

无。CR-004（两端顺序常量各存一份）为已接受的 MINOR 风险，本轮以 TC-WEB-603/604/606 与 TC-INT-601/603 双向锁定顺序，未发现实际漂移。
