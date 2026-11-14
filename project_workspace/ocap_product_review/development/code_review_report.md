<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-14T09:25:55+08:00</timestamp>
  <project_name>ocap_product_review</project_name>
  <version>3.0.0</version>
  <input_files>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md</file>
    <file>requirements/user_stories.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：产品评审修正（GROUP_C-002）

## 摘要

- `git diff --stat -- backend frontend miniprogram`：69 个既有文件修改（+1267 / −506），另有 22 个新文件或目录（后端 7、Web 9、小程序 6 含测试）。`project_workspace/`、`.claude/` 下的改动不属于本次产品代码，未触碰。
- 五维平均分：Correctness 8.62 / Security 9.00 / Performance 8.92 / Maintainability 8.69 / Testability 8.69，合计均值 8.78（13 个 MOD × 5 维 = 65 个分数，总和 571，571 ÷ 65 = 8.78）。
- 问题统计：CRITICAL 1（已修复 1）/ MAJOR 2（已修复 2）/ MINOR 3（OPEN 3）。合计 6 条：CR-001 ~ CR-006。

## 文件 → MOD/IFC 映射

| MOD | IFC | 文件 |
|---|---|---|
| MOD-074 | IFC-261/262/273/274 | `residency/housing.py`、`residency/views.py`、`residency/urls.py`、`identity/services.py`、`committee/services.py` |
| MOD-075 | IFC-263/264/277 | `residency/{models,services,views}.py`、`residency/migrations/0002_closed_status.py`、`identity/services.py`、`core/audit.py` |
| MOD-076 | IFC-265/266/267/272 | `claims/views.py`、`income/views.py`、`core/{config,views,urls,limits}.py` |
| MOD-077 | IFC-268 | `accounts/views.py` |
| MOD-078 | IFC-269/270 | `content/styles.py` |
| MOD-079 | IFC-271 | `ledger/views.py` |
| MOD-080 | — | `polls/views.py`、`income/views.py` |
| MOD-081 | IFC-278 | `jobs/e2e_fixture.py`、`jobs/management/commands/e2e_fixture.py` |
| MOD-082 | IFC-279/280/281/282 | `frontend/src/shared/{labels,confirm,usePaging,api,format}.js`、`PagerBar.vue`、`portal/parts/*`、`stores/auth.js` |
| MOD-083 | — | `frontend/src/portal/*.vue`（14 个） |
| MOD-084 | — | `frontend/src/admin/**`、`router/index.js` |
| MOD-085 | IFC-283/284 | `miniprogram/utils/{api,labels,confirm,paging}.js`、`components/UnitPicker.vue`、`pages/{units,me,index,claims,resolutions,polls}/index.vue`、`pages/reports/detail.vue`、`store/auth.js`、`pages.json` |
| MOD-086（同步） | — | 见 implementation_plan"现有测试调整" |

## 自验证结果

工作目录：仓库根，子目录用子 shell。`PY` = 画像指定的临时 venv。

| 命令 | 结果（输出尾部） |
|---|---|
| `(cd backend && $PY manage.py check --settings=config.test_settings)` | `System check identified no issues (0 silenced).` |
| `(cd backend && $PY manage.py test --settings=config.test_settings)` | `Ran 585 tests in 34.677s` / `FAILED (failures=1)`：唯一失败为 `test_tc_int_311_downloaded_template_imports_back`（既有基线失败，期望 4 行实际 6 行，GROUP_D 按 US-175 更新，本阶段不改） |
| `(cd backend && $PY manage.py makemigrations --check --dry-run --settings=config.test_settings)` | `No changes detected` |
| `python3 -m compileall -q backend` | 无输出，退出 0 |
| `(cd frontend && npx vitest run --passWithNoTests)` | `Test Files  20 passed (20)` / `Tests  190 passed (190)` |
| `(cd frontend && npm run build -- --base=/ocap/)` | `✓ built in 30.34s`（仅有 chunk 大于 500 kB 的既有警告） |
| `(cd miniprogram && npx vitest run --passWithNoTests)` | `Test Files  12 passed (12)` / `Tests  85 passed (85)` |

对比基线（HEAD afa1fe8：后端 561 条 1 条既有失败；前端 181/181；小程序 75/75）：后端新增 24 条用例全部通过、除 TC-INT-311 外零失败；前端 181 → 190（+9）全部通过；小程序 75 → 85（+10）全部通过。零新增失败。

未验证项：
- 小程序 `uni build -p mp-weixin`：开发机 uni alpha 工具链已知无法构建（记忆 M-SD-006），未运行；页面脚本与模板经 vitest 的 `@vue/test-utils` 编译并挂载（含新页面 `pages/reports/detail`，被 TC-E2E-202 逐页加载）。因画像 P4 的小程序测试命令已成功运行，且构建失败属既有环境限制，不阻塞。
- 迁移正向/反向执行（`manage.py migrate` 于 SQLite 临时库）：module_design 明确留给 GROUP_D；本次只做漂移检查。
- 远程 HTTP E2E、`e2e_fixture` 在测试机的执行：不在本阶段范围（画像 P4-1，需用户确认）。

## 按模块评审

### MOD-074 身份汇总与房屋聚合
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

`/me/housing` 查询数固定（Membership、Seat、同住人、待审计数各一条）；不含手机号、邮箱；`identity_labels` 与 `identity_view` 同口径。无问题。

### MOD-075 申请/申诉状态与注销关闭
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

注销在既有事务内、先于 `tombstone` 关闭待处理项并逐条写审计；`ALREADY_CLOSED` 先于 `ALREADY_DECIDED`；迁移手写。无问题。

### MOD-076 发起权限、金额上限与规则限制
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

导入每请求只读一次上限；`_parse_amount`/`_parse_rows` 带缺省参数，旧调用兼容；非法值不改原值。无问题。

### MOD-077 小程序会话
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

`client` 非字符串或不在集合内返回 400；管理员登录、微信登录未改。无问题。

### MOD-078 版式模板管理
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

`usage_count` 单条 GROUP BY 聚合；删除前先判存在再判引用。无问题。

### MOD-079 报表明细脱敏
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 9/10 | 9/10 |

脱敏为按需拷贝、不写库。扣分：该行为属 [ASSUMPTION]（Q-B-01），尚待用户确认；见 implementation_plan 开放问题。

### MOD-080 现行规则固化
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

仅常量引用替换，文案与行为不变。无问题。

### MOD-081 E2E 夹具命令
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 8/10 |

护栏齐全：`OCAP_E2E_FIXTURE=1` 门闩、密码只取环境变量且不输出、双条件圈定、账本保护退出码 2、清册行数前后比对、分批删除。扣分：`cleanup` 单函数较长，拆分有利于单测，可在后续批次处理（不影响本批验收）。

### MOD-082 Web 公共件
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

`AuthImage` 释放 objectURL；`usePaging` 兼容数组与分页对象；labels 键集合与小程序一致并有测试守护。无问题。

### MOD-083 Web 用户端页面
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 8/10 | 8/10 | 8/10 |

残留状态下 8 个既有用例失败，已按需求同步（CR-002）。扣分：产权业主首页多一次 `/me/housing` 请求；`Units.vue` 为重写，体量较大。

### MOD-084 Web 管理端页面
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

`UserPicker` 防抖、每页 10 条；模板管理页拦截空名称并显示被引用数。扣分：`AdminFinance.vue` 同时承担列表翻页与配置卡，职责偏多。

### MOD-085 小程序
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 8/10 | 8/10 |

本次从零实现：同住人链路、身份展示、报表明细、入口可见性、加载更多、7 天会话请求体。扣分见 CR-004、CR-005。

### MOD-086 测试同步（既有部分）
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 9/10 | 9/10 |

全部调整有需求依据，未删用例、未放宽断言。扣分：新增用例主体尚在 GROUP_D，现有自验证规格不覆盖所有 AC。

## CR 问题表

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | CRITICAL | `miniprogram/`（残留状态） | 续做起点时 MOD-085 未开始：Must Have 的小程序 AC（AC-150-04、151-05、152-04、153-05、155-01/02、156-05、157 小程序部分、161-03）无实现 | FIXED（本次实现 MOD-085，追溯表已登记实现位置） |
| CR-002 | MAJOR | `frontend/tests/*`、`backend/tests/integration/test_frontend_contract.py`、`test_ui_theme_qa.py` | 残留状态复跑：后端 2 个契约/主题用例（TC-CONTRACT-4、TC-INT-003）与前端 8 个用例因已批准需求而过期（选房逻辑抽出、API 增参、导航与页面数、汇总身份、分页参数、底部标签对非成员隐藏"报销"） | FIXED（逐条同步，见 implementation_plan"现有测试调整"，未删用例、未放宽断言） |
| CR-003 | MAJOR | `miniprogram/tests/*` | 小程序改动使 13 个既有用例过期（页面数 13→14、汇总身份、非成员待办隐藏、分页参数、登录请求体 `client`） | FIXED（同上） |
| CR-004 | MINOR | `miniprogram/pages/claims/index.vue:withdraw` | 小程序"撤回"无二次确认；REQ-FUNC-150 的撤回确认只列了 Web 用户端，小程序只要求移除/退出同住人，故未加 | OPEN（建议下一批评审时与产品确认是否扩到小程序） |
| CR-005 | MINOR | `miniprogram/components/UnitPicker.vue:pickRoom` | `change` 事件的 `specific_part`/`label` 取房号文案（`room.label`），不是完整专有部分名称 | OPEN（页面当前只用 `unit_id`，不影响功能） |
| CR-006 | MINOR | 过程 | 本次对既有测试文件与部分新建文件使用了 Bash 中的 python/sed 脚本改写，未全程用 Edit/Write（协议 §3 规则 3，便于审计） | OPEN（已用 `git diff` 核对，改动范围限于"现有测试调整"表所列文件；后续调用改用 Edit/Write） |

统计核对：CRITICAL 1（FIXED 1）；MAJOR 2（FIXED 2）；MINOR 3（OPEN 3）；合计 6。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无（MAJOR 共 2 条，均已修复；未超过 3 条）。

## 缺陷修复

不适用（非缺陷修复模式）。

## 现有测试调整

见 implementation_plan.md"现有测试调整"表（含用例 → 原断言 → 新断言 → 依据）。要点：没有删除任何用例，也没有放宽断言；因"非成员隐藏报销"而修改的底部标签栏用例，同时新增了非成员 4 项的反向用例；CORR-024（窄屏底部栏）未触及。

---

## 本轮评审（回流 1，GROUP_C-004，1.1.0）

### 摘要
- 修复 DEF-019/017/018/020。改动文件：后端 `income/{services,views}.py`、`committee/{services,views}.py`；Web `shared/labels.js`、`admin/AdminFlows.vue`、`portal/{Income,Tasks,ResolutionDetail,InfoList}.vue`；测试 2 个（现有测试调整，见 implementation_plan）。小程序未改。
- 五维（本轮改动）：Correctness 9 / Security 9 / Performance 8 / Maintainability 9 / Testability 9。
- 问题统计：CRITICAL 0 / MAJOR 0 / MINOR 2（OPEN）。

### 自验证结果
```
(backend) manage.py check            -> System check identified no issues (0 silenced).
(backend) manage.py test             -> Ran 705 tests ... OK
(backend) makemigrations --check --dry-run -> No changes detected
(frontend) npx vitest run            -> Test Files 21 passed (21); Tests 221 passed (221)
(frontend) npm run build -- --base=/ocap/ -> ✓ built in 33.70s
(miniprogram) npx vitest run         -> Test Files 13 passed (13); Tests 94 passed (94)
```
前端改动后又单独复跑后端契约/主题/缺陷证据用例：Ran 50 tests OK（含 TC-INT-512/513/514）。小程序 `uni build` 未运行（M-SD-006，且本轮未改小程序）。

### CR
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-007 | MINOR | `income/views.py:SheetSerializer` | `can_void` 对每个已生效行做一次审批实例查询（页大小上限 100，仅 EFFECTIVE 行）；可批量预取 | OPEN（量级小，后续优化） |
| CR-008 | MINOR | `income/services.py:void_sheet` | 被拒作废额外写 DENIED 审计，需求未要求 | OPEN（保守加入，便于审计追查） |

### 缺陷修复
| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-019 | `income/services.py:void_sheet` | 作废只校验 `IsIncomeMember`，`ApprovalEngine.is_original_approver` 无调用方 | 增加原审批人校验与 `can_void`；Web 按钮条件一致 |
| DEF-017 | `committee/views.py:put` | 校验失败先于审计抛错 | 抛错前写失败审计 |
| DEF-018 | `committee/services.py:merge_seats` | 合并只改状态，无审计 | 写 `SEAT_INVALIDATED` |
| DEF-020 | `frontend/src/shared/labels.js` 等 | 流程列表 `prop="scope"/"mode"` 直出代码 | 中文映射，另修 4 处同类 |

### 现有测试调整
见 implementation_plan"现有测试调整（回流 1）"：2 条后端用例，由录入人作废改为原审批人作废，并新增录入人被拒断言；依据 AC-060-04/10。

---

## 本轮评审（回流 2，GROUP_C-005，2.1.0）

### 摘要
- 修复 DEF-021/022 并按 REQ-FUNC-158 做彻底同类扫描（命令与命中清单见 implementation_plan"缺陷修复（回流 2）"）。改动文件均为 Web 前端：`portal/{Home,Tasks,ResolutionDetail,InfoDetail}.vue`、`admin/{AdminAudit,AdminFinance,AdminMemberships,AdminContentPosts,AdminContentEditor}.vue`、新建 `shared/adminText.js`。后端、小程序、测试均未改。
- 五维（本轮改动）：Correctness 9 / Security 9 / Performance 9 / Maintainability 9 / Testability 9。
- 问题统计：CRITICAL 0 / MAJOR 0 / MINOR 1（OPEN）。

### 自验证结果
```
(backend) manage.py test                 -> Ran 710 tests in 142.605s / OK
(frontend) npx vitest run --passWithNoTests -> Test Files 22 passed (22); Tests 232 passed (232)
(frontend) npm run build -- --base=/ocap/ -> ✓ built in 1m 4s
(miniprogram) npx vitest run --passWithNoTests -> Test Files 13 passed (13); Tests 94 passed (94)
```
过程记录：首次把新映射放进 `labels.js` 时前端 TC-UNIT-588 失败（1 failed / 231 passed），改放 `shared/adminText.js` 后复跑全绿。小程序 `uni build` 未运行（M-SD-006，本轮未改小程序）。

### CR
| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MINOR | `frontend/src/shared/adminText.js` | `CLAIM_TYPE_TEXT` 与 `portal/Claims.vue:typeLabel` 内联映射重复 | OPEN（后续可让 Claims.vue 引用，本轮最小改动不动） |

### 缺陷修复
| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-021 | `portal/Home.vue:27-28`、`portal/Tasks.vue:16` | 首页待办卡片复制自旧模板，直出 `task.scope` / `submitted_at`；DEF-020 只修了 Tasks 主体行 | 类别/标题回退用 `textOf(FLOW_SCOPE_TEXT, …)`，时间用 `formatDateTime` |
| DEF-022 | `portal/ResolutionDetail.vue:7` | 回流 1 只处理 approval_mode，漏掉同行 `vote_deadline` | `formatDateTime` |
| 同类 | 见 implementation_plan 清单 | 管理端 `<el-table-column prop=…>` 直出 ISO 时间/枚举，回流 1 的 grep 只覆盖模板插值，未覆盖 `prop=` 列 | 改为 slot + 格式化 |

### 现有测试调整
无。
