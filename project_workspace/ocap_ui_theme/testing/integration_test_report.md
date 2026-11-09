<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-09T22:27:42+08:00</timestamp>
  <project_name>ocap_ui_theme</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>testing/unit_test_report.md</file>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告：ocap 多风格界面

> 1.1.0（缺陷回流 1/2）：新增 DEF-001 回归 TC-INT-010…015（6 个，边界 6）；后端 integration 165 → 171，本层 total 224 → 230，新写 34 → 40。DEF-001 状态：已修复，回归用例通过。

## 摘要

- 执行时间：2026-11-09T22:23:56+08:00 起（最后一次执行）；环境同单元测试报告（Django 5.2.19 + SQLite 内存库；vitest/jsdom，`@/shared/http` 与 `uni.request` 为替身，api.js、store、页面、路由均为真实模块）。
- 命令：
  - `cd backend && python manage.py test tests.integration --settings=config.test_settings`
  - `cd frontend && npx vitest run tests/login.spec.js tests/pages.spec.js tests/qa_int_theme.spec.js`
  - `cd miniprogram && npx vitest run tests/pages.spec.js tests/qa_int_theme.spec.js`
- total = pass + fail + skip + blocked + not_testable = 230 + 0 + 0 + 0 + 0 = 230（后端 171 + frontend 32 + miniprogram 27；其中现有 190、本次新写 40）
- 通过率 = pass / (pass + fail + blocked) = 230 / (230 + 0 + 0) = 1.00
- 判定模式：baseline —— 相对基线零新增失败且新写用例全部通过。
- 上一层（单元）门控 PASSED，本层得以执行。**本层门控：PASSED**（新增失败 0；新写 40 / 40 通过）。

## 执行输出

```
$ cd backend && python manage.py test tests.integration --settings=config.test_settings
Ran 171 tests in 7.942s
OK

$ cd frontend && npx vitest run tests/login.spec.js tests/pages.spec.js tests/qa_int_theme.spec.js
 Test Files  3 passed (3)
      Tests  32 passed (32)

$ cd miniprogram && npx vitest run tests/pages.spec.js tests/qa_int_theme.spec.js
 Test Files  2 passed (2)
      Tests  27 passed (27)
```

## 分项结果

### 集成边界 1：accounts 偏好接口 ↔ core 权限/错误/ORM（后端，MOD-023）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-005 | AC-091-04 | 未登录 / 坏令牌 401；管理员 403（GET、PUT）；游客/户主/同住人/主任均 200 且 PUT 回显 | PASS | — | — |
| TC-INT-006 | AC-091-04、AC-078-03 | PUT 体与查询串带他人 id（user_id、id）无效：A 的偏好不变，B 只改自己；B 读不到 A 的值 | PASS | — | — |
| TC-INT-007 | IFC-142/143 | POST/DELETE/PATCH `/me/theme` 返回 405，偏好不变 | PASS | — | — |
| TC-INT-008 | AC-091-02 | `/me` 与登录响应键集合不含 theme（接口契约未被污染） | PASS | — | — |
| TC-INT-301（7，现有） | AC-075-01、AC-078-03、AC-091-04 | GROUP_C 的 test_theme_preference_api.py（含非法值 11 种、隔离、初值 null） | PASS | — | — |

### 集成边界 2：前端调用 ↔ 后端路由（契约，MOD-023 ↔ MOD-025/028）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-001 | AC-078-04、AC-091-02 | Web 与小程序 api.js 均含 GET+PUT `/me/theme`，resolve 到支持 get/put 的视图 | PASS | — | — |
| TC-INT-002 | AC-091-02 | 解析 frontend/src/shared/api.js、miniprogram/utils/api.js 及 upload 的全部调用（>110 个），逐个 resolve 到后端路由且方法被视图支持：未解析调用数 = 0 | PASS | — | — |
| TC-INT-003 | GR-C-002 条件④ | Home.vue 新增的 `approvalApi.tasks`（GET /approval/tasks）与 `pollApi.list`（GET /polls）、小程序首页 `api.polls`/`tasks` 的路径、方法在 api.js 与页面源码中成立并 resolve 到后端 | PASS | — | — |
| TC-INT-004 | AC-081-03、CR-008 | 真实 HTTP：户主 GET /polls=200、GET /approval/tasks=403；委员两者 200 | PASS | — | — |
| TC-INT-302（4，现有） | AC-078-04、AC-091-02 | GROUP_C 的 test_frontend_contract.py：Web 路由、小程序路由、已知错误路径已消除、`test_theme_preference_contract`（字段 `theme`） | PASS | — | — |

契约范围核对：`/me/theme`（GET、PUT，请求/响应字段 `theme`）、Home 新增两个调用，均在复跑中通过（GR-C-002 条件④）。

### 集成边界 3：权限（accounts/approval/income/ledger/resolutions/polls/claims/registry/core ↔ 全局鉴权）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-009 | AC-091-03 | 匿名/游客/户主/委员/主任/管理员 × 11 个受保护操作（GET /me、/approval/tasks、/income/sheets、/ledger/reports、/admin/audit-logs、/admin/registry/units、/polls、/resolutions、/claims、/units/options，POST /resolutions）共 66 个状态码断言。期望值取自 HEAD 导出基线实测 | PASS | — | — |

零回归的对照证据：同一份矩阵（原样复制到 `git archive HEAD` 导出的基线代码树，使用同一 venv 与 test_settings）单独运行 `Ran 1 test … OK`；在当前代码树运行同样通过，所以 66 个断言在改动前后结果完全一致。首版矩阵曾含 `GET /admin/appeals`，该调用在基线和当前代码上都抛 `TypeError`，已从矩阵剔除并作为既有缺陷 DEF-001 上报（见 e2e_test_report"缺陷"）。

### 集成边界 4：Web 路由 ↔ 风格 store ↔ 登录/个人中心/布局页面（MOD-025/026）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-101（5） | AC-082-01/02/04、AC-076-04、AC-077-03、AC-078-01 | 真实 router.afterEach：管理端固定 bento 且不读写设备记忆、不请求 /me/theme；离开管理端回到设备记忆；管理端令牌缺失跳 /admin/login；未登录 /me 跳登录且 DOM 无风格区块；已登录进用户端页触发对账，账号值覆盖设备记忆 | PASS | — | — |
| TC-INT-102（5） | AC-075-01、AC-077-02、AC-086-01、AC-090-03 | 真实 Login 页：账号值优先且对账发生在 router.replace 之前；null → bento 并覆盖遗留记忆；下线 key → bento；读取失败 → 保持设备记忆并继续跳转；Register/WechatCallback 源码顺序为先对账后跳转 | PASS | — | — |
| TC-INT-103（2） | AC-074-01、AC-076-01/02/03、AC-086-02 | 真实 Me 页：独立"界面风格"区块（首个标题，其后仍有资料区块）、3 项名称顺序、默认 bento 选中、来回切换 4 次共 4 次 PUT；保存失败提示含"保存失败"并回滚 | PASS | — | — |
| TC-INT-104（1） | AC-079-02/03 | logout 后设备记忆保留，initFromDevice 应用 terminal，登录页无风格入口 | PASS | — | — |
| TC-INT-105（2） | AC-084-01、AC-085-01/02 | 真实 PortalLayout：决议列表/详情仅"决议"高亮，切投票后仅"投票/调查"，底部标签栏 5 项且高亮唯一，顶部导航保留 | PASS | — | — |
| TC-INT-303（17，现有） | 基线 | frontend login.spec 3 + pages.spec 14（基线用例，回归） | PASS | — | — |

### 集成边界 5：小程序登录/我的页 ↔ 风格 store ↔ utils/api.js + http.js（MOD-028/029）

| TC | AC | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-201（4） | AC-075-01、AC-077-02、AC-086-01、AC-090-03 | 真实 login 页：账号值优先；GET /me/theme 带 `Bearer T` 且先于 reLaunch；null → bento；下线 key → bento；读取失败（500）保持设备记忆并跳转 | PASS | — | — |
| TC-INT-202（2） | AC-079-01/02/03、AC-083-03 | 登录页：无记忆 theme-bento，有记忆 theme-terminal，无风格入口；记忆下线 → bento | PASS | — | — |
| TC-INT-203（4） | AC-074-01、AC-077-01/04、AC-079-02、AC-086-02 | 真实 me 页：3 项、PUT /me/theme `{theme}` 带 Bearer、setTabBarStyle 被调用、下线记忆 → bento 选中且列表无下线项、保存失败 toast 并回滚、退出登录保留设备记忆 | PASS | — | — |
| TC-INT-303（17，现有） | 基线 | miniprogram pages.spec 17 | PASS | — | — |

分项合计：后端 15 新写（9 + 回流 6）+ 156 现有（148 基线 + 8 GROUP_C）= 171；frontend 15 新写 + 17 现有 = 32；miniprogram 10 新写 + 17 现有 = 27；新写 40 + 现有 190 = 230。

本层调试记录（均为测试写错，已修；无产品缺陷）：
- 首版 TC-INT-009 因探测 `/admin/appeals` 抛 TypeError 而出错——定位为既有缺陷 DEF-001，改探测 `/admin/registry/units`（TC-INT-009 保持该写法不变，未改动；申诉列表由 TC-INT-010…015 覆盖）。
- 首版 TC-INT-102/103/105 失败 6 条：vitest `beforeEach(() => mock.mockImplementation(...))` 把 mock 函数作为返回值被当作清理函数调用；布局测试把含 `<router-view>` 的 PortalLayout 嵌套在自身路由下导致渲染两次；登录用例未先 `initFromDevice()`（真实应用由路由钩子完成）。修测试后全部通过（各修 1 轮）。

### 集成边界 6：管理端申诉列表 ↔ core.page_response ↔ residency 序列化器（DEF-001 回归，后端，1.1.0 新增）

| TC | AC / DEF | 描述 | 结果 | 实际输出（FAIL 时） | 根因分类 |
|---|---|---|---|---|---|
| TC-INT-010 | DEF-001、AC-091-02 | 管理员 GET /admin/appeals=200；分页键 {count,page,page_size,results}、条目键集合、applicant 键、手机号脱敏与设计一致 | PASS | — | — |
| TC-INT-011 | DEF-001 | 关联附件时 proof 为 {id,name,size,content_type}（首版曾误用不存在的 Attachment 字段，测试写错，改正 1 轮） | PASS | — | 测试问题（已修） |
| TC-INT-012 | DEF-001 | ?status=PENDING/APPROVED/REJECTED 各自只返回对应条目；未知状态为空；page/page_size 生效 | PASS | — | — |
| TC-INT-013 | DEF-001、AC-091-03 | 匿名/坏令牌 401；游客/户主/委员用户令牌 403 | PASS | — | — |
| TC-INT-014 | DEF-001 | 决议接口 REJECT 后列表按状态可见且 reject_reason 一致（首版请求体字段误写为 reason，实为 reject_reason，测试写错，改正 1 轮） | PASS | — | 测试问题（已修） |
| TC-INT-015 | DEF-001 | 全部 page_response 列表接口冒烟：管理员 9 + 委员 6 共 15 个均 200 分页包装（首版把 /admin/income/sheets 放在管理员令牌下得 401，该路径实为 IsIncomeMember 委员令牌，测试写错，已移入委员组） | PASS | — | 测试问题（已修） |

对照：同一测试文件复制到 `git archive HEAD` 导出的未修复树（同 venv、test_settings）运行：`Ran 6 tests … FAILED (errors=5)`（TC-INT-010/011/012/014/015 因 `TypeError: AppealAdminSerializer.__init__() got an unexpected keyword argument 'context'` 出错；TC-INT-013 不触达序列化器，修复前后均通过）。当前代码树：`Ran 6 tests … OK`。

## 与基线对比（baseline 模式）

| 范围 | 基线 | 本次 | 新增失败 |
|---|---|---|---|
| 后端 integration | 148 OK（HEAD 导出完整树实跑） | 171 OK（148 + GROUP_C 8 + 新写 9 + 回流新写 6） | 0 |
| frontend 本层文件中的基线用例 | login 3 + pages 14 = 17 passed | 同 17 个 passed | 0 |
| miniprogram 本层文件中的基线用例 | pages 17 passed | 同 17 个 passed | 0 |
| 既有失败 | 无 | 无 | — |

失败清单：无。

## 失败汇总（需路由给开发）

无（集成层无失败）。附带发现的既有缺陷 DEF-001（GET /admin/appeals 返回 500）不属于本次改动；**1.1.0：已修复（residency/views.py:116），回归 TC-INT-010…015 通过**，详见 e2e_test_report。
