<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-17T18:12:16+08:00</timestamp>
  <project_name>ocap_identity_property</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_identity_property/requirements/requirements_spec.md（1.0.0）</file>
    <file>project_workspace/ocap_identity_property/architecture/architecture_design.md（0.1.0）</file>
    <file>project_workspace/ocap_identity_property/architecture/module_design.md（0.1.0）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（INCREMENTAL：全部沿用，不新增第三方依赖）

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增 / 沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 语言 / 框架（后端） | Python + Django + DRF | `Django>=5.2,<6.0`（`backend/requirements.txt`，画像 P1）；测试机 5.2.19（画像 P4） | 沿用 | 新增 1 个模型、3 个 APIView，与 `residency` 现有写法一致 | REQ-FUNC-233~236 | 不得用 Django 6.x 生成迁移（画像 P4），迁移手写 |
| 数据存储 | MySQL（测试环境）/ SQLite 内存库（测试） | 画像 P1 | 沿用 | 新表仅用 OneToOne、CharField、DateTimeField，两库行为一致；刻意不用 JSON 列（ADR-128 方案 D 被否） | REQ-FUNC-234 | 状态枚举最长 9 字，列宽取 12 |
| 前端（Web） | Vue 3 + Vite + Element Plus + vue-router + Pinia | `frontend/package.json`（画像 P1） | 沿用 | 同组件多路由（ADR-119 既有做法）、store 既有 `useHousingStore` | REQ-FUNC-224~232、238 | 页面拆分后契约测试静态读源码，变量名受约束 |
| 前端（小程序） | uni-app (Vue 3) + Pinia | `miniprogram/package.json`（画像 P1） | 沿用 | 单页重排，不增 `pages.json` 条目 | REQ-FUNC-237 | 安装依赖需 `--legacy-peer-deps`（画像 P4） |
| 测试 | Django test runner；vitest（Web、小程序） | 画像 P4：后端 957、前端 438、小程序 119 的基线 | 沿用 | 基线模式（零新增失败） | REQ-NFUNC-044 | 大量既有用例需随文案与路由调整（module_design"测试影响"） |
| 进程管理 | systemd `ocap-backend` + gunicorn + nginx | 画像 P7 | 沿用 | 无新增运行单元 | — | 迁移须先于重启 |
| CI/CD | GitHub Actions（只测试与构建） | 画像 P7 | 沿用 | 无变更 | — | — |
| 部署方式 | 物理机 tar → scp → 解包 → 迁移 → systemd 重启 | 画像 P7 | 沿用 | 不用容器（画像 P8） | — | — |
| 新增依赖 | 无 | — | — | — | — | — |
| 联网查询 | 未进行 | — | — | 不引入新依赖、不涉及闭源 API，无需联网（协议 §L-7 / §N-3） | — | — |

## 技术风险

### High
- **H-1 校验旁路风险（确认接口）**：确认接口若漏掉"集合子集校验"会成为绕过姓名核对的通道（C-71）。缓解：校验写在 `PhoneMatchService.confirm` 内、以服务端 `units_by_phone(user.phone)` 为准；用例必须覆盖"勾选他人专有部分 → 422 且无 Membership""非 PENDING → 409""限频"（TC 由 test-engineer 落到 `backend/tests/integration`）。
- **H-2 契约测试静态读取前端源码**：页面拆分/新增变量名（`item`/`unit`/`r`）会让 `test_frontend_contract.py`、`test_owner_auth_v2_contract.py` 误判。缓解：module_design 已列出受影响行号与命名约束；开发完成后必须跑后端全量（画像 P4）。

### Medium
- **M-1 `auto_bound` 弃用字段**：恒空字段残留，旧测试多处断言。缓解：ADR-130；一次性改完 5 个后端测试文件；后续批次移除字段。
- **M-2 旧地址兼容回归**：`/units/review`、`/units#review`、`/units/pick`、`/me/identity` 多处被现有 vitest 断言。缓解：逐条同步用例，新增"非产权业主打开 `/units/review` 无卡片"用例。
- **M-3 PENDING 期间清册新增同号码专有部分会出现在列表**：已列为开放问题；用户逐套勾选确认，风险可接受。缓解：如需完全固定，改用 ADR-128 方案 D。
- **M-4 小程序无法在本机构建验证**：缓解：以 vitest 页面用例与契约测试覆盖，微信开发者工具手工验收（NOT_TESTABLE 清单由 test-engineer 登记）。

### Low
- **L-1 jsdom 无 `scrollIntoView`、`matchMedia`**：缓解：调用处用可选链容错（`?.scrollIntoView?.()`，沿用 M-SA-021 思路）。
- **L-2 `MeIdentity.vue` 删除后残留引用**：缓解：开发后 `git grep MeIdentity`，并同步 `layout_pages.spec.js:27`、`product_review_ui.spec.js:28`。
- **L-3 迁移依赖的 accounts 最新迁移编号**：开发时以 `ls backend/apps/accounts/migrations` 核对后填写，不可凭记忆。
