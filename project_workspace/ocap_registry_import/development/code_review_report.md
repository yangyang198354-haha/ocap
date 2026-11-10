<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T00:21:15+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/module_design.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.2.0 门控版本)</file>
    <file>development/implementation_plan.md (1.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：业主清册导入增强（GROUP_C）

## 摘要

- **1.1.0 缺陷回流（DEF-007~012）**：改动 6 个文件（import_spec/import_template/importing/views/auto_bind/registryImport.js），均为最小改动；新增问题 CR-015~CR-017（MINOR，见下）。后端 327/327 OK；前端 vitest 125/126（1 条既有用例因 DEF-012 同步 revoke 断言失败，见"现有测试调整"）、前端构建成功。以下 1.0.0 摘要保留为历史。

- 改动范围：`git diff --stat` 22 个已跟踪文件（+802 / -271）；另有 10 个新建文件（未跟踪）。合计 32 个代码/测试文件，不含本目录文档。
- 冻结接口：IFC-152 ~ IFC-164；模块 MOD-030 ~ MOD-038 全部 DONE。
- 五维平均分：**8.5 / 10**。
- 问题统计：CRITICAL 2（已修复 2）/ MAJOR 6（已修复 4，遗留 2）/ MINOR 2（已修复 1，遗留 1）。
- 自验证结论：后端 247 个测试全通过，迁移一致性检查无变更，Web 前端构建成功、vitest 120 通过 / 2 个既有主题环境失败；小程序安装依赖后 vitest 69 个全通过。xlsx 解析与模板生成因本机缺 `openpyxl` 未验证 → **PARTIAL_SUCCESS**（详见"自验证结果"与"遗留 MAJOR"）。

## 文件 → MOD/IFC 映射

| 文件 | 新建/修改 | MOD | IFC |
|---|---|---|---|
| `backend/apps/registry/models.py` | 修改 | MOD-030 | IFC-152 |
| `backend/apps/registry/migrations/0002_owner_type_area.py` | 新建 | MOD-030 | IFC-161 |
| `backend/apps/registry/migrations/0003_backfill_legacy_owners.py` | 新建 | MOD-030 | IFC-161 |
| `backend/apps/registry/migrations/0004_phone_owner_required.py` | 新建 | MOD-030 | IFC-161 |
| `backend/apps/registry/serializers.py` | 修改 | MOD-030 | IFC-152 |
| `backend/apps/registry/import_spec.py` | 新建 | MOD-031 | IFC-153/154/156 |
| `backend/apps/registry/importing.py` | 新建 | MOD-031 | IFC-155/156 |
| `backend/apps/registry/import_template.py` | 新建 | MOD-031 | IFC-154 |
| `backend/apps/registry/services.py` | 修改 | MOD-033 | IFC-152/157 |
| `backend/apps/registry/views.py` | 修改 | MOD-032 | IFC-152~159 |
| `backend/apps/registry/urls.py` | 修改 | MOD-032 | IFC-152~159 |
| `backend/apps/residency/auto_bind.py` | 新建 | MOD-034 | IFC-160 |
| `backend/apps/residency/services.py` | 修改 | MOD-034 | IFC-160 |
| `backend/apps/accounts/views.py` | 修改 | MOD-035 | IFC-163 |
| `backend/apps/identity/views.py` | 修改 | MOD-035 | IFC-164 |
| `frontend/src/shared/api.js` | 修改 | MOD-036 | IFC-162 |
| `frontend/src/admin/registryImport.js` | 新建 | MOD-036 | — |
| `frontend/src/admin/RegistryImportDialog.vue` | 新建 | MOD-036 | IFC-162 |
| `frontend/src/admin/AdminRegistry.vue` | 修改 | MOD-036 | IFC-152/157/162 |
| `frontend/src/portal/Units.vue` | 修改 | MOD-037 | IFC-157 |
| `frontend/src/portal/Register.vue` | 修改 | MOD-037 | IFC-163 |
| `frontend/src/portal/Me.vue` | 修改 | MOD-037 | IFC-164 |
| `miniprogram/pages/units/index.vue` | 修改 | MOD-038 | IFC-157 |
| `miniprogram/pages/phone/index.vue` | 修改 | MOD-038 | IFC-164 |
| `miniprogram/utils/api.js` | 修改 | MOD-038 | IFC-157 |
| `backend/tests/support.py` 等 5 个测试文件 | 修改 | 测试适配 | — |
| `backend/tests/unit/test_registry_import_smoke.py` | 新建 | 自验证 | — |

## 自验证结果

| 命令 | 工作目录 | 输出尾部 | 结论 |
|---|---|---|---|
| `python manage.py check --settings=config.test_settings` | `backend` | `System check identified no issues (0 silenced).` | 通过 |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | `backend` | `No changes detected` | 通过（3 个手写迁移与模型一致） |
| `python manage.py test --settings=config.test_settings` | `backend` | `Ran 247 tests in 3.251s` / `OK` | 通过（全量，含既有测试） |
| `npm run build` | `frontend` | `✓ built in 7.36s`（仅 chunk > 500 kB 提示） | 通过 |
| `npx vitest run` | `frontend` | `Test Files 2 failed \| 10 passed (12)`；`Tests 2 failed \| 120 passed (122)` | 2 个失败均为既有主题模块问题：`tests/theme_build.spec.js:18` 生成 CSS 与仓库文件行尾差异；`tests/theme.spec.js` 报 `ENOENT lstat 'C:\tmp'`（Windows 路径）。`git status` 无 themes 相关改动 |
| `npm install --no-audit --no-fund --legacy-peer-deps`（与 `.github/workflows/ci.yml:99` 一致） | `miniprogram` | 退出码 0 | 通过（仅 postinstall 脚本提示） |
| `npx vitest run` | `miniprogram` | `Test Files 10 passed (10)`；`Tests 69 passed (69)` | 通过 |
| `python -c "import openpyxl"` | `backend` | `ModuleNotFoundError: No module named 'openpyxl'` | xlsx 解析与模板生成路径**未验证**；CSV 全链路已验证 |

冒烟覆盖（`tests/unit/test_registry_import_smoke.py`）：预检与正式导入数字一致、重复导入幂等、行级错误不影响合法行。

## 按模块评审

### MOD-030 模型、迁移、序列化器

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 8/10 |

- `build_specific_part` 只拼接非空段，`1-2-3-301` 与 `车库-A-088` 由同一函数生成，导入/单条/选择三处一致（AC-098-01/05）。
- 迁移 0003 按手机号回填无名业主且可逆；0004 先校验孤儿手机号再收紧非空，避免静默丢数据。
- 序列化器输出完整手机号仅限管理员端点；用户端仍走既有脱敏，无横向越权。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

### MOD-031 导入规格、引擎、模板

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 9/10 |

- 三段式 `read_rows → plan_import → apply_plan`：dry_run 只跑前两段，与正式导入共用计划，AC-100-01/03 由结构保证。
- 行级原子：任何行错误不写入该行；整文件错误（列缺失、超限、不可解析）走 400/503。
- `Deadline` 在解析每 500 行、计划、应用各阶段检查，超时 504 `IMPORT_TIMEOUT`。
- 手机号占用、姓名冲突、类型/面积冲突均在建计划阶段拒绝，不产生部分写入。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | CRITICAL | `importing.py` `_create_phones` | 新业主的手机号只存在 `PlannedOwner.phones`，从未落库，导致 AC-094-01"4 位有手机号业主可认证"不成立 | FIXED（合并 `plan.phones_to_create` 与业主自带手机号并去重） |
| CR-002 | CRITICAL | `importing.py` `_move_phones` / `_plan_row` | 手机号改属目标为本次新建业主时 `to_owner_ref` 无法解析而被跳过，手机号丢失（AC-099-02） | FIXED（支持 `("new", unit_key, name)` 引用，并调整 `apply_plan` 顺序为先建业主/手机号→再移动→最后删空业主） |
| CR-003 | MAJOR | `importing.py` `_plan_row` | 同一单元同一新业主出现在多行时重复创建业主 | FIXED（`state.owners` 复用 + `new_planned` 累积手机号） |
| CR-004 | MAJOR | `importing.py` `summary()` | `updated` 只统计类型/面积变化，新增业主的既有专有部分未计入（AC-099-01） | FIXED（`ImportPlan.touched` 计数，新建单元不计入） |
| CR-005 | MAJOR | `importing.py` `_create_owners` | 既有单元每行回查 DB 得到 `unit_key`（N+1） | FIXED（由 `owners_to_create[].unit_id` + `new_unit_ids` 构建映射） |
| CR-006 | MAJOR | `import_template.py` `EXAMPLE_ROWS` | 模板示例仅 1 行，不满足 AC-093-01"同单元 3 行 + 空手机号 + 车位" | FIXED（扩为 4 行） |
| CR-007 | MINOR | `importing.py` `_load_states` | 20000 行文件按全部 `specific_part` 一次性 `__in` 查询，SQLite 旧版本变量上限可能不足 | OPEN（测试环境为 MySQL；记录为开放问题，后续可分批） |

### MOD-032 管理端 API 与路由

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 8/10 |

- 7 条路由全部带管理员权限；`UnitOptionsView` 为 `IsMember`（用户端选择）。
- 业主全量替换先校验后写（先改名置 NULL 规避唯一约束，再重建手机号），失败不产生半更新（AC-095-03/07）。
- 导入端点校验扩展名与 5 MB 上限，`dry_run` 与正式共用计划；审计记录只写计数，不含姓名与手机号明文（AC-094-06）。
- 错误码与 module_design 一致：`IMPORT_FILE_INVALID`/`IMPORT_COLUMNS_MISSING`/`IMPORT_TIMEOUT`/`IMPORT_CONFLICT`/`IMPORT_UNAVAILABLE`。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

### MOD-033 查询服务

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

- `options` 按楼栋→单元→楼层逐级返回，`skipped` 标记跳过的层级，`has_empty` 表示存在空层级记录；房号选项带 `label = 户号（类型 面积）`（AC-098-02/03、AC-097-04）。
- `units_by_phone` 使用 `distinct().order_by("id")`，避免多手机号重复单元。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-008 | MAJOR | `services.py` `options` | 原实现过滤空串后不返回 `has_empty`，前端无法到达"无单元/楼层"的车位（AC-098-02/03） | FIXED（后端返回 `has_empty`，Web 与小程序在空层插入"未划分单元/楼层"选项） |

### MOD-034 自动绑定服务

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 8/10 |

- `bind_by_phone` 逐单元调用 `certify_owner(..., origin="REGISTRY_AUTO")`，`ALREADY_CERTIFIED` 跳过，其他 `ApiError` 与意外异常只记日志并中断，不阻断注册/绑定主流程。
- 审计 detail 在 `REGISTRY_AUTO` 时附 `origin` 与 `origin_label: 清册自动绑定`，可追溯到触发来源。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

### MOD-035 注册与手机号绑定触发点

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 9/10 | 9/10 | 9/10 | 8/10 |

- 注册成功与首次绑定手机号成功后返回 `auto_bound`；账号合并场景返回空列表（合并后身份由既有账号承担，避免误绑）。
- 自动绑定失败不影响注册/绑定成功响应（Q-RI-18=B 只要求"注册且认证成功"时绑定）。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

### MOD-036 Web 管理端

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 8/10 | 8/10 | 7/10 |

- 导入对话框：格式说明（文件类型/5 MB/20000 行/首工作表/类型取值）、列规则表、7 条说明与示例、模板下载（xlsx/csv）、预检→确认→结果、错误清单表格与 CSV 下载、"正在处理，请稍候…（最长 60 秒）"。
- 导入请求单独 100 s 超时（ADR-040），超时文案明确；结果以文字与表格呈现，不展示 JSON 原文（AC-100-05）。
- 编辑对话框仅在用户填写时提交类型/面积，允许只改其一的既有记录（AC-101-04）。
- 未新增前端单测（现有 vitest 覆盖主题与通用模块）；交互逻辑通过构建 + 手工路径核对，测试覆盖交由 GROUP_D。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-009 | MAJOR | `AdminRegistry.vue` `saveEdit` | 编辑时强制要求类型，导致兼容既有记录时无法只改面积（AC-101-04） | FIXED（空值不发送对应字段） |
| CR-010 | MINOR | `registryImport.js` | 导入超时 100000 ms 为常量，未与后端 `time_budget_seconds` 联动 | OPEN（后端默认 60 s，前端留 40 s 余量；若配置调大需同步） |

### MOD-037 Web 用户端

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 8/10 | 8/10 | 7/10 |

- `Units.vue` 按 `level/skipped/has_empty` 递归加载，跳级时自动请求下一层；`room` 层展示"户号（类型 面积）"与申诉提示；选择后调用认证，`PHONE_NOT_IN_REGISTRY` 引导产权申诉。
- `Register.vue` / `Me.vue` 在 `auto_bound` 非空时提示"已根据你的手机号自动认证为 … 的产权业主"。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

### MOD-038 小程序

**五维评分表**

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 8/10 | 8/10 | 8/10 |

- `pages/units` 与 Web 端同构：跳级、`has_empty` 插入"未划分"、末级 label、`PHONE_NOT_IN_REGISTRY` 提示；`pages/phone` 展示自动绑定结果。
- 依赖安装后既有 10 个测试文件 69 个用例全部通过，无新增失败；本次新增的跳级/选择逻辑尚无专门用例，交由 GROUP_D 补充。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| — | — | — | 本模块未发现问题 | — |

## 未解决的 CRITICAL

无。CR-001、CR-002 已在实现阶段修复并复跑通过。

## 遗留 MAJOR

| 编号 | 描述 | 遗留原因 | 建议处理时机 |
|---|---|---|---|
| M-1 | xlsx 解析（`read_rows`）与 xlsx 模板生成（`build_xlsx`）未验证 | 本机 Python 环境未安装 `openpyxl`（已在 `backend/requirements.txt` 声明），按协议不自行安装；代码在缺依赖时返回 503 `IMPORT_UNAVAILABLE`，不会 500 | GROUP_D 或 E2 预检：安装依赖后补 xlsx 用例（AC-093-01/03/04、AC-096/098 的 xlsx 路径） |
| M-2 | 性能类 AC 未实测：AC-094-07（20000 行 ≤60 s）、AC-100-07（预检 ≤60 s）、AC-100-08（10% 错误行 ≤60 s 且合计 20000） | 需真实 20000 行样本与画像 P7 测试环境，属测试阶段度量；实现侧已具备常量限制、`Deadline`、前端 100 s 超时与"处理中"状态 | GROUP_D（PHASE_09 性能/E2E）实测，不达标回流 GROUP_C |

以上 2 条均在 `implementation_plan.md` 需求追溯表标为 PARTIAL，未标记为 DONE。小程序测试已在安装依赖后全部通过，原"无 `node_modules` 无法运行"的遗留项已关闭。

## 缺陷修复

1.1.0（REWORK_AUTHORIZED）：

| DEF | 位置 | 根因 | 修改说明 |
|---|---|---|---|
| DEF-007 | `registry/import_template.py:build_xlsx`、`import_spec.py:spec_payload` | 模板单元格 General，Excel 将 0801 存为数字 | A/B/C/D/H 列整列及示例行设文本格式 "@"；说明与 notes 增补 CSV 提示 |
| DEF-008 | `registry/importing.py:read_rows/_fill_merged_cells` | read_only 模式无 merged_cells | 改普通模式读取并展开合并区域；20000 行实测 4.78 s |
| DEF-009 | `residency/auto_bind.py:bind_by_phone` | 失败即 break | 改 continue；每单元 `transaction.atomic()` savepoint |
| DEF-010 | `registry/views.py:AdminRegistryImportView.post` | 表单 dry_run 用 bool() | 与查询参数同样判定 "1"/"true" |
| DEF-011 | `registry/importing.py:_fill_names` | bulk_update 不触发 auto_now | 显式赋 `updated_at=timezone.now()` |
| DEF-012 | `frontend/src/admin/registryImport.js:downloadBlob` | click 后立即 revoke | `setTimeout` 1000 ms 后 revoke |

1.1.0 新增评审（五维：Correctness 8.5 / Security 9 / Performance 8 / Maintainability 9 / Testability 7，均≥6）：

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-015 | MINOR | `importing.py:read_rows` | 普通模式加载整个工作簿，内存高于 read_only；受 5 MB/20000 行上限约束，实测 4.78 s，可接受 | OPEN（已记取舍） |
| CR-016 | MINOR | `frontend/tests/registry_import.spec.js:61` | 既有用例同步断言 revoke，与 DEF-012 延迟释放冲突，须 test-engineer 调整 | OPEN |
| CR-017 | MINOR | `auto_bind.py`、`importing.py` | DEF-007~011 无专门测试覆盖（现有 327 个后端测试均未覆盖这些路径，故全绿并不证明修复） | OPEN（交 test-engineer） |

自验证（1.1.0）：`(cd backend && venv python manage.py test --settings=config.test_settings)` → `Ran 327 tests ... OK`；`python3 -m compileall -q backend` 通过；`(cd frontend && npx vitest run --passWithNoTests)` → `Tests 1 failed | 125 passed (126)`；`npm run build -- --base=/ocap/` → `built in 25.49s`；临时脚本（scratchpad，不入库）验证模板格式、合并单元格读取与 20000 行性能。小程序未改动，未重跑。CRITICAL 0 / MAJOR 0 新增 / MINOR 3 新增（均 OPEN）。CR-001 ~ CR-004、CR-008 ~ CR-009 的修复过程已记入对应模块的 CR 问题表。

## 现有测试调整

| 文件 | 调整 | 原因 |
|---|---|---|
| `backend/tests/support.py` | `make_unit` 支持 `phones`/`name`，先建 `RegistryOwner` 再建 `RegistryPhone`；`unit_no` 改为生成值 | `RegistryPhone.owner` 收紧为非空（0004），旧夹具直接建手机号会违反约束 |
| `backend/tests/smoke/test_flows_smoke.py` | 同样改为内建业主再建手机号 | 同上 |
| `backend/tests/integration/test_gap_must_have.py` | 移除"清册登记手机号"用例中的登记（保留游客语义）；`test_reregister_owner_must_certify_again` 改为 `test_reregister_owner_auto_bound_by_registry`；`/phones` PUT 改为 `/owners` | US-102 自动绑定改变了"注册后仍是游客"的前提；接口契约由 IFC-158 全量替换业主 |
| `backend/tests/integration/test_residency_api.py` | CSV 改为 8 列；dry_run 的 `imported` 由 0 改为 2；`/phones` 改 `/owners` | 新模板/新列契约与预检计数口径（dry_run 也返回将新增数） |
| `backend/tests/e2e/test_gap_journeys.py` | TC-E2E-014 改为断言注册即自动绑定（`auto_bound == [unit.id]`、身份含"户主"），删除手动 `/certifications`；`/phones` 改 `/owners` | US-102：手机号命中清册的注册用户无需手动认证 |

以上调整均为契约或语义变更的必要适配，未削弱既有断言强度；全量 247 个测试通过，无新增失败。

### 1.1.0 补充
`frontend/tests/registry_import.spec.js` TC-UNIT-114：未改（约束禁止），失败原因与建议修法见 implementation_plan 1.1.0"缺陷修复"节。
