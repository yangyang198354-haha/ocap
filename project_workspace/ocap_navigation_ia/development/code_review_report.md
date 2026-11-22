<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-22T12:32:00+08:00</timestamp>
  <project_name>ocap</project_name>
  <version>1.1.0</version>
  <input_files>
    <file>project_workspace/ocap_navigation_ia/architecture/module_design.md</file>
    <file>project_workspace/ocap_navigation_ia/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — 导航信息架构整合（Web + 微信小程序）

## 摘要

- 改动规模：`git diff --stat` 39 个已跟踪文件，542 行新增 / 477 行删除；另有 8 个新建源码文件（3 个小程序面板、2 个页面、1 个常量、2 份开发文档）。
- 五维平均分：9.3 / 10（Correctness 9.2、Security 9.6、Performance 9.4、Maintainability 9.2、Testability 9.1）。
- 问题统计：CRITICAL 2（已修复 2）/ MAJOR 2（已修复 2，含 GROUP_D 回流的 DEF-001）/ MINOR 3（已修复 3）。
- 1.1.0 回流复测：frontend 51 文件/575 用例、miniprogram 20 文件/147 用例、backend 1167 用例全部通过。
- 未解决的 CRITICAL：无。
- 产品代码无后端改动、无迁移、无新增依赖。

## 文件 → MOD/IFC 映射

| 文件 | MOD/IFC |
|---|---|
| `frontend/src/layout/menus.js` | MOD-174 / IFC-393 |
| `frontend/src/portal/PortalUserMenu.vue`、`frontend/src/shared/style.css` | MOD-175 / IFC-396 |
| `frontend/src/portal/units/UnitsIdentity.vue`、`frontend/src/portal/Units.vue` | MOD-176 / IFC-394 |
| `frontend/src/router/index.js` | MOD-177 / IFC-395 |
| `frontend/src/portal/Me.vue` | MOD-178 / IFC-397 |
| `frontend/src/portal/me/MePhone.vue` | MOD-174/175（C-363 文案） |
| `miniprogram/pages/units/index.vue`、`components/{IdentityPane,AppealPane,ResidentPane}.vue` | MOD-179 / IFC-398 |
| `miniprogram/pages/me/index.vue`、`pages/phone/index.vue`、`pages.json` | MOD-180 / IFC-399 |
| `miniprogram/utils/menu.js` | MOD-181 / IFC-400 |
| `miniprogram/utils/api.js`、`pages/email/index.vue`、`pages/cancel/index.vue` | MOD-182 / IFC-401 |

## 自验证结果

| 命令 | 结果 |
|---|---|
| `npm test`（frontend） | 首轮：`Test Files 50 passed`；`Tests 568 passed`。1.1.0 回流后：`Test Files 51 passed`；`Tests 575 passed` |
| `npm run build`（frontend） | 构建成功，仅 Element Plus 既有 chunk 体积警告 |
| `npm test`（miniprogram） | 首轮：`Test Files 19 passed`；`Tests 138 passed`。1.1.0 回流后：`Test Files 20 passed`；`Tests 147 passed` |
| `$env:UNI_INPUT_DIR=<miniprogram 根>; npm run build:mp-weixin` | `DONE Build complete.` |
| `python manage.py test --settings=config.test_settings`（backend） | `Ran 1167 tests ... OK (skipped=2)` |

说明：小程序 uni CLI 默认输入目录为 `src/`，本仓库源码位于 `miniprogram/` 根，构建需显式设置 `UNI_INPUT_DIR`（已在报告中记录，未改项目配置）。构建产物 `miniprogram/dist`、`project.config.json`、`project.private.config.json` 已清理。

## 按模块评审

### MOD-174 Web 菜单与文案配置
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-175 Web 用户下拉菜单
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-006 | MINOR | `miniprogram/pages/units/*` | 新样式曾使用 `var(--accent-text, #4f46e5)` 颜色字面量兜底，违反主题测试约束 | FIXED |

### MOD-176 Web 身份与房屋页 Tab 化
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MAJOR | `UnitsIdentity.vue:applyInitialTab` | 同一组件实例从 `/units?tab=review` 切到 `/me/identity` 时未回到默认 Tab | FIXED |

### MOD-177 Web 路由兼容与初始 Tab
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-178 Web 窄屏“我的”页分组
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 9/10 | 10/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-179 小程序“我的房屋”三 Tab
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | CRITICAL | `IdentityPane.vue:loadReview` | 组件挂载时 `ownsAnyUnit` 尚为 false，审批列表被跳过且无后续加载，导致“待我审批”永远为空 | FIXED（`watch(ownsAnyUnit)` 触发加载） |
| CR-002 | CRITICAL | `IdentityPane.vue` 审批面板 | 非产权业主仍渲染审批卡片 DOM（仅隐藏子 Tab），违反 AC-300-03 / AC-234-04 | FIXED（`v-if="ownsAnyUnit"`） |
| CR-004 | MINOR | `IdentityPane.vue` | 拆分后丢失旧页 `id="review"` 定位锚点，兼容跳转断言失败 | FIXED |

### MOD-180 小程序“我的”页分组
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MINOR | `pages/units/index.vue`、`IdentityPane.vue` | Tab 常量循环变量命名为 `item`，被后端字段契约扫描误判为接口字段 | FIXED（改名为 `t` / `st`） |

### MOD-181 小程序菜单常量
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无 | — |

### MOD-182 小程序邮箱验证与账号注销页
**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 10/10 | 9/10 | 9/10 |

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 无（输入校验含邮箱正则、6 位验证码、11 位手机号；注销二次确认） | — |

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无未修复 MAJOR。

## 缺陷修复

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-001（GROUP_D 回流，MAJOR） | `miniprogram/utils/confirm.js` | 注销页调用 `confirmDanger('cancelAccount')`，`CONFIRM_TEXTS` 缺少该键，`confirmDanger` 以“未知的确认类型”拒绝，点击确认后不发起 `/me/cancel` | 在 `CONFIRM_TEXTS` 增加 `cancelAccount`（标题“注销账号”+ 两条后果）；重跑小程序全量 147 用例通过，TC-E2E-1108 由 FAIL 转 PASS |

## 现有测试调整（行为变更导致，逐条说明）

| 文件 | 调整内容 | 原因 |
|---|---|---|
| `frontend/tests/layout_menus.spec.js` | 二级项 4→3；用户菜单 7→6（分组展平顺序）；`/units/appeal` 文案 | ADR-166/168 |
| `frontend/tests/layout_nav.spec.js` | 侧栏/切换条 4→3，文案改“我的认证与申述” | REQ-FUNC-297/299 |
| `frontend/tests/layout_pages.spec.js` | 身份页改用 Tab 断言；绑定手机标题；“我的”页分组与退出按钮位置 | ADR-167、REQ-FUNC-309 |
| `frontend/tests/layout_router.spec.js` | `/units/review` → `?tab=review`；`/units/appeals` 改为重定向 | ADR-170 |
| `frontend/tests/identity_property_menu_router.spec.js` | 同上，并移除右上角“我的身份与房屋”断言 | ADR-166/170 |
| `frontend/tests/identity_property_identity_page.spec.js` | 底部卡片→页内 Tab；业主/游客分支；定位行为 | ADR-167 |
| `frontend/tests/identity_property_e2e.spec.js` | 身份页标题由 Tab 承载；Tab 数量与 `?tab=review` | ADR-167/170 |
| `frontend/tests/layout_e2e.spec.js` | 二级项数量、菜单项、`/units/review` 落点 | 同上 |
| `frontend/tests/batch1118_e2e.spec.js` | “认证申诉”→“我的认证与申述” | REQ-FUNC-298 |
| `frontend/tests/user_menu.spec.js` | 8→7 项并断言两个组标题 | REQ-FUNC-305~310 |
| `frontend/tests/layout_css.spec.js` | 允许 `prefers-reduced-motion: reduce` 条件 | REQ-NFUNC-061 |
| `frontend/tests/pages.spec.js` | 手机号页标题统一“绑定手机” | C-363 |
| `miniprogram/tests/pages.spec.js` | 同上 | C-363 |
| `miniprogram/tests/owner_auth_v2.spec.js` | `pickUnit` 支持面板索引，申诉用第 2 个选择器 | ADR-169 |
| `miniprogram/tests/product_review_ui.spec.js` | UnitPicker 2→3，申请用第 3 个 | ADR-169 |
| `miniprogram/tests/identity_property_pages.spec.js` | 审批标题改为“包含”；申请用第 3 个选择器 | ADR-169 |
| `miniprogram/tests/{brand_login,qa_e2e_pages,qa_unit_theme,qa_e2e_extend,theme}.spec.js` | 页面数 14→16；页面目录排除 `components/` | 新增邮箱/注销页与面板拆分 |
| `backend/tests/integration/test_frontend_contract.py` | 小程序契约源改为“宿主 + components”并集 | MOD-179 拆分 |
| `backend/tests/integration/test_owner_auth_v2_contract.py` | 同上（createAppeal 键、OWNER_NOT_MATCHED） | MOD-179 拆分 |
| `backend/tests/integration/test_phone_match_contract.py` | 同上（unit_type_label/area_display） | MOD-179 拆分 |

## 改动范围说明

`git status` 中 `project_workspace/_kb_inbox.jsonl`、`project_workspace/ocap_appeal_center/phase_status.md`、`deployment_report.md`、`registry_import_投票权清单.xlsx` 为本批次开始前已存在的用户/前序批次改动，本次未触碰。本次新增源码文件：

- `miniprogram/utils/menu.js`
- `miniprogram/pages/units/components/{IdentityPane,AppealPane,ResidentPane}.vue`
- `miniprogram/pages/email/index.vue`
- `miniprogram/pages/cancel/index.vue`
