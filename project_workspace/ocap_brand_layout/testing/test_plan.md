<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T14:30:24+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>requirements/user_stories.md（1.0.0）</file>
    <file>architecture/module_design.md（1.0.0，MOD-131 与测试影响清单）</file>
    <file>development/implementation_plan.md（2.0.0，含 DEF-001/002 修复节）</file>
    <file>development/code_review_report.md（1.1.0）</file>
    <file>testing/integration_test_report.md（0.1.0，GR-D-001 FAIL 依据）</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：品牌更名 Cyber@红枫岭 + Web 左侧导航布局 + 多分辨率自适应（INCREMENTAL，GROUP_D-003，缺陷回流 1/2 后重跑；1.1.0：GR-D-003 更正，补后端层）

## 测试策略

- **被测改动**：纯前端（Web 用户端/管理端、小程序登录页与标题、风格生成物）；后端、`frontend/src/shared/api.js`、`miniprogram/utils/api.js` 零改动。
- **范围 in**：MOD-119~130 的产品行为（jsdom 可测部分）；MOD-131 新建 12 个 spec；39 条既有用例的同步（逐条"原意 → 新写法"见下节）。
- **范围 out**：
  - （1.1.0 更正）后端产品代码零改动，但后端测试读取前端页面源码，故**后端全量用例纳入各层并实跑**（PM venv，见各报告）。1.0.0 的"后端不运行"属误判（GR-D-003-F01），已作废。
  - 真实视口度量、字体渲染、WXSS 真机表现：jsdom 不能度量，全部列入 e2e_test_report"人工验证清单"（NOT_TESTABLE）。
  - 不连接测试环境（本批无写入；浏览器人工验证由用户/运维在部署后完成）。
- **环境**：Node/vitest（`frontend/`：jsdom + @vue/test-utils + Element Plus + Pinia；`miniprogram/`：vitest + uni 桩）。无外网、无真实 API；HTTP 层全部 `vi.mock`。无 hil/sim 硬件概念（P11-1 = 无），运行方式列统一记 `-`。
- **分层机制**（画像 P4/P3 无 tag；vitest 以文件分层，用例 ID 前缀标识层级）：
  - UNIT = 纯函数/配置/静态文件扫描/单组件（`layout_menus`、`admin_session`、`brand`、`layout_css` + 小程序 `brand_login`）。
  - INT = 跨模块真实框架组件（SideNav+路由+Pinia、PortalLayout、AuthShell+主题仓库、路由表、用户菜单、契约）。
  - E2E（替代口径）= `layout_e2e.spec.js`：真实 App + 真实路由 + 假服务端的多步 jsdom 旅程（无浏览器框架）。
- **判定模式**：INCREMENTAL baseline——每层相对基线零新增失败且新写用例全部通过，才进入下一层；critical_path = 1.00。
- **基线（改动前实跑，invocation 给定）**：前端 281/281（26 文件）、小程序 104/104（15 文件）。改动后 GROUP_C 的 39 条失败由本组同步（已全部转绿，见各报告）。本次新写用例：前端 157（UNIT 53 / INT 101 / E2E 3）+ 小程序 15（UNIT）= 172。
- **门控**：见各层报告。0.1.0 时 INT 层有 2 条新写用例因产品缺陷失败（DEF-001、DEF-002）而门控 FAILED（GR-D-001）；GROUP_C-003 修复后（`art/index.js:10`、`PortalLayout.vue:49`），本次（0.2.0）按层重跑：UNIT PASSED → INT PASSED → E2E PASSED，全量回归 0 新增失败。

## 1.1.0 修订说明（GR-D-003 更正，重试 2/2）

- 后端 6 条契约用例（`test_frontend_contract.py`：test_phone_bind_change_contract、TC-INT-487/488/490；`test_owner_auth_v2_contract.py`：TC-INT-713、719）因页面拆分（Units.vue/Me.vue → portal/units/*、portal/me/*）失败，已把扫描范围改为"宿主 + 拆分文件"，断言一条未放宽；逐条"原意 → 新写法"见 integration_test_report 1.1.0。另预防性同步 `test_frontend_contract.py` 逐级选房字段检查一处。
- 已扫描 backend/tests 对 frontend/src、miniprogram 的全部路径引用：无指向已删除/不存在文件者（含 AdminThemeSwitcher.vue）。
- 本次新写用例 0 条（仅同步 6+1 处既有后端用例，TC 编号沿用）；后端 957/957 OK，前端 438/438，小程序 119/119；UNIT/INT/E2E 各层门控均 PASSED，全量回归 0 新增失败。
- 故事覆盖核对表不变（后端同步用例对应 US-157/151/152/178/199 等 owner_auth_v2、product_review 既有故事，非本批 Must Have 范围）。
- "契约测试"一节中"后端不运行"的说法随之作废：既有后端契约测试已实跑通过。

## 0.2.0 修订说明（缺陷回流 1/2 后重跑）

- 产品代码：仅 `frontend/src/brand/art/index.js`、`frontend/src/portal/PortalLayout.vue` 在 GR-D-001 之后被修改（见 implementation_plan 2.0.0）。
- **测试代码零改动**：`find frontend/tests miniprogram/tests -newer frontend/tests/layout_pages.spec.js` 仅命中 `miniprogram/tests/brand_login.spec.js`（修改时间 08:28:29，早于 0.1.0 报告 08:40，且在 PM 的 GR-D-001 复跑之前）；测试文件最后修改时间均早于本次所有计数运行，冻结成立。
- 缺陷回归用例即原失败用例（未改动）：TC-INT-874（DEF-001）、TC-INT-914（DEF-002）。修复前失败证据：0.1.0 实跑与 PM 的 GR-D-001 复跑均为 `2 failed | 436 passed (438)`；修复后本次 438/438。
- 已知局限：TC-E2E-801 仍按"进入 /units* 后"断言角标（`layout_e2e.spec.js:185` 注释写于修复前，测试冻结未改）；"刚登录即展开我的房屋看到角标"这一链路由 TC-INT-914 覆盖（真实登录链路：简要对象 → fetchMe 补全 → 展开）。

## 既有 39 条失败的同步（"原意 → 新写法"；不删用例、不降低业务断言）

复核方式：`git diff -U1 -- frontend/tests`（11 个既有文件 +173/−110），逐文件审阅；未删除任何 `it(`/`describe(`，业务断言保留或按需求改写，改写项均有需求依据（左侧导航取代顶部导航、个人中心/我的房屋/管理端分区拆页、OQ-B03）。共同点：`helpers.js::mountPage` 新增可选参数 `props`、`pinia`（向后兼容，缺省行为不变）。

| # | 既有用例（文件:用例） | 原意 | 新写法 | 判断 |
|---|---|---|---|---|
| 1 | admin_theme 口径1~4「管理端顶栏渐变/onHero/高亮」 | 顶栏渐变 + `.brand` onHero + `.topnav a.is-active` 白胶囊且 hover 在 active 之前 | 顶栏渐变与 `--on-hero` 保留；`.brand`→用户菜单触发器 onHero+透明；`.topnav a.is-active`→侧栏 `.side-item.is-active` 黑胶囊规则必须存在；hover 次序改为触发器 hover 先于 focus-visible | 断言数量不减；仅对象随结构迁移 |
| 2 | admin_theme「用户端 B 黑色胶囊原样保留」 | `.topnav a.is-active` 与 `.topnav` 胶囊容器 | `.side-item.is-active`、`.tabbar a.is-active` 黑胶囊原文、侧栏圆角规则，并新增 `not.toContain('.topnav')` | 加强 |
| 3 | admin_theme 口径8~9「AdminLayout 渲染 14 链接」 | 品牌、14 导航、高亮"业主清册"、风格入口存在 | 侧栏品牌文本、9 个一级、无 `.topnav`、`.user-menu-trigger` 存在、高亮"业主清册"，并新增展开"内容管理"后含"版式模板"（REQ-FUNC-153 仍可达） | 等价+加强 |
| 4 | admin_users TC-UNIT-411 | 注册用户目录展示 | 挂载传 `section:'registered'` | 仅传 prop |
| 5~11 | owner_auth_v2 TC-UNIT-667~673（7 条） | Units 整页上的姓名核对/转申诉/文案 | 667/668 挂 `UnitsPick`，670~672 挂 `UnitsAppeal`；669：OWNER_NOT_MATCHED 后断言跳 `/units/appeal`、仓库预填"张三"，再挂 `UnitsAppeal` 断言姓名带入、预填被消费、未选房屋禁用提交、选房后可用（原"已选房屋保留/认证产权不禁用"按 OQ-B03 改为"只带姓名、需重选"，该两条原断言被替换而非单纯删除，替换依据 module_design IFC-323/OQ-B03）；673：文案"请改用下方产权申诉"→"请改用"认证申诉""（实现偏差表已登记），其余"不得要求先绑定手机号""jpg/png/pdf"保留并对两页都断言 | 判断：669 属需求驱动的行为变更，用例仍守护同一 AC-201-01/02 |
| 12~13 | pages TC-WEB-028、029 | 绑定/换绑手机号区块 | 挂载 `MePhone`（原 `Me`） | 仅换挂载对象 |
| 14 | pages TC-WEB-030 | 改密 + 注销请求体 | 分别挂 `MePassword`、`MeCancel`，请求断言不变 | 同上 |
| 15 | product_review_rework2 TC-UNIT-591 | 审计日志中文/时间格式 | `AdminAudit` 传 `section:'logs'` | 仅传 prop |
| 16~20 | product_review_ui TC-UNIT-522/523/524/527/529 | Units 整页同住人链路 | 分别 `Units section=pick`、`UnitsPick`、`UnitsApplications`+`UnitsMyAppeals`（两页文本合并断言，断言不变）、`UnitsReview` | 仅换挂载对象 |
| 21~25 | product_review_ui TC-UNIT-530~534 | 个人中心头像/生日/注销 | 挂 `MeIdentity`/`MeProfile`/`MeCancel`（mountMe 加 component 参数） | 同上 |
| 26 | product_review_ui TC-UNIT-577 | 顶部导航非成员无报销/收入表/待办 | 改读 `nav.side-nav`；"个人中心"由"应含"改为"不应含"（移入右上角菜单，REQ-FUNC-206） | 需求驱动翻转 1 条断言 |
| 27~28 | product_review_ui TC-UNIT-543、544 | AdminUsers 启用/停用/是否/共 N 条；昵称搜索 | 管理员账号分区与注册用户分区各挂一次并合并文本断言（"是/否"取自管理员分区，"共 2 条"取自注册分区，其余原断言不变）；544 传 `section:'registered'` | 断言项全保留 |
| 29 | product_review_ui TC-UNIT-547 | 金额上限卡 | 传 `section:'limit'` | 仅传 prop |
| 30 | product_review_ui TC-UNIT-548 | 11 个确认键调用守护 | 扫描前剥离 HTML/行注释（新页头注释提到 `confirmDanger('…')`），守护对象仍是真实调用 | 防假阳性，不降级 |
| 31 | qa_e2e_extend TC-E2E-103 | `/me` 风格选择器 4 项 | `/me/style` | 仅路径 |
| 32~34 | qa_e2e_theme TC-E2E-101、102 | 在 `/me` 切换风格 | `/me/style`（4 处） | 仅路径 |
| 35~36 | qa_int_theme TC-INT-103 | 风格区块独立、保存失败回滚、个人资料区块仍在 | 挂 `MeStyle`，断言标题恰为["界面风格"]、`MeProfile` 页恰为["个人资料"]且无 radio | 加强 |
| 37~38 | qa_int_theme TC-INT-105 | 顶部导航高亮仅"决议"、底栏 5 项 | `.side-nav .side-item.is-active .side-label`；底栏 5 项保持，`.side-nav` 存在且无 `.topnav` | 等价 |
| 39 | qa_unit_theme TC-UNIT-108 | 只有 Me 引用 ThemePicker；管理端切换器 | 只有 `portal/me/MeStyle.vue` 引用；`AdminLayout` 含 `AdminUserMenu`，`AdminThemeSwitcher.vue` 已不存在，菜单含 `useAdminThemeStore`、`store.list`、`admin-theme-trigger` | 等价 |

结论：39 条均为"用例随被测结构迁移"，无删除；2 处断言按需求翻转/替换（#9 的 669、#26 的 577），其余等价或加强。

## AC 映射

用例位置缩写：`FT/` = `frontend/tests/`，`MT/` = `miniprogram/tests/`；方法名 = `it('TC-… / AC-…')` 标题；运行方式一律 `-`（无硬件）；测试数据一律为用例内 `vi.mock` 的假服务端与 `localStorage` 桩（不入库、不写持久存储）。全部为"新写"，既有用例仅作回归（见上节与各报告）。

| AC | 用例 ID | 级别 | 位置 |
|---|---|---|---|
| AC-207-01 | TC-INT-869、TC-UNIT-841、TC-UNIT-844、TC-UNIT-843 | INT/UNIT | FT/auth_shell、FT/brand |
| AC-207-02 | TC-INT-870、TC-INT-863 | INT | FT/auth_shell |
| AC-207-03 | TC-UNIT-842、TC-INT-834 | UNIT/INT | FT/brand、FT/layout_router |
| AC-207-04 | TC-UNIT-842、TC-E2E-803 | UNIT/E2E | FT/brand、FT/layout_e2e |
| AC-208-01 | TC-UNIT-884、TC-UNIT-888 | UNIT | MT/brand_login |
| AC-208-02 | TC-UNIT-881、TC-UNIT-882、TC-UNIT-845 | UNIT | MT/brand_login、FT/brand |
| AC-208-03 | TC-UNIT-889 | UNIT | MT/brand_login |
| AC-209-01 | TC-INT-861、863、866 | INT | FT/auth_shell |
| AC-209-02 | TC-INT-862、864、874（DEF-001 回归） | INT | FT/auth_shell |
| AC-209-03 | TC-UNIT-846、847、848 | UNIT | FT/brand |
| AC-209-04 | TC-UNIT-872、873（静态，真实视口见人工清单） | UNIT | FT/layout_css |
| AC-209-05 | TC-INT-868、TC-INT-867、TC-UNIT-894（(1)(2)(3) 机器可查部分）；(4) 人工 | INT/UNIT | FT/auth_shell、MT/brand_login |
| AC-209-06 | TC-INT-871 | INT | FT/auth_shell |
| AC-210-01 | TC-UNIT-801、TC-INT-881 | UNIT/INT | FT/layout_menus、FT/layout_pages |
| AC-210-02 | TC-UNIT-813、TC-INT-809 | UNIT/INT | FT/layout_menus、FT/layout_nav |
| AC-210-03 | TC-INT-808、TC-INT-821 | INT | FT/layout_nav、FT/layout_router |
| AC-210-04 | TC-INT-828 | INT | FT/layout_router |
| AC-211-01 | TC-UNIT-802、TC-INT-812、TC-INT-882 | UNIT/INT | FT/layout_menus、layout_nav、layout_pages |
| AC-211-02 | TC-UNIT-802 | UNIT | FT/layout_menus |
| AC-211-03 | TC-INT-896 | INT | FT/layout_pages |
| AC-211-04 | TC-UNIT-803、TC-INT-883、TC-INT-884 | UNIT/INT | FT/layout_menus、layout_pages |
| AC-212-01 | TC-INT-841、842、881 | INT | FT/user_menu、layout_pages |
| AC-212-02 | TC-INT-841、TC-UNIT-805 | INT/UNIT | FT/user_menu、layout_menus |
| AC-212-03 | TC-INT-846、847 | INT | FT/user_menu |
| AC-212-04 | TC-INT-843、844、TC-UNIT-819、821 | INT/UNIT | FT/user_menu、layout_menus |
| AC-212-05 | TC-INT-845、900 | INT | FT/user_menu、layout_pages |
| AC-213-01 | TC-INT-898、823、845、TC-UNIT-805 | INT/UNIT | FT/layout_pages、layout_router、user_menu |
| AC-213-02 | TC-INT-901 | INT | FT/layout_pages |
| AC-213-03 | TC-INT-899 | INT | FT/layout_pages |
| AC-213-04 | TC-INT-902 | INT | FT/layout_pages |
| AC-213-05 | TC-E2E-802（注销页入口）；确认弹窗取消不发请求沿用既有 TC-UNIT-534（回归，已同步挂 `MeCancel`） | E2E/回归 | FT/layout_e2e、product_review_ui |
| AC-213-06 | TC-INT-903 | INT | FT/layout_pages |
| AC-214-01 | TC-UNIT-804、TC-INT-890 | UNIT/INT | FT/layout_menus、layout_pages |
| AC-214-02 | TC-INT-804、824、890、891 | INT | FT/layout_nav、layout_router、layout_pages |
| AC-214-03 | TC-UNIT-806、TC-INT-810、885、886、887、892、**914（DEF-002 回归，已修复后 PASS）** | UNIT/INT | FT/layout_menus、layout_nav、layout_pages |
| AC-214-04 | TC-UNIT-669（同步，回归）、TC-E2E-801 | 回归/E2E | FT/owner_auth_v2、layout_e2e |
| AC-214-05 | TC-INT-924、既有 TC-UNIT-668（同步） | INT/回归 | FT/layout_contract、owner_auth_v2 |
| AC-215-01 | TC-INT-893、894、825 | INT | FT/layout_pages、layout_router |
| AC-215-02 | TC-INT-896、897 | INT | FT/layout_pages |
| AC-215-03 | TC-INT-895 | INT | FT/layout_pages |
| AC-215-04 | TC-INT-805、819、TC-UNIT-813 | INT/UNIT | FT/layout_nav、layout_menus |
| AC-216-01 | TC-INT-801、TC-UNIT-817 | INT/UNIT | FT/layout_nav、layout_menus |
| AC-216-02 | TC-INT-802 | INT | FT/layout_nav |
| AC-216-03 | TC-INT-803 | INT | FT/layout_nav |
| AC-216-04 | TC-INT-804、806 | INT | FT/layout_nav |
| AC-217-01 | TC-INT-807 | INT | FT/layout_nav |
| AC-217-02 | TC-INT-808、TC-UNIT-814 | INT/UNIT | FT/layout_nav、layout_menus |
| AC-218-01~04 | TC-UNIT-861、862、863（静态口径）；真实视口度量 MV-01 | UNIT | FT/layout_css |
| AC-219-01 | TC-UNIT-862、864；真实度量 MV-01 | UNIT | FT/layout_css |
| AC-219-02 | TC-UNIT-874、875；真实度量 MV-01、MV-02 | UNIT | FT/layout_css |
| AC-219-03 | TC-UNIT-869（触发器可点性静态）；真实度量 MV-01 | UNIT | FT/layout_css |
| AC-220-01 | TC-INT-882、888、TC-UNIT-867 | INT/UNIT | FT/layout_pages、layout_css |
| AC-220-02 | TC-INT-904、TC-UNIT-869 | INT/UNIT | FT/layout_pages、layout_css |
| AC-220-03 | TC-INT-904 | INT | FT/layout_pages |
| AC-220-04 | TC-INT-905、TC-UNIT-867 | INT/UNIT | FT/layout_pages、layout_css |
| AC-220-05 | TC-INT-831、905 | INT | FT/layout_router、layout_pages |
| AC-221-01 | TC-INT-831 | INT | FT/layout_router |
| AC-221-02 | TC-INT-830、889、TC-UNIT-807 | INT/UNIT | FT/layout_router、layout_pages、layout_menus |
| AC-221-03 | TC-INT-829 | INT | FT/layout_router |
| AC-222-01 | TC-UNIT-871、既有 theme.spec（构建对比度）；真实对比度由 `build.mjs --strict` 校验 | UNIT/回归 | FT/layout_css、theme.spec |
| AC-222-02 | TC-INT-903 | INT | FT/layout_pages |
| AC-222-03 | TC-INT-913、TC-INT-865 | INT | FT/layout_pages、auth_shell |
| AC-222-04 | TC-UNIT-871、既有 admin_theme（同步）| UNIT/回归 | FT/layout_css、admin_theme |
| AC-223-01 | TC-INT-910 | INT | FT/layout_pages |
| AC-223-02 | TC-UNIT-843、844、TC-UNIT-883 | UNIT | FT/brand、MT/brand_login |
| AC-223-03 | TC-INT-832 | INT | FT/layout_router |
| AC-224-01 | TC-UNIT-808、TC-INT-813、910 | UNIT/INT | FT/layout_menus、layout_nav、layout_pages |
| AC-224-02 | TC-UNIT-816、TC-INT-814、913 | UNIT/INT | FT/layout_menus、layout_nav、layout_pages |
| AC-224-03 | TC-UNIT-809 | UNIT | FT/layout_menus |
| AC-224-04 | TC-INT-822、832、833 | INT | FT/layout_router |
| AC-225-01 | TC-UNIT-810、TC-INT-813、907 | UNIT/INT | FT/layout_menus、layout_nav、layout_pages |
| AC-225-02 | TC-UNIT-810、TC-INT-814、909、826 | UNIT/INT | 同上 |
| AC-225-03 | TC-INT-906、908 | INT | FT/layout_pages |
| AC-225-04 | TC-INT-813、TC-UNIT-816 | INT/UNIT | FT/layout_nav、layout_menus |
| AC-225-05 | TC-INT-906（金额上限分区；保存非法金额沿用既有 TC-UNIT-547，已同步 `section:'limit'`） | INT/回归 | FT/layout_pages、product_review_ui |
| AC-226-01 | TC-UNIT-831、TC-INT-848、873 | UNIT/INT | FT/admin_session、user_menu、auth_shell |
| AC-226-02 | TC-INT-849 | INT | FT/user_menu |
| AC-226-03 | TC-INT-850、851、852 | INT | FT/user_menu |
| AC-226-04 | TC-INT-853、TC-UNIT-834 | INT/UNIT | FT/user_menu、admin_session |
| AC-226-05 | TC-INT-854、TC-UNIT-832、833、819 | INT/UNIT | FT/user_menu、admin_session、layout_menus |
| AC-227-01 | TC-INT-865、866、868（(4) 人工 MV-04） | INT | FT/auth_shell |
| AC-227-02 | TC-INT-865 | INT | FT/auth_shell |
| AC-227-03 | TC-INT-872 | INT | FT/auth_shell |
| AC-227-04 | TC-UNIT-872、873（静态；真实视口 MV-01/04、字体回退 MV-05） | UNIT | FT/layout_css |
| AC-228-01 | TC-UNIT-884、885、887、892、893、894、895（WXSS 真机 MV-03） | UNIT | MT/brand_login |
| AC-228-02 | TC-UNIT-886 | UNIT | MT/brand_login |
| AC-228-03 | TC-UNIT-888、890、891 | UNIT | MT/brand_login |
| AC-229-01 | TC-UNIT-801、TC-INT-809 | UNIT/INT | FT/layout_menus、layout_nav |
| AC-229-02 | TC-INT-809、TC-UNIT-813 | INT/UNIT | FT/layout_nav、layout_menus |
| AC-229-03 | TC-INT-889 | INT | FT/layout_pages |
| AC-230-01 | TC-INT-816、888 | INT | FT/layout_nav、layout_pages |
| AC-230-02 | TC-INT-817、888 | INT | FT/layout_nav、layout_pages |
| AC-230-03 | TC-INT-912（抽屉；用户端切换条显隐由 TC-UNIT-867 静态覆盖）；真实 767/768 切换 MV-01 | INT/UNIT | FT/layout_pages、layout_css |
| AC-230-04 | TC-INT-818、885 | INT | FT/layout_nav、layout_pages |
| AC-231-01 | TC-UNIT-861（静态）；真实度量 MV-01 | UNIT | FT/layout_css |
| AC-231-02 | TC-UNIT-874、875；真实度量 MV-02 | UNIT | FT/layout_css |
| AC-231-03 | TC-INT-910、911 | INT | FT/layout_pages |
| AC-231-04 | TC-INT-912 | INT | FT/layout_pages |
| 契约（REQ-NFUNC-040、画像 P5） | TC-INT-921~926 | INT | FT/layout_contract |
| 旅程（critical path） | TC-E2E-801、802、803 | E2E（替代） | FT/layout_e2e |

## 契约测试（规则 17，REQ-NFUNC-040、画像 P5）

- `frontend/tests/layout_contract.spec.js`（TC-INT-921~926，INT）：解析新页面/仓库/菜单对 `api.js` 的调用，逐个对应到 `api.js` 既有导出函数、方法+路径、令牌类别（用户端/管理端），再用静态解析把路径对应到后端 `urls.py` 路由；断言 `api.js` 导出集合与基线一致（未新增/删除接口）。
- `git diff --stat HEAD -- frontend/src/shared/api.js miniprogram/utils/api.js backend` 输出 0 行（零改动证据）。
- 【1.1.0 更正：已实跑，957/957 OK】既有后端契约测试 `backend/tests/integration/test_frontend_contract.py`：原称后端不运行（原因见范围 out），由于 `api.js` 零改动且 `layout_contract` 在前端侧已覆盖路径/方法解析，仍在报告中如实写"未执行"，不标 PASS。
- 前端既有 `api.spec.js`、小程序既有 `api.spec.js` 在全量回归中通过。

## 测试数据需求

- 全部在用例内构造（假服务端表、`localStorage`/`matchMedia` 桩）；无 `[DATA_REQUIRED]`；不写持久存储，无需唯一化。

## 不可测项

| AC | 原因 |
|---|---|
| AC-209-05(4) | 用户目视确认"有赛博科技感"，代码无法替代（NOT_TESTABLE，人工清单 MV-04） |
| AC-218-01~04、AC-219-01~03、AC-220-04/230-03（真实 767/768 切换）、AC-231-01/02、AC-227-04（真实视口） | jsdom 不计算布局，不能度量横向滚动/占用宽度/侧栏可见性；静态 CSS 口径已测，真实度量归人工清单 MV-01/MV-02（计入 NOT_TESTABLE 的"人工验证条目"，不计入通过率分母） |
| AC-209-03（真实字体加载失败回退） | 浏览器行为，人工清单 MV-05；静态口径（`font-display`、回退变量、随包文件）已由 TC-UNIT-846/847 测 |
| AC-228-01（WXSS 真机/开发者工具渲染） | 无微信开发者工具、`build:mp-weixin` 基线即失败（GR-C-001-F04），人工清单 MV-03；CSS 文件结构口径已由 TC-UNIT-892~895 测 |

## 故事覆盖核对

25 个故事逐个列出**已执行**用例（本次 0.2.0 全部实跑通过，结果见各层报告）。

| US（优先级） | 用例 ID（已执行） | 层 |
|---|---|---|
| US-207（Must） | TC-UNIT-841~844、TC-INT-834、869、870 | UNIT/INT |
| US-208（Must） | TC-UNIT-881~884、888、889 | UNIT |
| US-209（Must） | TC-UNIT-846~848、872、873、TC-INT-861~864、874（DEF-001 回归，已修复后 PASS）、866~868、871、TC-E2E-801 | UNIT/INT/E2E |
| US-210（Must） | TC-UNIT-801、813、TC-INT-808、809、821、828、881、TC-E2E-801 | UNIT/INT/E2E |
| US-211（Must） | TC-UNIT-802、803、TC-INT-812、882~884、896、TC-E2E-802 | UNIT/INT/E2E |
| US-212（Must） | TC-INT-841~847、TC-UNIT-805、819、821、TC-E2E-801 | UNIT/INT/E2E |
| US-213（Must） | TC-INT-823、898~903、TC-UNIT-805、TC-E2E-801 | UNIT/INT/E2E |
| US-214（Must） | TC-UNIT-804、806、TC-INT-804、810、824、885~887、890~892、TC-E2E-801（TC-INT-914 为 DEF-002 回归用例，修复后 PASS） | UNIT/INT/E2E |
| US-215（Must） | TC-INT-805、819、825、893~897、TC-UNIT-804、TC-E2E-801 | UNIT/INT/E2E |
| US-216（Must） | TC-INT-801~806、TC-UNIT-817、TC-E2E-801 | UNIT/INT/E2E |
| US-217（Should） | TC-INT-807、808、TC-UNIT-814 | UNIT/INT |
| US-218（Must） | TC-UNIT-861~863（静态口径；真实视口 MV-01 待人工） | UNIT |
| US-219（Must） | TC-UNIT-862、864、869、874、875（静态口径；真实视口 MV-01/02 待人工） | UNIT |
| US-220（Must） | TC-INT-831、882、888、904、905、TC-UNIT-867、869、TC-E2E-802 | UNIT/INT/E2E |
| US-221（Should） | TC-INT-829~831、889、TC-UNIT-807、TC-E2E-801 | UNIT/INT/E2E |
| US-222（Must） | TC-UNIT-871、TC-INT-865、903、913、TC-E2E-801、既有 theme/admin_theme 同步回归 | UNIT/INT/E2E |
| US-223（Must） | TC-UNIT-843、844、883、TC-INT-832、910、TC-E2E-803 | UNIT/INT/E2E |
| US-224（Must） | TC-UNIT-808、809、TC-INT-813、822、832、833、910、TC-E2E-803 | UNIT/INT/E2E |
| US-225（Must） | TC-UNIT-810、816、TC-INT-813、814、826、906~909、TC-E2E-803 | UNIT/INT/E2E |
| US-226（Must） | TC-UNIT-831~837、TC-INT-848~854、873、TC-E2E-803 | UNIT/INT/E2E |
| US-227（Must） | TC-INT-865、872、873、TC-UNIT-872、873、TC-E2E-803 | UNIT/INT/E2E |
| US-228（Should） | TC-UNIT-884~895 | UNIT |
| US-229（Must） | TC-UNIT-801、813、TC-INT-809、889、TC-E2E-801 | UNIT/INT/E2E |
| US-230（Must） | TC-INT-816~819、888、TC-UNIT-867、TC-E2E-802 | UNIT/INT/E2E |
| US-231（Must） | TC-UNIT-874、875、TC-INT-910~912、TC-E2E-803（静态与抽屉；真实视口 MV-01/02 待人工） | UNIT/INT/E2E |

Must Have 故事 22 个，全部至少 1 个已执行用例（空行 0）。critical path（Must Have 的 E2E 用例）口径：替代（jsdom 整 App 旅程 TC-E2E-801~803，已执行 3/3 PASS）；有 E2E 级用例的 Must Have 故事 20 个：19 个有 jsdom 旅程用例（US-207、209~216、220、222~227、229、230、231）+ US-208 以小程序最高层可执行用例（TC-UNIT-881~895 渲染登录页，15/15 PASS）替代；US-218、US-219 只能真实视口度量，NOT_TESTABLE，列人工清单 MV-01/02（计"待人工验证"）。覆盖率：可自动化的 Must Have 20/20 = 100%；含待人工的 20/22 = 90.9%。详见 e2e_test_report。
