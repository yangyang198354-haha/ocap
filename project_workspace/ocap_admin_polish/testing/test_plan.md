<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T23:32:38.0156563+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_admin_polish/requirements/user_stories.md</file>
    <file>project_workspace/ocap_admin_polish/development/implementation_plan.md</file>
    <file>project_workspace/ocap_admin_polish/development/code_review_report.md</file>
    <file>project_workspace/ocap_admin_polish/architecture/module_design.md</file>
  </input_files>
  <phase>PHASE_07,PHASE_08,PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# 测试计划：管理端打磨（INCREMENTAL）

## 测试策略

- 被测改动：专有部分新拼接规则与存量重生成（US-132~US-138）、管理端多风格（US-139~US-144）。
- 范围：in scope = 本次 MOD-064~MOD-073 的产品行为与相关既有回归；out of scope = 15 页 × 3 风格的人工视觉走查（列入人工验证清单）、部署后页面冒烟（E2 由部署阶段执行）。
- 环境：Windows 开发机；Python 3.14.6 / Django 6.0.6（画像 P4 已知差异）；后端 SQLite 内存测试库（`config.test_settings`，`MIGRATION_MODULES` 置空，迁移函数由测试直接调用）；前端 vitest 2.1.9 + jsdom；小程序 vitest 2.1.9。
- 判定模式：INCREMENTAL / baseline；每层相对基线零新增失败，新写用例全部通过；critical path 1.00。
- 基线：后端 530 tests OK (skipped=9)；前端 154 passed / 2 failed（既有 Windows 主题环境问题）；小程序 75 passed。GROUP_C 已修复前端既有环境失败（`theme.spec.js` 临时目录改 `os.tmpdir()`）。
- 层执行顺序：单元 → 集成 → E2E；各层通过后再执行全量回归（后端含 smoke，前端、小程序）。

## AC 映射

| AC | 用例 ID | 级别 | 运行方式 | 现有/新写 | 位置（文件::方法） | 前置 | 动作 | 预期 | 测试数据 |
|---|---|---|---|---|---|---|---|---|---|
| AC-132-01~04 | TC-UNIT-201/202 | unit | auto | 新写 | `backend/tests/unit/test_specific_part_rule.py::test_tc_unit_201/202` | 无 | 调用 build_specific_part | 新格式字符串 | 1栋/1单元/1/101 等 |
| AC-132-05 | TC-INT-134 | integration | auto | 现有 | `test_registry_import_enhancement.py::test_tc_int_134_import_missing_levels` | 导入文件缺楼栋/户号 | 导入 | 拒绝并提示缺少字段 | CSV 行 |
| AC-133-01~09 | TC-UNIT-203/204/205/206 | unit | auto | 新写 | `test_specific_part_rule.py` 同名方法 | 无 | 调用规则 | 后缀不重复、非数字原样、楼层省略、strip、3.0 原样 | 需求金标样例 |
| AC-134-01/02/03 | TC-INT-401 | integration | auto | 新写 | `test_specific_part_regeneration.py::test_tc_int_401_regenerate_and_reverse` | 旧格式 3 条 + 业主/手机号 | 执行迁移函数 | 新格式、字段不变、幂等、可逆 | 5742 规模前 3 条 |
| AC-134-04 | TC-INT-402 | integration | auto | 新写 | `test_specific_part_regeneration.py::test_tc_int_402_conflict_aborts_whole_batch` | 两条记录新值相同 | 执行迁移 | RuntimeError，数据不变 | 1/101 与 1层/101号 |
| AC-134-05 | TC-INT-404 | integration | auto | 新写 | `test_specific_part_regeneration.py::test_tc_int_404_review_lists_non_numeric_rooms` | 户号“整栋” | 执行迁移 | stdout 含 review=1 与明细 | 建设南路146号 |
| AC-134-06 | TC-INT-405 | integration | auto | 新写 | `test_specific_part_regeneration.py::test_tc_int_405_large_batch_under_time_budget` | 5742 条 | 执行迁移并计时 | <60 秒 | 合成数据 |
| AC-135-01/02/06 | TC-INT-421 | integration | auto | 新写 | `test_specific_part_display_consistency.py::test_tc_int_421_same_value_across_admin_and_portal` | 一条记录 + 认证用户 | 读管理端列表/房屋关系与 /me | 三处 specific_part 一致；/me 不含 PII | 1栋1单元1层101号 |
| AC-135-03/04 | TC-INT-422 | integration | auto | 新写 | 同上 `test_tc_int_422_old_format_keyword_does_not_match` | 一条记录 | 新旧关键词搜索 | 新命中、旧不命中 | 1栋1单元 / 1栋-1单元 |
| AC-135-05 | TC-INT-132/133 | integration | auto | 现有 | `test_registry_import_enhancement.py` | 车库/商铺记录 | 读 options | 选项文案为字段原值 | 车库/A-088 |
| AC-136-01/02/04 | TC-INT-413 | integration | auto | 新写 | `test_specific_part_consistency.py::test_tc_int_413_single_create_and_edit` | 管理员令牌 | 新增、重复新增、编辑楼层 | 201 / 409 UNIT_EXISTS / 新标识 | 1栋1单元 |
| AC-136-03 | TC-INT-416 | integration | auto | 新写 | `test_specific_part_consistency.py::test_tc_int_416_non_admin_denied` | 普通用户令牌 | POST 新增 | 401/403，条数不变 | 无 |
| AC-137-01~03 | TC-INT-412 | integration | auto | 新写 | `test_specific_part_consistency.py::test_tc_int_412_import_groups_equivalent_fields` | 管理员令牌 | 导入两行等价字段 | 合并为 1 个专有部分、2 位业主 | 1/101 与 1层/101号 |
| AC-137-04 | TC-INT-102 | integration | auto | 现有 | `test_registry_import_enhancement.py::test_tc_int_102_non_admin_denied` | 普通用户令牌 | 导入/预检 | 401/403 | 无 |
| AC-137-05 | TC-INT-144/145 | integration | auto | 现有 | `test_registry_import_enhancement.py` | 预检/正式导入 | 比对数字与 changes | 完全一致、新格式 | CSV |
| AC-137-06 | TC-INT-136 | integration | auto | 现有 | `test_registry_import_enhancement.py::test_tc_int_136_import_parking_row` | 车位行 | 导入 | 车库A-088 | 车库/A-088 |
| AC-137-07 | TC-E2E-302/303 | e2e | auto | 现有 | `test_registry_import_scale_journeys.py` | 20000 行 | 预检+正式 | 各自 ≤60 秒 | 合成 CSV |
| AC-138-01/02 | TC-INT-105、TC-UNIT-110 | integration/unit | auto | 现有（已同步） | 模板测试 | 下载模板 | 检查列说明与示例 | 含后缀规则、6 行示例 | 模板 |
| AC-138-03 | TC-INT-415 | integration | auto | 新写 | `test_specific_part_consistency.py::test_tc_int_415_template_examples_are_single_source` | 下载 csv 模板 | 预检+正式导入 | failed=0，标识与 spec.examples 一致 | 模板示例 |
| AC-138-04 | TC-INT-303~305 | integration | auto | 现有 | `test_registry_import_xlsx_defects.py` | xlsx 文本列 | 读取 | 前导零/3.0 不改写 | xlsx |
| AC-139-01~02 | admin_theme.spec.js::口径 8（结构）、TC-UNIT-503（前端） | integration | auto | 新写 | `frontend/tests/admin_theme.spec.js`、`admin_theme_store.spec.js` | Pinia + Element Plus | 渲染顶栏、选择风格 | 13 链接 + 入口；选择即时生效 | 3 套风格 |
| AC-139-03 | TC-UNIT-108（前端） | integration | auto | 现有（已同步） | `frontend/tests/qa_unit_theme.spec.js` | 风格注册表 | 渲染入口 | 选项由注册表驱动 | 3 套 |
| AC-139-04 | TC-UNIT-503（前端） | integration | auto | 新写 | `admin_theme_store.spec.js` | PUT 失败 | 选择风格 | 回滚并抛出 | mock 失败 |
| AC-139-05 | TC-E2E-105（前端） | e2e | auto | 现有（已同步） | `frontend/tests/qa_e2e_pages.spec.js` | 管理端登录页 | 打开 | 无风格入口 | 无 |
| AC-140-01~03 | TC-UNIT-501/502（前端） | integration | auto | 新写 | `admin_theme_store.spec.js` | 设备记忆/账号值 | init/reconcile | 默认 B、下线回退、失败保持 | mock |
| AC-141-01~05 | TC-UNIT-502/503/504（前端）、`test_admin_theme_preference_api.py` | integration/unit | auto | 新写 | `admin_theme_store.spec.js`、`backend/tests/integration/test_admin_theme_preference_api.py` | 管理员令牌 | 往返、隔离、登出 | 账号值权威、跨设备、设备记忆保留 | mock/DB |
| AC-142-01~06 | admin_theme.spec.js::口径 1~9 | integration | auto | 新写 | `frontend/tests/admin_theme.spec.js` | 读取源文件/生成物 | 作用域、渐变、对比度、结构 | 全部断言通过；视觉走查另列 | 主题文件 |
| AC-143-01~03 | TC-UNIT-504（前端）、`test_admin_theme_preference_api.py` | integration/unit | auto | 新写 | `admin_theme_store.spec.js`、`test_admin_theme_preference_api.py` | 两端 store/令牌 | 交叉选择 | 互不影响 | mock/DB |
| AC-144-01~04 | TC-UNIT-101（前端）、TC-INT-101（前端） | integration | auto | 现有（已同步） | `theme.spec.js`、`qa_int_theme.spec.js` | 路由 | 进入管理端 | 不再强制 B；默认 B 保持 | localStorage |
| REQ-NFUNC-19 | TC-INT-401/402/403 | integration | auto | 新写 | 迁移测试 | 旧数据 | 执行迁移 | 字段/子表/引用不变 | 3 条 |
| REQ-NFUNC-20 | 全量回归 | 全部 | auto | 现有 | 见各报告 | — | 复跑 | 零新增失败 | — |
| REQ-NFUNC-21 | TC-UNIT-306~308（前端） | integration | auto | 新写 | `admin_theme.spec.js` | 主题文件 | 对比度/叠加层 | ≥4.5、仅深色叠加 | 渐变采样 |
| REQ-NFUNC-22 | TC-UNIT-104（前端） | integration | auto | 现有（已同步） | `qa_unit_theme.spec.js` | index.html 脚本 | vm 沙箱执行 | 分键、无闪烁前提 | localStorage |
| REQ-NFUNC-23 | TC-INT-405、TC-E2E-302/303 | integration/e2e | auto | 新写/现有 | 迁移与导入规模测试 | 5742/20000 条 | 执行并计时 | <60 秒 | 合成数据 |

## 测试数据需求

- 需求金标样例（1栋1单元1层101号、1栋负1层924号、10栋1层1号、圣灯路155号1层、建设南路160号1层A、车库A-088、整栋、3.0、B1、-1）全部为虚构。
- 测试用户手机号由 `tests/support.py:next_phone()` 生成；无真实个人信息。
- 迁移 5742 条与导入 20000 行为合成数据；不含真实清册。
- `[DATA_REQUIRED]`：无。

## 不可测项

| AC | 原因 |
|---|---|
| AC-142-01/02/03/04/06 的最终视觉效果 | 需真实浏览器逐页目视；自动化只覆盖源文件/生成物规则与结构。列入人工验证清单。 |
| AC-139-01 的下拉菜单真实触控布局（窄屏） | jsdom 无布局引擎；列入人工验证清单。 |

## 故事覆盖核对

| Must Have US | 用例 ID（已执行） | 层 |
|---|---|---|
| US-132 | TC-UNIT-201、TC-UNIT-202、TC-INT-413 | unit / integration |
| US-133 | TC-UNIT-203、TC-UNIT-204、TC-UNIT-205、TC-UNIT-206 | unit |
| US-134 | TC-INT-401、TC-INT-402、TC-INT-403、TC-INT-404、TC-INT-405 | integration |
| US-135 | TC-INT-421、TC-INT-422、TC-INT-423、TC-INT-132、TC-INT-133 | integration |
| US-136 | TC-INT-413、TC-INT-416 | integration |
| US-137 | TC-INT-412、TC-INT-144、TC-INT-145、TC-E2E-302、TC-E2E-303 | integration / e2e |
| US-138 | TC-INT-415、TC-INT-105、TC-UNIT-110 | integration / unit |
| US-139 | TC-UNIT-501（前端）、TC-UNIT-503（前端）、TC-UNIT-108（前端）、TC-E2E-105（前端） | integration / e2e |
| US-140 | TC-UNIT-501（前端）、TC-UNIT-502（前端） | integration |
| US-141 | TC-UNIT-502/503/504（前端）、`test_admin_theme_preference_api.py` | integration / unit |
| US-142 | admin_theme.spec.js::口径 1~9 | integration |
| US-144 | TC-UNIT-101（前端）、TC-INT-101（前端） | integration |

## 人工验证清单（摘要，详见 e2e_test_report）

| 编号 | 对应 AC | 步骤 | 期望结果 | 环境 | critical path |
|---|---|---|---|---|---|
| M-01 | AC-142-01/04 | 15 页 × 3 风格逐页打开 | 背景/顶栏/主按钮/导航高亮/表格/弹窗/标签/卡片取色一致 | Web 浏览器 | 是（视觉部分） |
| M-02 | AC-142-02/03 | B 风格管理端顶栏 | 渐变色（与用户端首页同色系）、白胶囊高亮、主按钮强调色；用户端 B 仍白底黑胶囊 | Web 浏览器 | 是 |
| M-03 | AC-142-05/06 | 44px、对比度、减少动态效果 | 点击区域 ≥44px；无不可读文字；装饰动效 0 | Web 浏览器 | 是 |
| M-04 | AC-139-01、OQ-11 | 窄屏打开顶栏下拉 | 选项清晰、触控 ≥44px；高亮形态（白胶囊 vs 强调色填充）请用户确认 | 窄屏浏览器 | 否 |
