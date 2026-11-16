<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-16T18:32:47+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>development/implementation_plan.md</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告：房屋选择结构整理、申诉审核增强、认证姓名核对与席位授予放宽

## 摘要

- 改动范围（`git diff --stat`，本批文件）：产品代码已有文件修改 20 个（`318 insertions(+), 103 deletions(-)`，含后端 12、Web 前端 5、小程序 3）；既有测试最小同步 21 个（`154 insertions(+), 103 deletions(-)`）；新建 6 个（`registry/shops.py`、`registry/ownership.py`、`registry/management/commands/relocate_shops.py`、`committee/effective.py`、`residency/migrations/0003_appeal_owner_name.py`、`frontend/src/admin/parts/ProofThumbs.vue`）。`git diff --stat` 总数 45 个文件中另有 4 个**不是本批改动**（`.claude/agent-memory/system-architect/MEMORY.md`、`project_workspace/_kb_inbox.jsonl`、`project_workspace/ocap_product_review/{deployment/deployment_report.md,phase_status.md}`，开工前已处于已修改状态），未触碰。
- 五维平均分：Correctness 8.6、Security 8.6、Performance 8.5、Maintainability 8.4、Testability 8.0；总平均 **8.4**（各模块 5 维分数之和 337 ÷ 40 项 = 8.425）。
- 问题统计：**CRITICAL 0（已修复 0）/ MAJOR 2（OPEN 2）/ MINOR 6（FIXED 2、OPEN 4）**。

## 文件 → MOD/IFC 映射

| 文件 | MOD | IFC |
|---|---|---|
| `backend/apps/registry/ordering.py`、`registry/services.py` | MOD-112 | IFC-299、IFC-300 |
| `backend/apps/registry/shops.py`、`registry/management/commands/relocate_shops.py`、`registry/underground.py`（`format_name`） | MOD-111 | IFC-301、IFC-302 |
| `backend/apps/registry/exporting.py`、`registry/management/commands/export_registry_import_file.py` | MOD-113 | IFC-303 |
| `backend/apps/registry/ownership.py` | MOD-114 | IFC-304、IFC-305 |
| `backend/apps/residency/{models.py,views.py,apps.py}`、`residency/migrations/0003_appeal_owner_name.py` | MOD-115 | IFC-306~310 |
| `backend/apps/committee/{effective.py,services.py,views.py}`、`accounts/{directory.py,views.py}` | MOD-116 | IFC-311、IFC-312 |
| `frontend/src/{shared/api.js,portal/Units.vue,portal/parts/UnitCascader.vue,admin/AdminAppeals.vue,admin/AdminSeats.vue,admin/parts/ProofThumbs.vue}` | MOD-117 | IFC-313、IFC-315 |
| `miniprogram/{utils/api.js,components/UnitPicker.vue,pages/units/index.vue}` | MOD-118 | IFC-314 |

## 自验证结果

环境：Python 3.12 + Django 5.2.19 venv（只用，不装包）；工作目录仓库根，后端命令 `(cd backend && …)`；仅本地 SQLite，未连接测试机，未 ssh、未 commit、未 push。

| 命令 | 结果（输出尾部） |
|---|---|
| `python -m compileall -q backend` | 无输出，退出 0（`COMPILE_OK`） |
| `python manage.py check --settings=config.test_settings` | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | `No changes detected`（该设置置空 `MIGRATION_MODULES`，对迁移无判别力，仅作 P4 命令留痕） |
| scratch 设置（`MIGRATION_MODULES = {}`、临时 SQLite 文件）`makemigrations --check --dry-run` | residency/appeal/owner_name 无漂移；输出的 8 条 `Alter field id` 属仓库既有、与本批无关（未触碰） |
| scratch `migrate` → `migrate residency 0002` → `migrate residency` | `Applying residency.0003_appeal_owner_name... OK` → `Unapplying residency.0003_appeal_owner_name... OK` → `Applying … OK`（可逆已验证） |
| `python manage.py test --settings=config.test_settings`（后端全量） | `Ran 822 tests in 76.795s` / `FAILED (failures=1)`：唯一失败为 `tests.integration.test_registry_export_cmd.ExportSuccessTests.test_tc_int_611_no_file_written_into_repo_root_and_no_part_left`，原因是开发机仓库根存在 git 忽略的历史文件 `registry_import_underground_parking.xlsx`（mtime 2026-11-16 14:00，早于本批）。本批改动前后该用例均失败；把当前代码复制到无该文件的 scratch 目录后 `tests.integration.test_registry_export_cmd`：`Ran 16 tests … OK`。其余 821 条通过，即相对基线（PM：822 OK）**零新增失败**；本批未新增用例文件，用例总数不变 |
| scratch 冒烟（`tests/integration/test_scratch_oav2.py`，仅在 scratch 副本，不入库；合成数据） | `Ran 5 tests … OK`：`relocate_shops` dry-run 零写（`CaptureQueriesContext` 无 INSERT/UPDATE/DELETE）、apply、幂等（`would_change=0`、`already_target=4`）、restore 逐记录还原、冲突整批停止（退出码 2）、参数错误（1）；选项接口第一级 `["1","地下车位","商铺","配套用房"]`、商铺第二级 `["1栋","2栋","10栋","建设南路142号"]` 与 `level_label`；导出命令未归类守卫（2）、`--allow-unrelocated`（`structure=legacy`）、改库后 `structure=shop_relocated` 且 `precheck_would_create_units=0`、位置守卫（部署根内/目录 0755 → 3）、参数互斥（1）；认证四种失败响应体逐字相同、全角空格归一；无手机号申诉通过追加产权人（`notice`）、同号属他人 409 且整笔回滚、历史申诉 `SKIPPED_NO_OWNER_NAME`、附件 403/401/管理员 200、申诉列表页内查询数不随行数增长；席位未来起始日不生效/占名额/`expire_due` 不处理/结束日≤今天拒绝/开始日过远拒绝/`change` 沿用开始日 |
| `(cd frontend && npx vitest run --passWithNoTests)` | `Test Files  25 passed (25)` / `Tests  259 passed (259)`（基线 259/259） |
| `(cd frontend && npm run build -- --base=/ocap/)` | `✓ built in 52.41s`，`build_exit=0`（仅既有的 chunk 大于 500 kB 警告） |
| `(cd miniprogram && npx vitest run --passWithNoTests)` | `Test Files  14 passed (14)` / `Tests  97 passed (97)`（基线 97/97） |
| `(cd miniprogram && npm run build:mp-weixin)`（package.json 脚本，`uni build -p mp-weixin`） | **失败（退出 1）**：`@dcloudio/uni-mp-weixin/dist/uni.compiler.js not found`、`ENOENT … miniprogram/src/manifest.json`。uni alpha 工具链期望 `src/manifest.json`，仓库自首次提交起 `manifest.json` 在小程序根目录（`git log` 指向 cdf949f），与本批改动无关（同记忆 M-SD-006）。**小程序构建未验证**；用 `@vue/compiler-sfc`（frontend/node_modules）对 `miniprogram/pages/units/index.vue`、`miniprogram/components/UnitPicker.vue` 做模板+脚本编译检查：均 `OK`；Web 5 个改动 .vue + 新增 `ProofThumbs.vue` 同样 `OK` |

未验证项与原因：(1) 小程序 `uni build -p mp-weixin`（工具链既有不兼容，见上）；(2) 浏览器真实行为（`ProofThumbs.vue` 的 `createImageBitmap`/`IntersectionObserver`/iframe pdf 预览，jsdom 无法代表，见 CR-001）；(3) `relocate_shops` 与导出命令对真实清册（107 条商铺）的运行——须用户另行授权，本批仅合成数据；(4) `backend/tests/remote/**`（P4-1，仅部署后、E2 执行，见 R-01）。

## 按模块评审

### MOD-112 楼栋排序与选项显示名
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**：无。

### MOD-111 商铺归类规则与改库命令
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 8/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-003 | MINOR | `backend/apps/registry/shops.py:24-27` | 复用 `underground.py` 的私有函数（`_chunks`、`_differences`、`_read_backup`），与 ADR-107 选项 A 一致，但把私有名变成跨模块契约；后续 `underground.py` 重构需同步。OQ-05 已记"第三种归属修正出现时再抽取通用引擎" | OPEN |

### MOD-113 导出命令加固
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 8/10 | 8/10 |

**CR 问题表**：无新增（环境产物导致的上批用例失败见"自验证结果"与 implementation_plan R-02，不记为本模块缺陷）。

### MOD-114 清册核对与追加
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 8/10 | 9/10 | 9/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-007 | MINOR | `backend/apps/registry/ownership.py` | `mask_phone` 原先放在函数内导入，无必要（registry 已依赖 core）；已移到模块顶部并复跑 `test_residency_api`、`test_registry_import_enhancement`（81 条 OK） | FIXED |

### MOD-115 认证与申诉后端
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 9/10 | 8/10 | 8/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-005 | MINOR | `backend/apps/committee/views.py`（`parse_date`）与本模块无关，记在此仅为归档 | 席位授予 `term_start` 为 "2026-02-30" 这类合法格式但非法日期时 `parse_date` 抛 `ValueError` 变 500；既有行为，本批未引入、未修（超出最小改动） | OPEN |

安全说明：认证失败单一出口且限频先于校验（REQ-NFUNC-037）；响应与日志不含清册姓名/手机号；申诉列表手机号脱敏；审计 `detail` 手机号脱敏；附件 403 会暴露"该 UUID 对应资料存在"（OQ-07，UUID 不可猜，已登记待用户确认），故安全分 8。

### MOD-116 席位生效判定与授予校验
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 9/10 | 9/10 | 9/10 |

**CR 问题表**：无。`git grep "term_end__gte\|term_end >="` 现仅剩 `effective.py` 一处定义；`identity/services.py:61`、`residency/housing.py:43` 把 `status="ACTIVE"` 的席位交给 `identity_view`（由其按 `is_effective` 过滤），与设计一致。

### MOD-117 Web 前端
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 7/10 | 8/10 | 7/10 | 8/10 | 6/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `frontend/src/admin/parts/ProofThumbs.vue`（`loadThumb`、`openAt`） | 缩略图、大图、pdf 预览依赖浏览器 `createImageBitmap`/`IntersectionObserver`/iframe，jsdom 无法验证；仅通过构建、SFC 编译与既有前端测试；缩略图带宽成本（OQ-03）仍在。建议 GROUP_D 做组件级测试（mock `admin.downloadAttachment`），E2 部署后在测试环境人工核对一页 20 条×5 文件的表现 | OPEN |
| CR-004 | MINOR | `frontend/src/portal/Units.vue:61-69`（`el-upload` `:limit="5"` + 自定义 `http-request`） | `:limit` 对自定义上传的已选数无意义，已在 `uploadProof` 手动限 5 个（超出提示）；若一次多选超过 5 个，超出部分被拦并提示，但 `el-upload` 自身的超限提示不会出现 | OPEN |
| CR-006 | MINOR | `frontend/src/admin/parts/ProofThumbs.vue`（`<style scoped>`） | 首版 `border: 1px solid var(--line)` 简写触发 `admin_theme.spec.js` 的"<style> 仅用变量"守护；已拆为 `border-style/width/color` 并复跑该用例与全量 | FIXED |
| CR-008 | MINOR | `frontend/tests/`、`miniprogram/tests/` | 本批新增页面逻辑（姓名输入/转申诉/多附件/`level_label`/`ProofThumbs`/"待生效"）暂无专门自动化用例（按职责由 test-engineer 写 `owner_auth_v2.spec.js`）；现有用例仅做最小同步 | OPEN |

### MOD-118 小程序
**五维评分表**
| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 8/10 | 9/10 | 8/10 | 6/10 |

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-002 | MAJOR | `backend/tests/remote/remote_cases.py:328`（实际风险在远程用例 TC-E2E-337 流程） | 远程用例对测试环境真实房屋 `FIX["u1"]` 提交申诉并"通过"，本批起通过会向真实清册追加产权人，可能越出画像 P4-1（不得改动已导入清册）。本批仅补 `owner_name` 参数使其可调用，未运行远程用例；请 PM 决定改用 e2e 专属专有部分或标 NOT_TESTABLE | OPEN |

小程序构建 `uni build -p mp-weixin` 因工具链既有不兼容无法运行（见自验证结果）；小程序申诉资料仅图片（OQ-06，AC-201-01 PARTIAL）；Testability 6 对应 CR-008。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

共 2 条（≤3，无需逐条说明处理时机之外的额外理由，仍写明如下）：
- CR-001：原因为 jsdom 无法验证浏览器 API；建议 GROUP_D 补组件级用例，E2 部署后人工核对缩略图性能。
- CR-002：原因为画像 P4-1 边界与远程用例设计属 test-engineer/E2 范围；建议 PM 在 GROUP_D 回合前裁定。

## 缺陷修复

不适用（非缺陷修复模式）。

## 现有测试调整

逐条清单见 `implementation_plan.md` 的"既有测试最小同步"表（文件:行、原断言、新断言、原因）。共 21 个测试文件：后端 18、前端 1、小程序 2；均为 `name`/`owner_name` 入参补充、错误码 `PHONE_NOT_IN_REGISTRY`/`PHONE_REQUIRED` → `OWNER_NOT_MATCHED`、楼栋排序层级、`/admin/appeals` 键集合、附件 404→403、TC-INT-472 开始日规则、小程序姓名输入框断言；未删除或跳过任何用例，用例总数不变（后端 822、前端 259、小程序 97）。
