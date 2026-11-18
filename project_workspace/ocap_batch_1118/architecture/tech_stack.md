<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T00:54:23+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>architecture/architecture_design.md（0.1.0）</file>
    <file>architecture/module_design.md（0.1.0）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（INCREMENTAL：沿用既有栈，不新增任何依赖）

本批不引入新的第三方依赖、框架、服务或环境变量；未联网（不引入新依赖，且无闭源 API 事实需要核实）。版本均取仓库实测，不推测。

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言（后端） | Python | CI 用 3.13（画像 P4 [REPO ci.yml]）；本机 3.12 | 沿用 | 既有；本批代码避免在类体内用 `list/dict/set` 作成员名遮蔽注解（M-SA-008） | 全部 | 低 |
| 后端框架 | Django + DRF | `Django>=5.2,<6.0`、`djangorestframework>=3.15,<4.0`（`backend/requirements.txt:1-2`）；测试机 5.2.19（画像 P4） | 沿用 | 既有；DRF 默认解析器已含 MultiPart，申诉 multipart 分支无需配置（`config/settings.py:89-94`） | REQ-FUNC-239/240 | 迁移禁用 Django 6.x 生成（P4） |
| 数据存储 | MySQL（测试环境）/ SQLite 内存库（测试） | 画像 P1 | 沿用 | 新增 FK 列与唯一约束在两库行为一致（MySQL 唯一索引允许多个 NULL，同 M-SA-001 做法） | REQ-FUNC-251/252、REQ-NFUNC-049 | `Seat.user` 改可空须穷举读取点（module_design MOD-140） |
| 迁移 | 手写、单 app | committee 0002、residency 0005（画像 P6） | 沿用方式 | 画像 P6/P8 禁止提交 makemigrations 产物 | REQ-FUNC-251/252 | 测试库不跑迁移，须人工核对并用 `makemigrations --check --dry-run` 只读比对 |
| 文件存储 | 本地磁盘 `MEDIA_ROOT/<purpose>/` + `Attachment` 表 | `backend/apps/core/attachments.py` | 沿用 | 申诉文件仍落本地；新增"落盘后失败清理"补偿 | REQ-NFUNC-049(1) | 事务回滚不删磁盘文件，进程在落盘与清理之间被杀会留孤立文件（概率低，可由运维差集清理） |
| 前端框架 | Vue 3 + Vite + Element Plus + Pinia + vue-router + axios | `vue ^3.5.13`、`element-plus ^2.8.7`（本机实测 2.14.8）、`pinia ^2.1.7`、`vue-router ^4.4.5`、`axios ^1.7.9`、`vite ^6.0.1`（`frontend/package.json:20-31`） | 沿用 | `el-select` 的 `filterable`/`filter-method`、`el-table` 的 `sortable="custom"`/`sort-orders`、`el-upload` 的 `auto-upload=false` 均为既有能力，免新依赖 | REQ-FUNC-241/239/250 | 个别 prop 在 2.8.7 下限与 2.14.8 实装间可能有差异——package.json 为 `^`，实装以锁定版本为准，开发须在 2.8.7 语义下不使用新近才加入的属性 |
| 动效 | 纯 CSS（`transform/opacity/height`）+ Vue `<Transition>` JS 钩子 | 同上 | 沿用（无动效库） | 不引入动画库（画像 P8 无禁用，但无必要）；`@media (prefers-reduced-motion: no-preference)` 包裹所有新增规则，另有全局减少动效规则兜底 | REQ-FUNC-247/248、REQ-NFUNC-047 | 三主题观感需人工核对；`style.css` 不得含颜色字面量（`theme.spec` 守护） |
| 前端测试 | vitest | `vitest ^2.1.9`（`frontend/package.json:31`）；基线 37 文件 438 条（画像 P4，GROUP_C 前须重测） | 沿用 | 既有 | REQ-NFUNC-050 | jsdom 缺 `matchMedia`、`scrollIntoView`，须容错（M-SA-021） |
| 后端测试 | Django test runner，SQLite，替身 `apps/integrations/fakes.py` | 基线 957 条（画像 P4，GROUP_C 前须重测） | 沿用 | 既有；契约测试静态读取前端源码（`test_frontend_contract.py`、`test_owner_auth_v2_contract.py`） | REQ-NFUNC-050 | 只改前端也须跑后端全量（画像 P4） |
| 小程序 | uni-app (Vue 3) + Pinia + vitest | `miniprogram/package.json:13-17`；基线 16 文件 119 条 | 沿用（本批不改） | Q-B18-01=A | REQ-NFUNC-050 | 后端行为变化对其可见（进行中决议出现于公开页，`votes` 移除），见 ADR-146 |
| 进程管理 / 部署 | systemd `ocap-backend` + gunicorn + nginx（物理机） | 画像 P7 | 沿用 | 无变化；Docker 禁用（P8） | — | nginx `client_max_body_size` 须核实 ≥ 55 MB（仓库外配置，OQ-B7） |
| CI/CD | GitHub Actions `ci.yml`（只测试与构建） | 画像 P7 | 沿用 | 无变化 | — | — |
| 新增依赖 | 无 | — | — | — | — | — |

## 技术风险

### High
- 无 High 级风险。

### Medium
1. **单请求 multipart 体积（ADR-136）**：最多 5×10 MB。缓解：E1 只读核实 ocap 站点与 Freeark `^~ /ocap/` 块的 `client_max_body_size` 与 gunicorn `--timeout`（M-DE-007）；服务端先校验后落盘，内存最多同时持有 5 个文件内容（≈50 MB，测试机 4 GB 内存可接受），必要时开发改为流式写盘但保持"先全部校验"。
2. **`Seat.user` 可空（ADR-137）**：遗漏读取点会在待绑定席位上抛 `AttributeError`/`TypeError`（如 `polls/views.py:71` 的 `sorted` 遇 `None`）。缓解：module_design MOD-140 已列穷举清单；`active_member_ids`/`active_representative_ids` 排除空 user；新增回归用例构造待绑定席位后遍历席位列表、业主代表投票创建、决议表决与列表。
3. **公开范围与隐私变更（ADR-141）**：进行中决议公开、头像对登录用户可读、`votes` 移除。缓解：隐私度量写成用例（参与人响应无选项/手机号/真实姓名；公开决议响应无"谁投了什么"）；对用户的确认项见 OQ-B4/B5。
4. **表决口径副作用（ADR-139，用户已选）**：待绑定越多半数同意越难通过。缓解：席位页只读提示（Q-B18-33 推荐 A，用户待确认）。
5. **契约测试连带改动（画像 P4）**：`/me/housing` 字段集、`createAppeal` 键断言、决议公开用例需同步；缓解：module_design 已列出具体文件与行号，GROUP_C 先改测试断言再改代码并全量跑。

### Low
1. **清册改名使待绑定席位失效**：缓解：审计原因"清册变化"，管理员重新授予（OQ-B6）。
2. **自然顺序排序在内存完成（ADR-142）**：约 650 套毫秒级；规模到数万行前无需优化。缓解：记录阈值，增长后改为冗余排序列（需迁移）。
3. **旧认证用户无 `registry_owner` 记录（ADR-138）**：缓解：`certified_user_of` 手机号回退；仍失败时用"用户 ID 授予"旧路径（OQ-B1）。
4. **磁盘孤立文件（ADR-136）**：进程被杀于落盘与清理之间。缓解：差集脚本（运维，非本批交付）。
5. **动效观感与可达性**：缓解：减少动效下动画数 = 0 的 vitest 断言（样式文本检查）+ 人工三主题核对。
