<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-17T09:09:00+08:00</timestamp>
  <project_name>ocap_brand_layout</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>development/implementation_plan.md（2.0.0）</file><file>architecture/module_design.md（1.0.0）</file></input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告：品牌更名 + 左侧导航布局（INCREMENTAL，GROUP_D-003，缺陷回流 1/2 后重跑）

## 摘要

- 执行时间：2026-11-17T08:59:54+08:00 起（缺陷 DEF-001/002 修复后重跑；前端 11 文件 62.6s，小程序 41.8s）；环境：Node + vitest（jsdom），无外网，HTTP 全部 mock；后端零改动不运行。
- 命令（工作目录见括号）：
  - `(cd frontend && npx vitest run --passWithNoTests tests/layout_menus.spec.js tests/admin_session.spec.js tests/brand.spec.js tests/layout_css.spec.js tests/admin_theme.spec.js tests/admin_users.spec.js tests/qa_unit_theme.spec.js tests/product_review_ui.spec.js tests/product_review_rework2.spec.js tests/owner_auth_v2.spec.js tests/pages.spec.js)`
  - `(cd miniprogram && npx vitest run --passWithNoTests)`
- UNIT 层范围：新写 UNIT 用例 68 条（前端 53 + 小程序 15）+ 相关既有用例（前端 124 条：已同步的 11 个文件中的既有用例；小程序 104 条全量既有）。
- total = pass + fail + skip + blocked + not_testable = 296 + 0 + 0 + 0 + 0 = 296（前端 177 + 小程序 119；其中新写 68、既有 228）。
- 通过率 = pass/(pass+fail+blocked) = 296/296 = 100%；新写用例 68/68 通过。
- 判定模式 baseline：相对基线零新增失败（既有 228 条全部通过）且新写全部通过。**本层门控：PASSED**。
- 不可测：本层无 NOT_TESTABLE 用例（视口/字体/WXSS 项见 e2e_test_report 人工验证清单）。
- 后端：`git diff --stat HEAD -- backend frontend/src/shared/api.js miniprogram/utils/api.js` 输出 0 行（零改动，本次 09:07 复核）；本机无 Django（画像 P4），后端用例**未运行**，不标 PASS，不计入以上数字。
- 本层与 0.1.0 计数一致（296/296）：DEF-001 修复所在的 `art/index.js` 由 INT 层 TC-INT-874 守护，DEF-002 所在的 `PortalLayout.vue` 由 INT 层 TC-INT-914 守护；本层 UNIT 用例未受修复影响，重跑 0 失败。测试文件零改动（冻结，见 test_plan 0.2.0 修订说明）。

## 执行输出

```
(frontend, 11 files)  Test Files  11 passed (11)
                           Tests  177 passed (177)
                      exit=0
(miniprogram, 全量)   Test Files  16 passed (16)
                           Tests  119 passed (119)
                      exit=0
（以上为 2026-11-17 08:59:54 / 09:00:58 的最后一次执行输出）
```

按文件（前端）：layout_menus 21、admin_session 7、brand 10、layout_css 15（以上新写 53）；admin_theme 11、admin_users 2、qa_unit_theme 32、product_review_ui 31、product_review_rework2 12、owner_auth_v2 22、pages 14（既有，已同步，计 124）。小程序：brand_login 15（新写）+ 15 个既有文件 104。

## 分项结果

### 新写（前端，按模块）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-801~804 | AC-210-01、229-01、211-01/02/04、214-01、215-01/02 | MOD-120 菜单配置：业委会 9 项/非成员 6 项、二级项数、可见性规则 | PASS | — |
| TC-UNIT-805~811 | AC-212-02、213-01、214-03、221-02、224-01/03、225-01~03 | 个人中心 7 项、角标键、旧 hash 映射、管理端 9 项与二级项、菜单 key 唯一 | PASS | — |
| TC-UNIT-812~818 | AC-210-02、215-04、216-01/04、217-02、224-02、225-02/04 | isPathMatch/resolveActive/nextOpenKey 纯函数与输入校验 | PASS | — |
| TC-UNIT-819~821 | AC-212-04、226-05 | truncateLabel：12 字边界、码点计数、非字符串 | PASS | — |
| TC-UNIT-831~837 | AC-226-01/04/05、IFC-326 | adminSession：存取、无令牌不显示陈旧名、校验、存储不可用静默 | PASS | — |
| TC-UNIT-841~850 | AC-207-01/03/04、209-03、223-02、208-02、228-01、IFC-328 | 品牌常量、静态标题、9 处旧名残留 0、字体回退与随包、无 CDN、BrandMark | PASS | — |
| TC-UNIT-861~875 | AC-218-01~04、219-01/02、220-01/04、222-01、209-04、230-03、231-01/02 | 样式静态口径：取消最大宽、clamp、auto-fill、侧栏 sticky、媒体查询只含既有断点、44px 触控、无颜色字面量、AuthShell 分栏、管理端表格宽度合计 ≤1090 | PASS | — |

### 新写（小程序）

| TC | AC | 描述 | 结果 | 根因分类 |
|---|---|---|---|---|
| TC-UNIT-881~883 | AC-208-02、223-02 | pages.json 两处标题、tabBar 文案不变、无旧名 | PASS | — |
| TC-UNIT-884~887 | AC-208-01、228-01/02 | 三风格标题含品牌名、配图 4 view、无记忆回退 bento 且无入口、无颜色字面量 | PASS | — |
| TC-UNIT-888~891 | AC-208-01/03、228-03 | 三种登录入口、未注册提示、请求路径/字段不变、失败文案 | PASS | — |
| TC-UNIT-892~895 | AC-228-01、209-05(1)、ADR-032 | 每风格 .mp.css 定义配图、只用 CSS、含科技元素、三版互异 | PASS | — |

### 既有用例同步（39 条失败 → 全部转绿）

逐条"原意 → 新写法"见 test_plan.md「既有 39 条失败的同步」；本层涉及 admin_theme（3）、admin_users（1）、owner_auth_v2（7）、pages（3）、product_review_rework2（1）、product_review_ui（15）、qa_unit_theme（1）共 31 条，全部 PASS；其余 8 条（qa_e2e_extend 1、qa_e2e_theme 3、qa_int_theme 4）见集成/E2E 报告。复核结论：无删除用例，业务断言不降低；2 处按需求翻转/替换（TC-UNIT-669 OQ-B03、TC-UNIT-577 个人中心移出导航），依据已写明。

## 与基线对比（baseline 模式）

- 基线：前端 281/281（26 文件）、小程序 104/104（15 文件）。
- 本层既有用例失败清单：无（0 条）。新增失败：0。小程序既有 104 条全部通过。

## 失败汇总（需路由给开发）

无（本层 0 失败）。
