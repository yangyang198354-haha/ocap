<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-27T10:08:03.0867713+08:00</timestamp>
  <project_name>ocap_approval_history</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>development/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 审批与同住人申请历史记录测试计划

## 测试策略

- 被测改动：MOD-228～231；MOD-232 作为申请人记录回归保护。
- 范围：Web 前端、Django/DRF 后端、前后端方法与路由契约。小程序、部署和真实第三方服务不在范围内。
- 环境：本机 Python/Django，`config.test_settings` + SQLite 测试库；Vitest + jsdom，HTTP 层使用 `http.mock.js`，组件、真实 `api.js`、Pinia 与内存路由保持真实实现。
- 判定：INCREMENTAL baseline；每层零新增失败、新写用例全部通过才进入下一层；critical path=1.00，无覆盖率数值门槛。
- 基线：开发门控实跑后端相关 101/101、前端全量 631/631、契约 6/6 通过，无已知失败。全量回归分别按 Django 与 Vitest 最后一轮结果判定。
- 分层：API 参数装配为单元；真实 ORM/HTTP、页面与 API/Store 组合为集成；跨“待办→处理→历史→时间线”和“申请→审批→已通过/本人记录”的完整旅程为 E2E。

## AC 映射

| AC | 用例 ID | 级别 | 现有/新写 | 位置（文件::类/场景） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|
| AC-370-01 | TC-INT-2301；TC-E2E-2301 | INT/E2E | 新写 | `test_approval_history.py::HandledApprovalApiTests`；`approval_history_e2e.spec.js` | 单步待办 | 通过并填“同意”后查两种视图 | 待办移除；已处理一次且摘要/状态完整 | 1 个决议、1 名审批人 |
| AC-370-02 | TC-INT-2302；TC-INT-2308；TC-E2E-2301 | INT/E2E | 新写 | 后端 API；`Tasks.vue` | 两步实例完成第 1 步 | 查询/打开已处理 | 整单“审批中”、当前第 2 步，无审批写按钮 | 初审/终审两步 |
| AC-370-03 | TC-INT-2303 | INT | 新写 | `HandledApprovalApiTests` | 仅被指定；仅他人已操作 | 当前用户查已处理 | 均不收录，看不到他人个人清单 | 两个实例、三名委员 |
| AC-370-04 | TC-INT-2303；TC-INT-2309 | INT | 新写 | 后端 API；`Tasks.vue` | 当前用户无动作但有待办 | 切换已处理/待办 | 已处理空态，待办数量不变 | 1 条待办、0 条历史 |
| AC-371-01 | TC-UNIT-2301；TC-INT-2304；TC-INT-2309；TC-INT-924/925 | UNIT/INT | 新写+现有扩展 | `api.js`；后端 API；`Tasks.vue`；`layout_contract.spec.js` | 2 条决议与 23 条收入历史 | 传 handled+scope | 仅 2 条决议，count=2；请求方法/路由正确 | 25 条历史 |
| AC-371-02 | TC-INT-2305；TC-INT-2308；TC-INT-1304；TC-E2E-2301 | INT/E2E | 新写+现有 | 时间线 API；`ApprovalTimeline.vue` | 两步且有意见 | 打开审批过程 | 步骤、处理人、动作、时间、意见和整单状态完整；只读 | 两步动作留痕 |
| AC-371-03 | TC-INT-2305 | INT | 新写 | `test_approval_history.py::HandledApprovalApiTests` | 无关登录委员 | 直接 GET 实例详情 | 403，响应不含步骤/动作内容 | 无关委员 |
| AC-371-04 | TC-INT-2304；TC-INT-2309 | INT | 新写 | 后端 API；`Tasks.vue` | 25 条历史，每页 20 | 取第 1/2 页并翻页 | 20+5、count=25、实例无重复 | 25 个不同实例，含本人双动作 |
| AC-372-01 | TC-UNIT-2302；TC-INT-2306；TC-INT-2310；TC-INT-924/925；TC-E2E-2302 | UNIT/INT/E2E | 新写+现有扩展 | approved API/端点；`UnitsReview.vue` | 有待审同住申请 | 通过并填“已核实” | 待审移除，已通过记录字段完整；GET 路由正确 | 产权业主、申请人、A 房 |
| AC-372-02 | TC-INT-2307；TC-INT-2310；TC-E2E-2302 | INT/E2E | 新写 | approved 端点；`UnitsReview.vue` | 同单元含 5 种状态；另测空历史 | 查已通过/处理申请 | 仅 APPROVED；空态“暂无已通过的同住人申请” | PENDING/APPROVED/REJECTED/WITHDRAWN/CLOSED |
| AC-372-03 | TC-INT-2307 | INT | 新写 | approved 端点 | 其他单元通过；本人产权结束 | 查询历史 | 不含他人单元；失去产权后为空 | 两个单元、有效/结束产权 |
| AC-373-01 | TC-INT-2306；TC-INT-2311；TC-E2E-2302 | INT/E2E | 新写 | mine 端点；`UnitsApplicationRecords.vue` | 本人申请已通过且有备注 | 打开本人申请记录 | 显示通过、处理时间、备注，无需本人产权 | 申请人无 HEAD/OWNER |
| AC-373-02 | TC-INT-2306；TC-E2E-2302 | INT/E2E | 新写 | mine 端点与申请人旅程 | 他人也有通过申请 | 查询本人记录 | 只含本人申请 | 两名申请人 |

## 测试数据需求

无 `[DATA_REQUIRED]`。全部数据由测试工厂或 ORM 在隔离测试库/内存 HTTP 替身中创建；不使用生产数据，不调用真实闭源 API。

## 不可测项

无。无硬件、数值 golden data 或必须人工调用外部服务的 AC。

## 故事覆盖核对

| Must Have US | 用例 ID（已执行，结果见分层报告） | 层 |
|---|---|---|
| US-370 | TC-INT-2301～2303；TC-E2E-2301 | INT/E2E |
| US-371 | TC-INT-2304～2305、2308～2309；TC-E2E-2301 | INT/E2E |
| US-372 | TC-INT-2306～2307、2310；TC-E2E-2302 | INT/E2E |
| US-373 | TC-INT-2306、2311；TC-E2E-2302 | INT/E2E |
