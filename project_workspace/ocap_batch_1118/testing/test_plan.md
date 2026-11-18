<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-18T11:40:51+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
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

# 测试计划（ocap_batch_1118，INCREMENTAL，gate_mode=baseline）

## 测试策略

- 被测改动：implementation_plan 的 14 个模块（MOD-139~152）+ 时区缺陷修复（`jobs/views.py`、`run_due_jobs.py` 改用本地日期）。范围：US-244~259 共 16 个故事 / 93 条 AC（Must Have 15、Should Have 1）；REQ-NFUNC-046/048/049/050。
- 范围外：小程序源码（本批不改，仅回归 135 条）；真实浏览器动效观感、nginx 真实 50MB 上传、MySQL 迁移执行（列入 e2e_test_report"人工验证清单"）。
- 环境：本机 Python 3.12 + Django 5.2.19（PM 指定 venv），SQLite 内存库 `config.test_settings`；前端 `frontend/node_modules`（vitest 2.1.9 + jsdom）；小程序 vitest。不连接测试机/外部服务；短信、邮件、微信均走 `apps/integrations/fakes.py`；附件落盘用 `override_settings(MEDIA_ROOT=临时目录)`；时区用例 patch `django.utils.timezone.now`。
- 判定模式：baseline——每层相对基线零新增失败且新写用例全部通过；基线（HEAD c3a10ce，GROUP_C 自验证）：后端 Ran 1025（预期失败 B1~B7，TC-INT-504 时段相关既有失败本批已修复须稳定通过）、前端 41 文件 482（预期失败 F1~F9 + 8 个 Unhandled Errors）、小程序 18 文件 135。
- 分层标记：后端按目录 `tests/{unit,integration,e2e}/`（画像 P3/P4）；前端 vitest 页面/组件用例计 unit，跨 页面↔api.js↔后端路由 的契约用例计 integration，带状态假服务端旅程计 e2e（画像 P3：无浏览器 E2E 框架）。
- critical path 口径：替代（后端多步 API 旅程 TC-E2E-1601~1605 + 前端 jsdom 组件旅程 TC-E2E-1611~1614）。
- 数据：全部合成（姓名"业主甲/乙…"、`next_phone()` 生成手机号，C-79）；会落盘的用例用临时目录；无 `[DATA_REQUIRED]`。P11-1/P11-2 为"无"（无硬件/数值用例），运行方式列统一为"—"；P11-3 的外部 API 本批不涉及。
- 变异验证（M-TE-012）：在 scratchpad 副本回退被测行，6 个后端变异（申诉失败不清理磁盘、公开范围只认已结束、分母排除待绑定席位、参与人返回选项、清册排序忽略 order、共有产权人含本人）全部被新用例抓住；时区变异（`now().date()`）使 TC-INT-1140~1142 与既有 TC-INT-504（冻结北京时间 00:30）失败。

## REWORK 改写清单（REWORK_AUTHORIZED：B1~B7、F1~F9，不删用例、不空断言）

| # | 文件::用例 | 旧断言 → 新断言 | AC |
|---|---|---|---|
| B1 | backend/tests/integration/test_frontend_contract.py::test_tc_int_487 | AdminSeats.vue 含 `user_id` → 含 `registry_owner_id` 且不含 `user_id` | AC-256-01 |
| B2 | 同文件::test_tc_int_488 | 顶层字段集 {summary,units,pending_review_count} → 加 `real_names`；单元字段集加 `co_owners` | AC-247-01、AC-248-01 |
| B3 | backend/tests/integration/test_owner_auth_v2_contract.py::test_tc_int_713 | Web 侧从 `createAppeal({…})` 取键 {unit_id,owner_name,proof_ids} → 读 `form.append('…')` 键集 {unit_id,owner_name,files} 且调用 `unitApi.submitAppeal(`；小程序侧不变 | AC-244-02、AC-245-05 |
| B4 | backend/tests/integration/test_phone_match_api.py::test_tc_int_957 | 每套房屋字段集加 `co_owners` | AC-248-01 |
| B5 | backend/tests/integration/test_product_review_ac.py::test_tc_int_477 | `/me/housing` 顶层集合加 `real_names` | AC-247-01 |
| B6 | backend/tests/integration/test_product_review_api.py::test_resident_and_guest_get_empty_aggregates | 游客响应体加 `"real_names": []` | AC-247-03 |
| B7 | backend/tests/integration/test_registry_filters_contract.py::test_tc_int_585 | 页面查询参数集加 `sort`、`order`；过滤命中/不命中循环排除两者，另断言非法 sort/order 400 INVALID_QUERY、四个合法 sort×desc 200 且 count 不变 | AC-255-01 |
| F1 | frontend/tests/layout_contract.spec.js::TC-INT-921 | 必须覆盖 `unitApi.createAppeal` → `unitApi.submitAppeal`（并断言 Web 页面不再引用 createAppeal、仍保留导出）；新增 `resolutionApi.participants`/`admin.unitOptions`/`admin.ownerCandidates` 被页面引用 | AC-244-02、AC-251-01、AC-256-02 |
| F2 | 同文件::TC-INT-923 | api.js 导出集合基线加 `unitApi.submitAppeal`、`resolutionApi.participants`、`admin.unitOptions`、`admin.ownerCandidates` | IFC-363 |
| F3 | frontend/tests/layout_css.spec.js::TC-UNIT-865 | @media 条件恰为 768px 一对 → 宽度类条件仍**恰为** `(max-width: 767.98px)` 与 `(min-width: 768px)`（守护"断点只用 768px"），非宽度条件仅放行 `(prefers-reduced-motion: no-preference)` | AC-252-05、AC-253-04 |
| F4 | frontend/tests/owner_auth_v2.spec.js::TC-UNIT-669 | 未选房屋禁用提交 → 按钮可点，点击提示"请选择到具体户"且不发 POST /appeals | AC-245-01 |
| F5 | 同文件::TC-UNIT-670 | 提示"请先上传产权证明" → "请至少选择 1 份产权证明"；不发 /appeals 与 /attachments | AC-245-03 |
| F6 | 同文件::TC-UNIT-671 | 上传 2 份→提交 `{proof_ids}` → 选 2 份只暂存(/attachments=0，无"已上传")，一次 POST /appeals(FormData:unit_id/owner_name/files×2)，成功清空 | AC-244-01/02 |
| F7 | 同文件::TC-UNIT-672 | 提示"最多上传 5 份产权证明"且上传 5 次 → "最多 5 份"，暂存 5、全程 0 请求 | AC-245-04 |
| F8 | frontend/tests/product_review_ui.spec.js::TC-UNIT-541 | 搜索用户→提交 `user_id` → 逐级选房(UnitCascader+管理端选项)→选清册业主(姓名+脱敏手机号，已有席位置灰)→提交 `registry_owner_id` 且不含 `user_id` | AC-256-01/02 |
| F9 | frontend/tests/ui_blocks.spec.js::决议卡片三段比例 | 条宽=票数/已投票数(50/10/40) → 分母=participation.expected(25/5/20)，并断言"已参与 10 / 20 · 50%"、"进行中"、发起人昵称 | AC-250-01、AC-249-01 |

owner_auth_v2.spec 的 8 个 Unhandled Errors（旧 http-request 上传方式）随 F4~F7 改写消失（最终全量 vitest 输出无 "Errors"）。

## AC 映射

运行方式列：P11 为"无"，无硬件/数值用例，统一记"—"。位置缩写见下表。

| 缩写 | 文件 |
|---|---|
| BA / BS / BR / BH / BC / BT | backend/tests/integration/test_batch1118_appeal.py / backend/tests/integration/test_batch1118_seats.py / backend/tests/integration/test_batch1118_resolutions.py / backend/tests/integration/test_batch1118_housing_registry.py / backend/tests/integration/test_batch1118_contract.py / backend/tests/integration/test_batch1118_timezone.py |
| BU / BE | backend/tests/unit/test_batch1118_rules.py / backend/tests/e2e/test_batch1118_journeys.py |
| FU / FR / FA / FE | frontend/tests/batch1118_unit_pages.spec.js / frontend/tests/batch1118_resolution_nav.spec.js / frontend/tests/batch1118_admin.spec.js / frontend/tests/batch1118_e2e.spec.js |

用例 ID 与位置对应：TC-INT-1001~1011=BA；1020~1044=BS；1060~1088=BR；1100~1119=BH；1130~1134=BC；1140~1142=BT；TC-UNIT-1501~1531=BU；TC-E2E-1601~1605=BE；TC-UNIT-1201~1221=FU；1301~1342=FR；1401~1411=FA；TC-E2E-1611~1614=FE；改写用例在其原文件（见上表）。

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 预期（含明确期望值） |
|---|---|---|---|---|---|
| AC-244-01 | TC-UNIT-1201, TC-UNIT-1202, TC-E2E-1611 | UNIT/E2E | — | 新写 | 选 2 文件 → 显示 2 个暂存项(名/型/大小/移除)、POST=0、无"已上传" |
| AC-244-02 | TC-UNIT-1208, TC-UNIT-671(改写), TC-INT-1001, TC-INT-1131, TC-E2E-1601, TC-E2E-1611 | UNIT/INT/E2E | — | 新写+改写 | 一次 POST /appeals(FormData)；服务器 1 申诉 + 2 附件(LINKED) |
| AC-244-03 | TC-UNIT-1202, TC-E2E-1611；人工 M-8 | UNIT/E2E | — | 新写 | 卸载重进暂存区为空且全程 0 请求；真实刷新/关闭页面为人工项 |
| AC-244-04 | TC-UNIT-1203 | UNIT | — | 新写 | 暂存 3 → 移除 1 → 剩 2，POST=0 |
| AC-245-01 | TC-UNIT-1204, TC-UNIT-669(改写), TC-INT-1004 | UNIT/INT | — | 新写+改写 | 未选到具体户 → 提示"请选择到具体户"，请求 0；后端 400/404 且 0 残留 |
| AC-245-02 | TC-UNIT-1204, TC-INT-1005 | UNIT/INT | — | 新写 | 空/全空格 → "请输入产权人名字"；65 字超长；64 字边界成功 |
| AC-245-03 | TC-UNIT-1204, TC-UNIT-670(改写), TC-INT-1006 | UNIT/INT | — | 新写+改写 | 无文件 → "请至少选择 1 份产权证明"；后端 400 PROOF_REQUIRED |
| AC-245-04 | TC-UNIT-1205, TC-UNIT-672(改写), TC-INT-1007, TC-INT-1008, TC-UNIT-1501, TC-UNIT-1502 | UNIT/INT | — | 新写+改写 | 12MB/docx/第6份被拦并提示；后端 413/400 且 0 残留；10MB 边界合格 |
| AC-245-05 | TC-UNIT-1206, TC-INT-1011, TC-E2E-1601 | UNIT/INT/E2E | — | 新写 | 失败保留房屋/名字/文件，重提成功；后端第 2 文件落盘异常 → Appeal=0 Attachment=0 磁盘=0 |
| AC-245-06 | TC-UNIT-1207, TC-INT-1009, TC-INT-1010 | UNIT/INT | — | 新写 | 409 APPEAL_PENDING/ALREADY_CERTIFIED，附件新增 0，前端保留暂存 |
| AC-246-01 | TC-UNIT-1210, TC-UNIT-1212, TC-E2E-1611 | UNIT/E2E | — | 新写 | 输入"55"→ 55,551,552,553,155；60 不显示；点 552 选中并显示类型·面积 |
| AC-246-02 | TC-UNIT-1210, TC-UNIT-1212 | UNIT | — | 新写 | 清空输入恢复全部选项，已选不变 |
| AC-246-03 | TC-UNIT-1210, TC-UNIT-1212 | UNIT | — | 新写 | "zzz"无匹配 → 空选项，已选不变，无报错 |
| AC-246-04 | TC-UNIT-1214 | UNIT | — | 新写 | 三页共用同一组件；更换上一级后下级清空(update:modelValue=null)并重载 |
| AC-246-05 | TC-UNIT-1211, TC-UNIT-1213；人工 M-4 | UNIT | — | 新写 | 四级 filterable + 无匹配文案；每级过滤互不影响；键盘操作为人工项 |
| AC-247-01 | TC-INT-1100, TC-UNIT-1220, TC-E2E-1601, TC-E2E-1605 | INT/UNIT/E2E | — | 新写 | real_names=["业主甲"]，页面"真实姓名：业主甲" |
| AC-247-02 | TC-INT-1101 | INT | — | 新写 | 2 套房同名只出现 1 次 |
| AC-247-03 | TC-INT-1102, TC-UNIT-1220 | INT/UNIT | — | 新写 | 游客/同住人/清册姓名为空 → []，页面"—"，不以昵称代替 |
| AC-247-04 | TC-INT-1103, TC-E2E-1605 | INT/E2E | — | 新写 | 他人页面/接口出现 A 姓名次数 0 |
| AC-248-01 | TC-INT-1104, TC-UNIT-1221, TC-E2E-1601 | INT/UNIT/E2E | — | 新写 | co_owners=["业主乙"]，不含本人、无手机号 |
| AC-248-02 | TC-INT-1105, TC-UNIT-1221 | INT/UNIT | — | 新写 | 无其他共有产权人 → [] / 页面"无" |
| AC-248-03 | TC-INT-1106, TC-E2E-1605 | INT/E2E | — | 新写 | 同住人见全名；游客/未认证用户 0 暴露，管理端接口 403 |
| AC-248-04 | TC-INT-1104, TC-UNIT-1221 | INT/UNIT | — | 新写 | 未注册业主仍显示姓名，无"未注册"标注 |
| AC-248-05 | TC-INT-1107, TC-UNIT-1221 | INT/UNIT | — | 新写 | 每行只含各自共有产权人；查询数不随房屋数增长 |
| AC-249-01 | TC-INT-1062, TC-UNIT-1310 | INT/UNIT | — | 新写 | 发起人 昵称+身份、规则、截止、"已结束"+结果标签 |
| AC-249-02 | TC-UNIT-1310 | UNIT | — | 新写 | 指定负责人/无截止时间/无空白"截止" |
| AC-249-03 | TC-INT-1062, TC-UNIT-1311 | INT/UNIT | — | 新写 | 昵称为空 → 账号编号 |
| AC-249-04 | TC-INT-1060, TC-INT-1061, TC-UNIT-1312, TC-UNIT-1510, TC-E2E-1602, TC-E2E-1612 | INT/UNIT/E2E | — | 新写 | 公开列表含进行中半数同意，游客可打开详情 200 |
| AC-249-05 | TC-UNIT-1314 | UNIT | — | 新写 | 三个路由共用同一页面组件，四项齐全 |
| AC-249-06 | TC-INT-1060, TC-INT-1061, TC-INT-1073, TC-UNIT-1510 | INT/UNIT | — | 新写 | 指定负责人审批中/已撤回不公开；详情 403 且不泄露内容 |
| AC-250-01 | TC-INT-1065, TC-UNIT-1301, TC-UNIT-1313 | INT/UNIT | — | 新写 | 4/7·57%，着色 43%/14%，留白 43% |
| AC-250-02 | TC-INT-1066, TC-UNIT-1302 | INT/UNIT | — | 新写 | 7/7·100% 无留白 |
| AC-250-03 | TC-INT-1066, TC-UNIT-1302, TC-UNIT-1313 | INT/UNIT | — | 新写 | 0/7·0%，无 NaN |
| AC-250-04 | TC-INT-1066, TC-UNIT-1303, TC-UNIT-1313 | INT/UNIT | — | 新写 | expected=0 → "暂无表决人"不画条 |
| AC-250-05 | TC-INT-1067, TC-UNIT-1313 | INT/UNIT | — | 新写 | 指定负责人 participation=None，"由指定负责人审批" |
| AC-250-06 | TC-UNIT-1313；人工 M-5 | UNIT | — | 新写 | aria-label="已参与 4 / 7，同意 3，反对 1，弃权 0"；读屏实际朗读为人工项 |
| AC-250-07 | TC-INT-1068, TC-UNIT-1304, TC-E2E-1602 | INT/UNIT/E2E | — | 新写 | 7 席位含 1 待绑定，6 人表决 → 6/7·86%，不是 100% |
| AC-251-01 | TC-INT-1071, TC-UNIT-1320, TC-UNIT-1322, TC-INT-1074, TC-E2E-1612 | INT/UNIT/E2E | — | 新写 | "已参与 3 人"，昵称+头像(默认头像)+时间升序 |
| AC-251-02 | TC-INT-1063, TC-INT-1071, TC-UNIT-1320 | INT/UNIT | — | 新写 | 键恰为 display_name/avatar_url/voted_at；无选项/姓名/手机号；不列未参与者与待绑定 |
| AC-251-03 | TC-INT-1072, TC-UNIT-1321, TC-UNIT-1322 | INT/UNIT | — | 新写 | 无人参与 → "暂无人参与" |
| AC-251-04 | TC-INT-1072, TC-UNIT-1321, TC-UNIT-1322 | INT/UNIT | — | 新写 | 指定负责人 → "无表决参与人"，不请求参与人接口 |
| AC-251-05 | TC-INT-1073 | INT | — | 新写 | 未登录 401，管理员令牌 403，暴露 0 |
| AC-251-06 | TC-INT-1063, TC-INT-1064 | INT | — | 新写 | 进行中详情 200，聚合票数 1/1/0，无 votes/个人选择 |
| AC-252-01 | TC-UNIT-1314, TC-E2E-1612；人工 M-3 | UNIT/E2E | — | 新写 | 标题链接 /resolutions/{id} + ::after 拉伸 CSS；真实点击空白处为人工项 |
| AC-252-02 | TC-UNIT-1330, TC-UNIT-1331；人工 M-1 | UNIT | — | 新写 | 悬停抬升/阴影/按下缩放规则存在，时长 ≤400ms；视觉观感人工 |
| AC-252-03 | TC-UNIT-1315；人工 M-3 | UNIT | — | 新写 | 内嵌链接/按钮 z-index:1 不被拉伸层吞掉 |
| AC-252-04 | TC-UNIT-1315；人工 M-4 | UNIT | — | 新写 | 原生 <a> + :focus-within 焦点样式；真实键盘为人工项 |
| AC-252-05 | TC-UNIT-1330；人工 M-2 | UNIT | — | 新写 | 全部动效规则在 prefers-reduced-motion: no-preference 内 |
| AC-252-06 | TC-UNIT-1316 | UNIT | — | 新写 | 投票页 .poll-link → /polls/{id}，CSS 拉伸 |
| AC-253-01 | TC-UNIT-1340, TC-UNIT-1331, TC-E2E-1613 | UNIT/E2E | — | 新写 | 展开/收起高度过渡 280ms ≤400ms，点击即展开 |
| AC-253-02 | TC-UNIT-1332, TC-UNIT-1342, TC-E2E-1613 | UNIT/E2E | — | 新写 | 选中项 is-active 指示条，仅 1 项选中 |
| AC-253-03 | TC-UNIT-1332；人工 M-1 | UNIT | — | 新写 | 动效只用主题变量(无颜色字面量)；三主题观感人工 |
| AC-253-04 | TC-UNIT-1341, TC-UNIT-1330；人工 M-2 | UNIT | — | 新写 | matchMedia reduce → 无高度动画，功能照常 |
| AC-253-05 | TC-UNIT-1342, TC-E2E-1613 | UNIT/E2E | — | 新写 | Esc 收起并还焦点 |
| AC-253-06 | TC-UNIT-1332 | UNIT | — | 新写 | 窄屏 .sub-nav-item.is-active 同类强调，规则同在 no-preference 内 |
| AC-254-01 | TC-INT-1110, TC-UNIT-1530, TC-UNIT-1401, TC-E2E-1604, TC-E2E-1614 | INT/UNIT/E2E | — | 新写 | 默认自然顺序(2 在 10 前) |
| AC-254-02 | TC-INT-1111, TC-UNIT-1531, TC-E2E-1604 | INT/UNIT/E2E | — | 新写 | 逐页汇总=全量，无重复无遗漏 |
| AC-254-03 | TC-INT-1112 | INT | — | 新写 | 过滤后同一顺序 |
| AC-254-04 | TC-INT-1113 | INT | — | 新写 | 地下车位/商铺/负层沿用既有规则 |
| AC-255-01 | TC-INT-1114, TC-INT-1115, TC-UNIT-1402, TC-UNIT-1530, TC-E2E-1614 | INT/UNIT/E2E | — | 新写 | 楼层降序主键，其余键默认序；再点切回升序 |
| AC-255-02 | TC-INT-1116, TC-E2E-1604 | INT/E2E | — | 新写 | 房号降序第 1 页为全量最大；跨页无重复 |
| AC-255-03 | TC-INT-1118, TC-UNIT-1403, TC-UNIT-1404, TC-E2E-1614 | INT/UNIT/E2E | — | 新写 | 翻页/过滤保持排序；重置清除 |
| AC-255-04 | TC-INT-1117, TC-UNIT-1401, TC-UNIT-1405, TC-E2E-1614 | INT/UNIT/E2E | — | 新写 | 仅四列可排序；非法 sort/order 400 INVALID_QUERY |
| AC-255-05 | TC-INT-1118, TC-E2E-1604 | INT/E2E | — | 新写 | 非管理员 403/未登录 401，记录暴露 0 |
| AC-256-01 | TC-INT-1020, TC-UNIT-541(改写), TC-E2E-1602 | INT/UNIT/E2E | — | 新写+改写 | 待绑定席位 user=None，holder 快照，审计无手机号 |
| AC-256-02 | TC-INT-1021, TC-UNIT-541(改写) | INT/UNIT | — | 新写+改写 | 候选两位姓名、手机号脱敏，可单独授予 |
| AC-256-03 | TC-INT-1022 | INT | — | 新写 | 待绑定占名额 → 409 CAP_REACHED；撤销后可授予 |
| AC-256-04 | TC-INT-1023 | INT | — | 新写 | 同一业主第二个席位 409 ALREADY_SEATED |
| AC-256-05 | TC-INT-1024 | INT | — | 新写 | 已认证业主直接绑定，/me 显示委员 |
| AC-256-06 | TC-INT-1025 | INT | — | 新写 | TERM_NOT_CONFIGURED/INVALID_VALUE 沿用，席位 0 新增 |
| AC-256-07 | TC-INT-1026 | INT | — | 新写 | 非管理员 403/401，参数校验 400/404 |
| AC-257-01 | TC-INT-1030, TC-E2E-1602 | INT/E2E | — | 新写 | 手动认证 → 绑定，/me 委员，SEAT_BOUND 审计，无通知 |
| AC-257-02 | TC-INT-1031 | INT | — | 新写 | 申诉通过 → 绑定(via=APPEAL) |
| AC-257-03 | TC-INT-1032, TC-E2E-1602 | INT/E2E | — | 新写 | 手机号匹配确认 → 绑定(via=PHONE_MATCH) |
| AC-257-04 | TC-INT-1033 | INT | — | 新写 | 另一位业主认证不触发，席位不变 |
| AC-257-05 | TC-INT-1030, TC-INT-1088, TC-E2E-1602 | INT/E2E | — | 新写 | 待绑定期间表决 403；不计入已参与，计入分母 |
| AC-257-06 | TC-INT-1034, TC-E2E-1603 | INT/E2E | — | 新写 | 已有席位 → 冲突保持待绑定、CONFLICT、SEAT_BIND_CONFLICT 审计 |
| AC-257-07 | TC-INT-1035 | INT | — | 新写 | 已绑定后第二用户不重复绑定 |
| AC-257-08 | TC-INT-1036 | INT | — | 新写 | 业主代表绑定后仅代表权限 |
| AC-257-09 | TC-INT-1037, TC-INT-1142 | INT | — | 新写 | 不顺延任期；任期结束后不绑定 |
| AC-258-01 | TC-INT-1040, TC-UNIT-1410 | INT/UNIT | — | 新写 | 持有人/待绑定/冲突区分 |
| AC-258-02 | TC-INT-1041, TC-INT-1022, TC-UNIT-1411, TC-E2E-1603 | INT/UNIT/E2E | — | 新写 | 待绑定可变更/撤销，名额与分母同步释放 |
| AC-258-03 | TC-INT-1042, TC-INT-1043, TC-INT-1044, TC-E2E-1603 | INT/E2E | — | 新写 | 清册改名/删除 → 失效+审计"清册变化" |
| AC-258-04 | TC-INT-1020, TC-INT-1040, TC-UNIT-1410 | INT/UNIT | — | 新写 | 响应/页面无手机号明文 |
| AC-259-01 | TC-INT-1080, TC-UNIT-1520 | INT/UNIT | — | 新写 | N=5 含 1 待绑定，3/1 → 通过，应投总数 5 |
| AC-259-02 | TC-INT-1081, TC-UNIT-1520 | INT/UNIT | — | 新写 | N=5，2/2 → 未通过 |
| AC-259-03 | TC-INT-1082, TC-UNIT-1520 | INT/UNIT | — | 新写 | N=6，3/2 未通过(对照 N=5 通过)；4/1 通过 |
| AC-259-04 | TC-INT-1083, TC-UNIT-1521 | INT/UNIT | — | 新写 | N=4 含 2 待绑定，2 同意 → 未通过 |
| AC-259-05 | TC-INT-1068, TC-INT-1069, TC-UNIT-1304 | INT/UNIT | — | 新写 | 进度 6/7 与判定 N=7 一致，待绑定不在参与人列表 |
| AC-259-06 | TC-INT-1084, TC-E2E-1602 | INT/E2E | — | 新写 | 截止前绑定 N 不变，投票后已参与 +1 |
| AC-259-07 | TC-INT-1085, TC-E2E-1603 | INT/E2E | — | 新写 | 撤销待绑定 → N=4，3×2>4 通过，应投总数 4 |
| AC-259-08 | TC-INT-1086, TC-INT-1067 | INT | — | 新写 | CONFIGURED_CAP N=7 不随待绑定变化，3/3 未通过；指定负责人不受影响 |
| AC-259-09 | TC-INT-1087 | INT | — | 新写 | 待绑定业主代表不计入分母 |

补充（非 AC 专属，REQ-NFUNC / 缺陷回归 / 契约）：

| 项 | 用例 | 级别 | 现有/新写 | 说明 |
|---|---|---|---|---|
| REQ-NFUNC-050 JSON 分支不变 | TC-INT-1002 | INT | 新写 | 小程序 `proof_ids` 分支 201/NAME_REQUIRED/PROOF_REQUIRED 不变 |
| REQ-NFUNC-050 既有 voteShare | TC-UNIT-1305 | UNIT | 新写 | 导出与结构不变 |
| REQ-NFUNC-048 查询数不随行数增长 | TC-INT-1040、1070、1107 | INT | 新写 | 席位列表/公开决议列表/身份页 |
| 契约（画像 P5、M-PM-002） | TC-INT-1130~1134 + 既有 test_frontend_contract.py 全部路由解析用例 | INT | 新写+现有 | participants、owner-candidates、unit-options、appeals FormData、registry sort/order、/me/housing 与席位新字段均 resolve 到路由并核字段 |
| 管理端选项接口 | TC-INT-1119 | INT | 新写 | IFC-351：形状同成员端、无业主姓名手机号、仅管理员 |
| 时区缺陷（GR-C-001 condition） | TC-INT-1140~1142；既有 TC-INT-504（冻结北京时间 00:30 复跑 OK，变异后 FAIL） | INT | 新写+现有 | UTC 前一日 16:30 时 term_end=本地昨天 的席位被 run_due_jobs 与 `/jobs/expire-committee-seats` 置 EXPIRED，今天到期的仍 ACTIVE |

## 测试数据需求

全部由用例自行构造（合成姓名、`tests.support.next_phone()`、临时 MEDIA_ROOT）；无 `[DATA_REQUIRED]`。会落盘的用例使用 `tempfile.TemporaryDirectory`，结束即清理；无持久存储写入，无需唯一化。

## 不可测项

| AC | 原因 |
|---|---|
| AC-252-02、AC-253-03 的"观感/三套风格实际可见" | `[NOT_TESTABLE: jsdom 无渲染引擎]`，CSS 规则存在性与时长已测，实际观感列入人工 M-1 |
| AC-252-04/05、AC-253-04 的"系统实际减少动效偏好" | `[NOT_TESTABLE]`，规则位置与 matchMedia 降级已测，真实偏好列入人工 M-2 |
| AC-252-01/03 的"真实点击命中区域" | `[NOT_TESTABLE: ::after 伪元素命中需真实布局]`，列入人工 M-3 |
| AC-246-05、AC-252-04 键盘；AC-250-06 读屏 | `[NOT_TESTABLE]`，列入人工 M-4、M-5 |
| 60m 上限/50MB 上传（AC-244-02 部署侧）、MySQL 迁移执行 | `[NOT_TESTABLE: 无服务器/MySQL]`，列入人工 M-6、M-7 |
| AC-244-03 真实刷新/关闭页面 | 暂存为纯页面内状态，jsdom 已验证卸载重进为空且 0 请求；真实浏览器观察列入人工 M-8 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-244 | TC-UNIT-1201~1203、1208、671；TC-INT-1001、1131；TC-E2E-1601、1611 | UNIT/INT/E2E |
| US-245 | TC-UNIT-1204~1207、669、670、672、1501~1503；TC-INT-1003~1011；TC-E2E-1601、1611 | UNIT/INT/E2E |
| US-246 | TC-UNIT-1210~1215；TC-INT-1119；TC-E2E-1611 | UNIT/INT/E2E |
| US-247 | TC-INT-1100~1103；TC-UNIT-1220；TC-E2E-1601、1605 | INT/UNIT/E2E |
| US-248 | TC-INT-1104~1107；TC-UNIT-1221；TC-E2E-1601、1605 | INT/UNIT/E2E |
| US-249 | TC-INT-1060~1062；TC-UNIT-1310~1312、1314、1510；TC-E2E-1602、1612 | INT/UNIT/E2E |
| US-250 | TC-INT-1065~1068；TC-UNIT-1301~1304、1313；TC-E2E-1602、1612 | INT/UNIT/E2E |
| US-251 | TC-INT-1063、1064、1071~1074；TC-UNIT-1320~1322；TC-E2E-1602、1612 | INT/UNIT/E2E |
| US-252 | TC-UNIT-1314~1316、1330、1331；TC-E2E-1612（真实命中/观感见人工 M-1~M-4） | UNIT/E2E |
| US-253 | TC-UNIT-1332、1340~1342、1330、1331；TC-E2E-1613（观感见人工 M-1/M-2） | UNIT/E2E |
| US-254 | TC-INT-1110~1113；TC-UNIT-1401、1530、1531；TC-E2E-1604、1614 | INT/UNIT/E2E |
| US-255 | TC-INT-1114~1118；TC-UNIT-1402~1405；TC-E2E-1604、1614 | INT/UNIT/E2E |
| US-256 | TC-INT-1020~1026；TC-UNIT-541(改写)；TC-E2E-1602 | INT/UNIT/E2E |
| US-257 | TC-INT-1030~1037、1088、1142；TC-E2E-1602、1603 | INT/E2E |
| US-259 | TC-INT-1080~1088；TC-UNIT-1520、1521；TC-E2E-1602、1603 | INT/UNIT/E2E |
| US-258（Should Have，非必需） | TC-INT-1040~1044；TC-UNIT-1410、1411；TC-E2E-1603 | INT/UNIT/E2E |
