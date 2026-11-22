<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-22T12:52:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/requirements/user_stories.md</file>
    <file>project_workspace/ocap_navigation_ia/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>project_workspace/ocap_navigation_ia/development/implementation_plan.md</file>
    <file>project_workspace/ocap_navigation_ia/development/code_review_report.md</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划 — 导航信息架构整合（Web + 微信小程序）

## 测试策略

- **被测改动**：MOD-174~182（Web 菜单与下拉、身份页 Tab、路由兼容、窄屏“我的”分组；小程序三 Tab、我的页分组、邮箱/注销页）。
- **范围**：
  - In scope：菜单结构与文案、页内 Tab 与数量角标、深链白名单、下拉动效参数与 CSS、分组设置入口、小程序三 Tab 切换与子 Tab、邮箱验证与账号注销调用链、前后端接口契约。
  - Out of scope：真实微信开发者工具渲染、真机操作、树莓派部署（E2）、生产数据库。
- **环境**：Node + Vitest（前端 51 文件、小程序 20 文件）；Django `config.test_settings`（SQLite 测试库）；不连生产、不联网。
- **判定模式**：baseline 零新增失败（基线=GROUP_C 结束时的全绿：frontend 568、mini 138、backend 1167）。
- **基线来源**：`code_review_report.md` 1.0.0 自验证结果。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置 | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-299-01/02 | TC-UNIT-804、TC-E2E-1613、TC-INT-803/804/816 | UNIT/INT/E2E | sim | 现有 | layout_menus / batch1118_e2e / layout_nav | 已登录 | 读取/点击二级菜单 | 3 项且文案“我的认证与申述” | 静态菜单 |
| AC-299-03/04 | TC-WEB-910、TC-E2E-801 | INT/E2E | sim | 现有 | identity_property_identity_page / layout_e2e | 产权业主 | 进入身份页 | 页内 Tab 可进入申诉/审批 | 合成 housing |
| AC-300-01/02/03/04 | TC-WEB-910/911/912、TC-INT-1103/1104 | INT | sim | 现有+新写 | identity_property_identity_page / navigation_ia | 业主/游客 | 加载身份页 | 双 Tab、角标、非业主无 Tab | 合成 housing |
| AC-301-01/02 | TC-INT-824、TC-MP-905 | INT | sim | 现有 | layout_router / identity_property_pages | — | 路由/页面 | 同住人申请分区与子 Tab | 合成申请 |
| AC-302-01/02/03/04 | TC-UNIT-1101、TC-INT-841/898/899/904 | UNIT/INT | sim | 现有+新写 | navigation_ia / user_menu / layout_pages | 已登录 | 打开右上角菜单/“我的”页 | 两组、6 项、文案“绑定手机” | 合成 me |
| AC-303-01/02 | TC-INT-841 | INT | sim | 现有 | user_menu | 已登录 | 点击退出登录 | 清 token 回 /login | 合成 me |
| AC-304-01/02/03/04 | TC-E2E-1101~1104 | E2E | sim | 新写 | mini tests/navigation_ia | 业主/游客 | 切换三个 Tab 与子 Tab | 面板可见性、审批行、申请入口 | 合成 housing |
| AC-305-01/02/03/04 | TC-UNIT-1101、TC-E2E-1105/1106 | UNIT/INT/E2E | sim | 新写 | mini tests/navigation_ia | 已登录 | 查看/点击设置项 | 两组、入口文案、跳转、主题保存 | 合成 me |
| AC-306-01/02/03/04 | TC-INT-830、TC-INT-972、TC-INT-1103/1104/1105 | INT | sim | 现有+新写 | layout_router / identity_property_menu_router / navigation_ia | 业主/游客 | 访问旧地址与非法 tab | 重定向/白名单回落 | 合成 housing |
| AC-307-01/02 | TC-WEB-910、TC-E2E-801 | INT/E2E | sim | 现有 | identity_property_identity_page / layout_e2e | 业主 | 审批一条 | 侧栏与 Tab 角标同步递减 | 2 条待审批 |
| AC-308-01/02/03 | TC-UNIT-1102、TC-INT-1101/1102 | UNIT/INT | sim | 新写 | navigation_ia | 已登录 | 读取常量/组件 props/CSS | 400ms、180ms、reduce→0s | 静态源码 |
| AC-309-01/02 | TC-UNIT-1101、TC-MP-903 | UNIT/INT | sim | 新写+现有 | navigation_ia / identity_property_pages | — | 读取两端常量 | 逐字一致、菜单无“认证申诉” | 静态常量 |
| AC-310-01/02/03 | TC-E2E-1105/1107/1108、TC-INT-904 | INT/E2E | sim | 新写+现有 | mini navigation_ia / layout_pages | 已登录 | 遍历入口与新增页面 | 入口齐全、可调用、无权限过滤 | 合成 me |

## 测试数据需求

- 前端/小程序：合成 `housing`（OWNER/HEAD 与游客两种）、`me`（含/不含手机号）、待审批与我的申诉列表；均在各 spec 内构造，无 `[DATA_REQUIRED]`。
- 后端契约：复用仓库既有 fixture；无外部数据。

## 不可测项

| AC | 原因 |
|---|---|
| AC-308-02（真实鼠标悬停时序） | 组件测试只能断言 props 与 CSS；真实 180ms 悬停意图需人工在浏览器观察，列入 E2E 报告人工验证清单。 |
| 小程序真机渲染与微信审核 | 本批次不部署、不真机运行；仅构建 + 组件测试。 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-299 | TC-UNIT-804、TC-INT-803/804/816、TC-E2E-1613 | UNIT/INT/E2E |
| US-300 | TC-WEB-910/911/912、TC-INT-1103/1104、TC-E2E-801 | INT/E2E |
| US-301 | TC-INT-824、TC-MP-905 | INT |
| US-302 | TC-UNIT-1101、TC-INT-841/898/899/904 | UNIT/INT |
| US-303 | TC-INT-841 | INT |
| US-304 | TC-E2E-1101~1104 | E2E |
| US-305 | TC-UNIT-1101、TC-E2E-1105/1106/1107/1108 | UNIT/INT/E2E |
| US-306 | TC-INT-830、TC-INT-972、TC-INT-1103/1104/1105、TC-E2E-801 | INT/E2E |
| US-307 | TC-WEB-910、TC-E2E-801 | INT/E2E |
| US-309 | TC-UNIT-1101、TC-MP-903 | UNIT/INT |
| US-310 | TC-E2E-1105/1107/1108、TC-INT-904 | INT/E2E |
| US-308（Should） | TC-UNIT-1102、TC-INT-1101/1102 | UNIT/INT |
