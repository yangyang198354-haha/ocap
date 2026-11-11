<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T23:19:22.4786396+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_admin_polish/development/implementation_plan.md</file>
    <file>project_workspace/ocap_admin_polish/architecture/module_design.md</file>
    <file>project_workspace/ocap_admin_polish/architecture/architecture_design.md</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：管理端打磨（INCREMENTAL）

## 摘要

- 改动：产品代码 18 个文件（新增 8、修改 10），测试代码 15 个文件（新增 7、修改 8），文档 2 个。
- 五维平均分：9.3 / 10。
- 问题统计：CRITICAL 0（已修复 0）/ MAJOR 0 / MINOR 5。
- 结论：MOD-064 ~ MOD-073 全部实现，需求追溯表无 MISSING/PARTIAL；自验证全部通过。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `backend/apps/registry/models.py` | MOD-064 / IFC-243 |
| `backend/apps/registry/views.py` | MOD-064（单条新增判重） |
| `backend/apps/registry/migrations/0005_regenerate_specific_part.py` | MOD-065 / IFC-244 |
| `backend/apps/registry/management/commands/registry_specific_part_preview.py` | MOD-066 / IFC-245 |
| `backend/apps/registry/import_spec.py`、`import_template.py` | MOD-067 / IFC-247 |
| `backend/apps/accounts/models.py`、`services.py`、`views.py`、`urls.py`、`migrations/0003_adminaccount_theme_key.py` | MOD-068 / IFC-248~250 |
| `frontend/src/theme/core.js`、`adminStore.js`、`store.js`、`apply.js`、`shared/api.js` | MOD-069 / IFC-251~253、IFC-259 |
| `frontend/index.html`、`src/router/index.js`、`admin/AdminLogin.vue`、`admin/AdminLayout.vue`、`theme/AdminThemeSwitcher.vue` | MOD-070 / IFC-254~257 |
| `frontend/src/shared/style.css`、`themes/bento.web.css`、`themes/bento.theme.json`、生成物 | MOD-071 / IFC-258 |
| `frontend/src/admin/RegistryImportDialog.vue` | MOD-072 |
| `backend/tests/**`、`frontend/tests/**` | MOD-073 |

## 自验证结果

| 命令 | 输出尾部 | 结论 |
|---|---|---|
| `python -m compileall -q backend` | `COMPILE_OK` | 通过 |
| `python manage.py test tests.unit.test_specific_part_rule tests.integration.test_specific_part_regeneration tests.integration.test_specific_part_consistency tests.integration.test_admin_theme_preference_api tests.integration.test_registry_specific_part_preview --settings=config.test_settings` | `Ran 28 tests ... OK` | 通过 |
| `python manage.py test --settings=config.test_settings` | `Ran 558 tests in 12.411s / OK (skipped=9)` | 通过（基线 530，新增 28） |
| `npm run test -- --run`（frontend） | `Test Files 19 passed / Tests 181 passed` | 通过（基线 154 passed + 2 环境失败；本次同时修复 Windows 临时目录用例） |
| `npm run build`（frontend） | `✓ built in 7.62s` | 通过 |
| `node scripts/themes/build.mjs`、`--check` | `wrote ...` / 无错误输出，退出码 0 | 通过 |
| `npm test -- --run`（miniprogram） | `Test Files 11 passed / Tests 75 passed` | 通过（零改动、零新增失败） |

环境说明：本机 Python 3.14.6 / Django 6.0.6（画像 P4 已知差异，未安装或降级依赖）；迁移未在本机执行（画像 P6 手写迁移，测试环境 `MIGRATION_MODULES` 置空，迁移函数由测试直接调用验证）。

## 按模块评审

### MOD-064 专有部分规则与单条判重

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 10/10 | 9/10 | 10/10 |

- 规则 5 条分支与 ADR-064 一致；单条新增改经同一函数判重，409 `UNIT_EXISTS` 在库层 `IntegrityError` 之前拦截。
- 已带后缀优先于纯数字判断，避免"1层层"；楼层省略仅取决于"户号以楼层值+层开头"。
- 字符串运算无额外查询；正则预编译。
- MINOR：规则常量与迁移冻结副本是有意重复（ADR-066），维护时须同时注意两处，由金标测试分别守护。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-301 | MINOR | `registry/migrations/0005_regenerate_specific_part.py:_regenerate` | 核对清单全量写 stdout，数据量极大时日志较长；当前规模 5742 条可接受 | OPEN |

### MOD-065 存量重新生成迁移

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 8/10 | 9/10 |

- 冲突先检测后写入；两阶段占位更新在单事务内；`casefold` 检测 + 库层 `IntegrityError` 兜底；幂等与反向恢复均有测试。
- 只写 `specific_part`，不刷新 `updated_at`，字段与子表条数不变。
- 5742 条合成数据测试耗时 < 60 秒。
- MINOR：迁移内规则为冻结副本，注释已写明禁止随运行时修改。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-302 | MINOR | `0005_regenerate_specific_part.py:_write_lines` | 冲突/清单输出未做条数上限，极端数据下 stderr 很大 | OPEN |

### MOD-066 核对预览命令

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 9/10 | 9/10 | 9/10 |

- 只读；输出不含姓名与手机号；`--limit` 校验；`floor_omitted` 用"含楼层/不含楼层结果是否相同"判定，不依赖私有函数。
- MINOR：`conflicts` 只输出 id 列表，未输出每个字段原值（迁移 stderr 有完整字段）；预检只读场景足够。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-303 | MINOR | `registry_specific_part_preview.py:handle` | 冲突明细仅含 casefold 值与 id，人工定位需再查库 | OPEN |

### MOD-067 / MOD-072 导入说明、模板与对话框

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 10/10 | 9/10 | 10/10 |

- 示例与文案单一来源；模板 6 行示例覆盖多业主、空手机号、车位、负楼层、商铺；前端删除旧硬编码示例。
- `notes` 与 `suffix_rules` 并存时前端过滤重复；未改 `api.js` 导入调用契约。
- 模板文本列设置保持不变（前导零/3.0 不改写）。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-304 | MINOR | `import_spec.py:spec_payload` | `notes` 同时包含 `suffix_rules` 文案，前端需过滤；若第三方客户端直接渲染 notes 会重复展示 | OPEN |

### MOD-068 管理员风格偏好（后端）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 9/10 | 10/10 |

- `/admin/me/theme` 仅 `IsAdmin`；普通用户令牌 403，管理员令牌访问 `/me/theme` 仍 403；偏好物理隔离。
- 只校验格式、不校验启用集合；可空列、手写迁移、可逆。
- 与用户端 `set_theme` 有 3 行差异，属可接受的小重复。

### MOD-069 / MOD-070 前端风格核心、管理端 store 与接线

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 9/10 | 8/10 | 10/10 |

- 用户端 store 行为保持不变（除删除 `forAdminRoute`）；管理端独立设备键与账号接口。
- 首屏脚本按路径选键并设置 `data-surface`；登录成功先对账再跳转；登出保留设备记忆。
- 顶栏入口由注册表驱动，新增风格自动出现；未知风格拒绝且不发请求。
- MINOR：对账失败时每次进入管理端路由都会重试一次；这是 ADR-073 的预期行为，但会产生周期性请求。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-305 | MINOR | `frontend/src/router/index.js:afterEach` | `reconcile()` 失败后 `reconciled` 保持 false，后续每次管理端导航都会重试 | OPEN |

### MOD-071 管理端主题化样式

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 9/10 | 9/10 | 8/10 | 9/10 |

- 所有新增规则双重限定 `html[data-theme="bento"][data-surface="admin"]` + `.admin-bar`/`.el-button--primary`；用户端 `bento.web.css:10-12` 未改。
- 悬停规则在高亮规则之前；高亮块无 `#11121A`/`#fff`；叠加层只用 `rgba(17,18,26,…)`。
- 顶栏渐变使用 `--hero`/`--on-hero`，未新增 token、未改构建脚本；三个停点均有对比度项，插值采样 ≥4.5。
- 登录页/布局的内联颜色清理完成；15 页页面本体未改（守护测试证明合规）。
- MINOR：渐变右端白字余量仅 0.1（4.60 对 4.5），已在 ADR-075/OQ-12 登记。

### MOD-073 测试同步与新增守护测试

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 8/10 | 9/10 | 10/10 |

- 新增 5 个后端测试文件、2 个前端测试文件，并同步 8 个既有测试文件。
- 修复 Windows 下 `theme.spec.js` 使用 `/tmp` 的环境问题（改用 `os.tmpdir()`），此前为既有失败。
- 5742 条迁移测试在 SQLite 内存库约 1 秒，可接受。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 缺陷修复

不适用（本轮为首次实现，无缺陷回流）。

## 现有测试调整

| 文件 | 调整 | 原因 |
|---|---|---|
| `backend/tests/unit/test_registry_import_rules.py` | 旧标识金标 → 新规则；CSV 模板示例数 4→6、空手机号 2→4 | REQ-FUNC-123/124、REQ-FUNC-129 |
| `backend/tests/unit/test_registry_import_smoke.py` | `1-1-3-301` → `1栋1单元3层301号` | 同上 |
| `backend/tests/unit/test_domain_rules.py` | 删除手写 `specific_part` 占位（模型 save 会覆盖） | 防止与规则冲突 |
| `backend/tests/e2e/test_registry_import_journeys.py` | `车库-A-101` → `车库A-101` | 同上 |
| `backend/tests/e2e/test_registry_import_scale_journeys.py` | `1栋-08-8-0801` → `1栋08单元8层0801号` | 同上 |
| `backend/tests/integration/test_registry_import_enhancement.py` | `车库-A-*`、`1-2-3-301` → 新格式；模板示例数 4→6、空手机号 2→4 | 同上 |
| `backend/tests/integration/test_registry_import_query_bounds.py` | 手写 `B-1-1-{i}` → `build_specific_part(...).casefold()` | 保证 key 与存储值一致 |
| `backend/tests/integration/test_registry_import_xlsx_defects.py` | `1-08-8-0801` → `1栋08单元8层0801号` | 同上 |
| `backend/tests/support.py` | `next_specific_part` 改为新格式（当前无调用方） | MOD-073 清单 |
| `frontend/tests/theme.spec.js` | 删除 `forAdminRoute` 断言；临时目录改用 `os.tmpdir()` | REQ-FUNC-135；修复 Windows 环境失败 |
| `frontend/tests/qa_unit_theme.spec.js` | 首屏脚本分键 + `data-surface`；管理端入口断言改为 `AdminThemeSwitcher` | AC-141-02/05、AC-143-02 |
| `frontend/tests/qa_int_theme.spec.js` | 管理端独立记忆与账号偏好对账 | AC-144-01/02 |
| `frontend/tests/qa_e2e_theme.spec.js` | 旅程第 8 步改为管理端独立偏好 | AC-143-01/02 |
| `frontend/tests/qa_e2e_pages.spec.js` | 管理端页面断言有顶栏入口；登录页无入口 | AC-139-01/05 |
