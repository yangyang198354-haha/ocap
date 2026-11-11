<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T22:45:48+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
    <file>architecture/module_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型：管理端打磨（INCREMENTAL）

> 本次**不新增任何第三方依赖**，不联网查询（无新依赖、无外部 API；版本均取自仓库依赖清单与本机 `npm ls` 实测）。选型沿用画像 P1 与基线 `ocap_registry_import`、`ocap_ui_theme`。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言/框架 | Python + Django + DRF | Django `>=5.2,<6.0`、DRF `>=3.15,<4.0`（`backend/requirements.txt:1-2`）；测试机实测 Django 5.2.19、CI Python 3.13（画像 P4）。**不得用 Django 6.x 生成/校验迁移**（画像 P4） | 沿用 | 规则与偏好接口都是既有视图/模型的小改动 | REQ-FUNC-123~129/130~132 | 迁移须手写（画像 P6/P8），已设计为手写 `RunPython` 与 `AddField` |
| 数据库 | MySQL（测试环境库 `ocap`）；测试 SQLite 内存库 | 画像 P1/P7；测试 `MIGRATION_MODULES` 置空（`backend/config/test_settings.py:17`，不跑迁移） | 沿用 | 数据迁移函数可被测试直接调用（`importlib`），不依赖迁移执行 | REQ-FUNC-125、REQ-NFUNC-19/23 | MySQL 无事务性 DDL：数据迁移在函数内显式 `transaction.atomic`（ADR-067）；MySQL 唯一索引大小写不敏感 → 冲突检测用 `casefold`，库层约束兜底 |
| 数据迁移手段 | Django `RunPython` + 历史模型 `apps.get_model`；规则为迁移内**冻结副本** | 沿用既有写法 `registry/migrations/0003_backfill_legacy_owners.py` | 沿用（模式） | 不依赖会演进的应用代码（ADR-066）；可逆；幂等 | REQ-FUNC-125 | 运行时规则与迁移副本是有意的两份（金标测试分别守护） |
| 批量更新 | `QuerySet.bulk_update(batch_size=200)` | Django 内置 | 沿用 | 5742 行约 58 条更新语句；200×3 变量 <999 适配 SQLite 旧上限（既有提交"导入批量查询分批适配 SQLite 变量上限"） | REQ-NFUNC-23 | `bulk_update` 不刷新 `auto_now`（OQ-05 已决定不刷新） |
| 管理命令 | Django `BaseCommand`（`registry_specific_part_preview`） | Django 内置；既有命令位于 `backend/apps/jobs/management/commands/` | 沿用（模式） | 只读预检/幂等核对，不引入 HTTP 接口与鉴权面 | REQ-FUNC-125 | 无应用级鉴权（依赖服务器 shell 权限），输出不含姓名与手机号 |
| 表格模板生成 | `openpyxl` | `>=3.1,<4.0`（`backend/requirements.txt:5`） | 沿用 | 模板示例行由单一来源生成（ADR-070） | REQ-FUNC-129 | 无新增 |
| 前端框架 | Vue 3 + Pinia + vue-router + axios | `npm ls` 实测 vue 3.5.45；`frontend/package.json:20-24`（pinia `^2.1.7`、vue-router `^4.4.5`、axios `^1.7.9`） | 沿用 | 管理端 store 与用户端 store 并列（ADR-072） | REQ-FUNC-130~135 | 无新增 |
| UI 组件库 | Element Plus | 2.14.8（`npm ls` 实测；`package.json:21` 为 `^2.8.7`）；许可证 MIT（基线 ocap_ui_theme tech_stack 已核实，本次未复核） | 沿用 | 顶栏切换用 `el-dropdown`（ADR-074）；换肤沿用 `--el-*` 变量映射 | REQ-FUNC-130/133 | 个别组件在深色风格下可能残留默认色（基线 OQ-T03 同类风险），走查清单覆盖 |
| 风格体系 | 风格定义 `themes/*.theme.json` + `scripts/themes/build.mjs` 生成 `themes.css` / `registry.js` | 仓库内脚本，仅 Node 内置模块；本机 Node 22.23.3（`node --version`）；CI Node 版本以 `.github/workflows/ci.yml` 为准（本次未改） | 沿用 | 管理端作用域覆盖写在 `themes/bento.web.css`，对比度项写在 `bento.theme.json`，由脚本实算校验（ADR-075；1.1.0 增渐变顶栏，复用 `--hero`/`--on-hero`，不新增 token，不改构建脚本） | REQ-FUNC-133、REQ-NFUNC-21 | 生成物须与源同步提交（`--check` 守护）；构建脚本只校验单色背景，渐变插值由前端守护测试补足（OQ-12） |
| 前端测试 | vitest + @vue/test-utils | vitest `^2.1.9`、`@vue/test-utils` 实测 2.5.1、vite 6.4.5（`package.json:28-31`、`npm ls`） | 沿用 | 新增 `admin_theme.spec.js`、`admin_theme_store.spec.js`；位置 `frontend/tests/`（画像 P3） | REQ-NFUNC-20 | 无 |
| 后端测试 | Django test runner | 画像 P4 | 沿用 | 新增用例位于 `backend/tests/{unit,integration}/`（画像 P3） | REQ-NFUNC-20 | 既有约 10 个测试文件有旧格式断言，须同步更新并单列说明 |
| 小程序 | uni-app（Pinia、vitest） | 画像 P1 | 沿用，**本次零改动**（ADR-077） | 无展示点、无管理端调用（`git grep -n "specific" -- miniprogram` 无命中） | REQ-FUNC-126 | 无 |
| 进程管理/部署 | 物理机 tar → scp → 解包 → 迁移 → systemd 重启，不用容器 | 画像 P7；`ocap-backend`（gunicorn 127.0.0.1:9000）+ nginx 8090 | 沿用 | 迁移 `registry 0005`、`accounts 0003` 随部署执行；建议停服务→迁移→启动（OQ-04） | REQ-FUNC-125 | 迁移与重启之间旧代码可能用旧规则写入单条编辑（OQ-04） |
| CI/CD | GitHub Actions（只跑测试与构建，不部署） | `.github/workflows/ci.yml`（画像 P7） | 沿用 | 无变化 | — | 无 |
| 新增依赖 | 无 | — | — | — | — | — |

## 技术风险

### High
- **H1 存量标识重新生成在目标库上的唯一约束交叉**：新值与另一条记录的旧值相同（例如 `车库A-088`）会让单遍更新中途违反唯一约束，且 MySQL 不支持事务性 DDL、MySQL 唯一索引大小写不敏感。缓解：先全量检测、两阶段占位更新、整体单事务、库层 `IntegrityError` 触发整批回滚（ADR-067）；测试覆盖交叉与冲突两类样例；上线前用 `registry_specific_part_preview` 在目标环境复核冲突 = 0；迁移前 `dumpdata registry.registryunit` 作数据级备份（OQ-04，由 E1 写入计划）。
- **H2 迁移与重启之间的新旧规则混写**：迁移后、重启前旧进程仍按旧规则处理单条新增/编辑，可能写入旧格式标识。缓解：建议停服务→迁移→启动；若不停服务，事后用核对命令检查 `would_change`，非 0 则再次执行迁移函数（幂等）。

### Medium
- **M1 `[INFERRED]` 5742 条 ≤60 秒**（REQ-NFUNC-23 前半）：设计估算约 58 条批量语句，远低于上限 `[ESTIMATE]`；缓解：测试环境实测并记入部署报告。
- **M2 规则边界的歧义**：全角数字、"1层楼"类户号是否算"以楼层值+层开头"（OQ-02/OQ-03）。缓解：已按字面实现并写入金标；建议 PM 在测试环境只读统计含非 ASCII 数字的字段条数。
- **M3 管理端"同等程度"的视觉效果无法自动判定**（ADR-075 口径第 7 项）：缓解：15 页 × 3 风格走查清单列入 test_plan 的人工验证清单；自动化覆盖无固定色/无内联色/作用域规则/对比度。
- **M4 窄屏顶栏**：13 个导航项 + 切换入口在 <768px 会换行（OQ-09）。缓解：不做布局重构，只保证可用与 44px 点击区域；走查清单项。
- **M5 既有测试的同步面较大**：旧格式断言（约 10 个后端测试文件）与"管理端固定 B"断言（4 个前端测试文件）。缓解：module_design MOD-073 列出清单，按基线实跑逐个核对，修改后单列说明，gate_mode=baseline 以零新增失败为准。

- **M6（1.1.0）渐变顶栏白字余量小**：渐变右端 `#DB2777` 上白字 4.60:1（阈值 4.5），插值最小 4.592；构建脚本不解析渐变。缓解：三个停点逐一建 `contrast` 项 + 前端守护测试对渐变插值采样 + 叠加层只许深色（ADR-075、MOD-073）；日后调整 `hero` 须同步更新。

### Low
- **L1 管理员偏好接口无限流**（OQ-06）：只改本人一个字段、写入成本低；缓解：PM 门控确认，必要时复用 `RateLimiter.hit`。
- **L2 已下线风格 key 留在库里**：读时由客户端回退 B（沿用基线 ADR-025），无安全影响。
- **L3 B 风格管理端主按钮改用强调色**（OQ-07 已关闭，用户 Q-B1=B 确认）：仅作用于 `data-surface="admin"`，用户端不受影响；缓解：走查时请用户确认视觉。
- **L4（1.1.0）高亮形态为推断**：导航当前页高亮选白色胶囊 + 强调色文字，备选强调色填充（OQ-11）；缓解：走查确认，改选只动一条 CSS 规则。
