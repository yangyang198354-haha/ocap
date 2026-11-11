<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T23:01:26.2548515+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md</file>
    <file>requirements/user_stories.md</file>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>architecture/tech_stack.md</file>
    <file>phase_status.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：管理端打磨（专有部分显示格式 + 管理端多风格）

## 实现概览

- 模块 10 个（MOD-064 ~ MOD-073），改动文件 30 个（后端 13、前端 12、主题/生成物 3、文档 2）。
- 实现顺序按 module_design「依赖关系」拓扑排序：MOD-064 →（MOD-066、MOD-067 → MOD-072）→ MOD-065；MOD-068 → MOD-069 → MOD-070（同时依赖 MOD-071）；MOD-073 最后补齐守护测试与既有用例同步。
- 工作区已有上一增量未提交改动（accounts 用户目录、registry/importing.py 的 WRITE_BATCH、registry/services.py 楼层排序及其测试），本计划不触碰这些文件（AdminUsers.vue 亦未改动）。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-064 | `backend/apps/registry/models.py` | 修改 | — | M | 原位替换 `build_specific_part`：strip、空段跳过、已带后缀原样、ASCII 纯数字/负+数字补后缀、楼层省略规则、直接连接 | DONE |
| 2 | MOD-064 | `backend/apps/registry/views.py` | 修改 | 1 | S | 单条新增预检查改经 `build_specific_part` 判重（409 UNIT_EXISTS） | DONE |
| 3 | MOD-065 | `backend/apps/registry/migrations/0005_regenerate_specific_part.py` | 新建 | — | H | 冻结新旧规则、`plan_regeneration`、冲突检测（casefold）、两阶段占位更新、单事务、可逆、核对清单输出 | DONE |
| 4 | MOD-066 | `backend/apps/registry/management/__init__.py`、`management/commands/__init__.py`、`management/commands/registry_specific_part_preview.py` | 新建 | 1 | M | 只读预览命令 `registry_specific_part_preview [--limit N]` | DONE |
| 5 | MOD-067 | `backend/apps/registry/import_spec.py` | 修改 | 1 | M | `EXAMPLE_ROWS`、`example_identifiers()`、`SUFFIX_RULES`；列说明追加后缀规则；`spec_payload()` 增 `suffix_rules`/`examples` | DONE |
| 6 | MOD-067 | `backend/apps/registry/import_template.py` | 修改 | 5 | S | 示例行改读 `import_spec.EXAMPLE_ROWS`（6 行），说明追加后缀规则 | DONE |
| 7 | MOD-068 | `backend/apps/accounts/models.py`、`accounts/services.py`、`accounts/views.py`、`accounts/urls.py` | 修改 | — | S | `AdminAccount.theme_key`；`set_admin_theme`；`AdminThemePreferenceView`（GET/PUT `/admin/me/theme`，IsAdmin）；路由 | DONE |
| 8 | MOD-068 | `backend/apps/accounts/migrations/0003_adminaccount_theme_key.py` | 新建 | 7 | S | 手写 `AddField`（可空、可逆） | DONE |
| 9 | MOD-069 | `frontend/src/theme/core.js`、`frontend/src/theme/adminStore.js` | 新建 | 7 | M | 共享工具（KEY_RE、注册表查找、设备键读写）；管理端 store（initFromDevice/enter/reconcile/select/resetSession） | DONE |
| 10 | MOD-069 | `frontend/src/theme/store.js`、`frontend/src/theme/apply.js`、`frontend/src/shared/api.js` | 修改 | 9 | S | 用户端 store 改用 core、删除 `forAdminRoute`；`applyTheme` 增 surface；`admin.theme/setTheme` | DONE |
| 11 | MOD-071 | `frontend/src/shared/style.css`、`themes/bento.web.css`、`themes/bento.theme.json`、生成物 `frontend/src/theme/generated/themes.css` | 修改 | — | H | `.admin-bar` 与 `.topbar` 共享骨架、窄屏不隐藏管理导航、`.admin-login`、`.admin-theme-trigger`；管理端作用域覆盖（渐变顶栏/深色胶囊容器/白胶囊高亮/强调色主按钮/焦点环）；对比度项 | DONE |
| 12 | MOD-070 | `frontend/index.html`、`frontend/src/router/index.js`、`frontend/src/admin/AdminLogin.vue`、`frontend/src/admin/AdminLayout.vue`、`frontend/src/theme/AdminThemeSwitcher.vue` | 修改/新建 | 9,11 | M | 首屏脚本分键与 data-surface；路由 afterEach；登录对账与登出重置；数据驱动导航 + 切换入口 | DONE |
| 13 | MOD-072 | `frontend/src/admin/RegistryImportDialog.vue` | 修改 | 5 | S | 说明区渲染 `suffix_rules` 与 `examples`，删除硬编码示例 | DONE |
| 14 | MOD-073 | `backend/tests/unit/test_specific_part_rule.py` 等 5 个后端测试文件、`frontend/tests/admin_theme.spec.js`、`frontend/tests/admin_theme_store.spec.js`、`frontend/tests/api.spec.js` | 新建/修改 | 全部 | H | 新规则金标、迁移、预览命令、一致性、管理员偏好接口；主题守护与 store 用例；契约用例 | DONE |
| 15 | MOD-073 | MOD-073 清单列出的既有测试同步更新 | 修改 | 全部 | M | 旧标识断言与新行为断言（管理端不再固定 B） | DONE |

## 需求追溯

| US | AC | 实现位置（文件:函数/组件） | 状态 | 说明 |
|---|---|---|---|---|
| US-132 | AC-132-01 ~ 132-04 | `backend/apps/registry/models.py:build_specific_part`；`/admin/registry/units` 序列化输出 | DONE | 规则单点；AC-132-05 沿用 `validate_unit_fields` |
| US-132 | AC-132-05 | `backend/apps/registry/import_spec.py:validate_unit_fields`（未改） | DONE | 必填校验不变 |
| US-133 | AC-133-01 ~ 133-09 | 同上 + `backend/tests/unit/test_specific_part_rule.py` 金标 | DONE | 含负楼层、3.0、-1/B1、空段、楼层省略 |
| US-134 | AC-134-01/02/03/04 | `registry/migrations/0005_regenerate_specific_part.py:plan_regeneration/regenerate_specific_parts` | DONE | 冲突整批不生效、幂等、字段原值不变、可逆 |
| US-134 | AC-134-05 | 迁移 stdout 与 `registry_specific_part_preview` 的 review 明细 | DONE | 只读清单 |
| US-134 | AC-134-06 | 迁移批量更新 batch_size=200；预览命令 | DONE | 规模性能由测试覆盖 |
| US-135 | AC-135-01 ~ 135-05 | 存储列即新格式：`registry/views.py` 搜索、`identity`、`residency`、导入 changes 均读 `specific_part` | DONE | 代码零改动（IFC-260） |
| US-135 | AC-135-06 | 既有权限代码未改 | DONE | 回归覆盖 |
| US-136 | AC-136-01 ~ 136-04 | `registry/views.py:AdminUnitListView.post/AdminUnitDetailView.patch` + 模型 save | DONE | 判重经同一函数 |
| US-137 | AC-137-01 ~ 137-07 | `registry/importing.py` 调用 `build_specific_part`（未改调用方式） | DONE | 分组/匹配随规则变化 |
| US-138 | AC-138-01 ~ 138-04 | `registry/import_spec.py`、`registry/import_template.py`、`frontend/src/admin/RegistryImportDialog.vue` | DONE | 单一来源；模板文本列不变 |
| US-139 | AC-139-01 ~ 139-05 | `frontend/src/theme/AdminThemeSwitcher.vue`、`AdminLayout.vue`、`router/index.js` | DONE | 入口在顶栏；登录页无入口 |
| US-140 | AC-140-01 ~ 140-03 | `frontend/src/theme/adminStore.js:initFromDevice/reconcile`、`theme/core.js:resolveKey` | DONE | 默认 B、下线回退、读取失败保持 |
| US-141 | AC-141-01 ~ 141-05 | `adminStore.js`、`index.html` 内联脚本、`AdminLogin.vue`、`AdminLayout.vue:logout` | DONE | 账号偏好权威；分键设备记忆 |
| US-142 | AC-142-01 ~ 142-06 | `themes/bento.web.css` 管理端作用域、`shared/style.css`、`bento.theme.json`、`frontend/tests/admin_theme.spec.js` | DONE | 结构+色彩+对比度守护；视觉走查留 GROUP_D |
| US-143 | AC-143-01 ~ 143-03 | `adminStore.js` 独立状态与 `ocap_admin_theme` 键；`/admin/me/theme` 与 `/me/theme` 分离 | DONE | 互不影响 |
| US-144 | AC-144-01 ~ 144-04 | `router/index.js` 删除强制 B；`store.js` 删除 `forAdminRoute`；既有断言同步 | DONE | 默认 B 保持 |
| NFUNC-19 | — | 迁移只写 `specific_part`，不刷新 `updated_at` | DONE | 测试断言字段与子表条数 |
| NFUNC-20 | — | 全量回归 | DONE | 零新增失败（见 code_review_report） |
| NFUNC-21 | — | 对比度项、44px、无新增动画 | DONE | 构建脚本 + 守护测试 |
| NFUNC-22 | — | 首屏脚本分键、无跳变 | DONE | store 与内联脚本测试 |
| NFUNC-23 | — | batch_size=200、纯字符串规则 | DONE | 规模测试 |

## 迁移

- `backend/apps/registry/migrations/0005_regenerate_specific_part.py`：手写数据迁移，冻结新旧规则；冲突检测 + 两阶段占位更新 + 单事务；`RunPython` forward/reverse；可逆。依赖 `registry.0004_phone_owner_required`。
- `backend/apps/accounts/migrations/0003_adminaccount_theme_key.py`：手写 `AddField`（`theme_key` 可空），依赖 `accounts.0002_user_theme_key`；可逆（`RemoveField`）。

## 架构偏差

无。

## 开放问题

- `[ASSUMPTION]` 楼层省略规则按 ADR-064 第 4 点：`stem = floor.strip()` 去掉末尾"层"，`stem` 非空且 `room` 以 `stem + "层"` 开头才省略；"1层楼"也视为开头匹配（OQ-03 已登记）。
- `[ASSUMPTION]` 迁移占位前缀 `~regen~` 在库中不存在时直接使用；若存在则以 `RuntimeError` 中止（不写数据）。
- `[ASSUMPTION]` 管理端风格 store 的 `reconcile()` 在账号值不在注册表时不写库（仅本地回退 B），与 ADR-073 的后端"只校验格式"一致。

## 因本变更同步更新的既有用例

| 文件 | 原断言 | 更新为 | 原因 |
|---|---|---|---|
| `backend/tests/unit/test_registry_import_rules.py` | `build_specific_part("1","2","3","301") == "1-2-3-301"` 等 3 条 | 新规则金标 | REQ-FUNC-123/124 |
| `backend/tests/unit/test_registry_import_smoke.py` | `"1-1-3-301"` | `"1栋1单元3层301号"` | 同上 |
| `backend/tests/unit/test_domain_rules.py` | 手写 `specific_part=f"1-1-101-…"` | 经 `build_specific_part` 生成 | 保证存储列由规则写入 |
| `backend/tests/e2e/test_registry_import_journeys.py` | `"车库-A-101"` | `"车库A-101"` | 同上 |
| `backend/tests/e2e/test_registry_import_scale_journeys.py` | `"1栋-08-8-0801"` | `"1栋08单元8层0801号"` | 同上 |
| `backend/tests/integration/test_gap_must_have.py` | 旧标识间接断言 | 保持（读取同一 `unit.specific_part`） | 无需改值 |
| `backend/tests/integration/test_registry_import_enhancement.py` | 多处 `"车库-A-088"`、`"1-2-3-301"`、`"车库-A-090"` | 新格式 | 同上 |
| `backend/tests/integration/test_registry_import_query_bounds.py` | 手写 `B-1-1-{i}` | 经 `build_specific_part` 生成唯一键 | 同上 |
| `backend/tests/integration/test_registry_import_xlsx_defects.py` | `"1-08-8-0801"` | `"1栋08单元8层0801号"` | 同上 |
| `backend/tests/support.py` | `next_specific_part` 旧格式 | 新格式前缀（当前无调用方） | MOD-073 清单 |
| `backend/tests/unit/test_registry_import_rules.py`、`backend/tests/integration/test_registry_import_enhancement.py` | CSV 模板示例数 4 → 6、空手机号 2 → 4 | 新示例覆盖负楼层/商铺 | REQ-FUNC-129 |
| `frontend/tests/theme.spec.js` | 临时目录 `process.env.TMPDIR || '/tmp'` | `os.tmpdir()` | 修复 Windows 既有失败，保证全量回归通过 |
| `frontend/tests/theme.spec.js` | `forAdminRoute()` 固定 B | 管理端 store 分键/默认 B | REQ-FUNC-135 |
| `frontend/tests/qa_unit_theme.spec.js` | 管理端恒 bento、无风格入口 | 管理端读 `ocap_admin_theme`、有入口 | 同上 |
| `frontend/tests/qa_int_theme.spec.js` | 管理端固定 bento | 管理端独立记忆 | 同上 |
| `frontend/tests/qa_e2e_theme.spec.js` | 管理端固定 B | 管理端独立记忆 | 同上 |
| `frontend/tests/qa_e2e_pages.spec.js` | 管理端无风格入口 | 管理端有切换入口 | 同上 |
