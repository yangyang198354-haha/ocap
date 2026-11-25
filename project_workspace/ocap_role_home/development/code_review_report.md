<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-25T12:39:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_role_home/development/implementation_plan.md</file><file>frontend/src/portal/Home.vue</file><file>frontend/src/stores/auth.js</file><file>frontend/src/shared/style.css</file><file>miniprogram/pages/index/index.vue</file><file>miniprogram/store/auth.js</file></input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 — 代码评审报告

## 摘要

- 代码与测试改动：18 个文件，`536 insertions(+), 293 deletions(-)`（`git diff --stat -- frontend/src frontend/tests miniprogram/pages miniprogram/store miniprogram/tests`）；SDLC 文档改动未计入。
- 五维平均分：8.7 / 10。
- 问题统计：CRITICAL 0（已修复 0）、MAJOR 1（已修复 1）、MINOR 3（已修复 2，遗留 1）。
- 自验证：Web 构建通过、Web 607 项测试全通过；小程序构建通过、154 项测试全通过。

## 文件 → MOD/IFC 映射

| 文件 | MOD / IFC |
|---|---|
| `frontend/src/stores/auth.js` | MOD-215 / IFC-436 |
| `frontend/src/portal/Home.vue` | MOD-216 / IFC-437、438、439、440 |
| `frontend/src/shared/style.css` | MOD-217 / IFC-441 |
| `miniprogram/store/auth.js` | MOD-218 / IFC-442 |
| `miniprogram/pages/index/index.vue` | MOD-219 / IFC-443、444 |

## 自验证结果

### Web 构建

```bash
cd frontend && npm run build -- --base=/ocap/
# 输出尾部：
# dist/assets/index-dgc7SPY5.js  1,154.71 kB │ gzip: 382.01 kB
# ✓ built in 8.90s
```

### Web 现有测试

```bash
cd frontend && npx vitest run
# Test Files 57 passed (57)
#      Tests 607 passed (607)
```

### 小程序构建

```bash
cd miniprogram && UNI_INPUT_DIR=. npx uni build -p mp-weixin --outDir /tmp/mp-dist
# Compiler version: 5.36（vue3）
# Compiling...
# DONE  Build complete.
```

说明：仓库 `miniprogram/package.json` 的 `build:mp-weixin` 脚本按 `src/` 布局调用 uni CLI，而本仓库是 HBuilderX 根目录布局，直接运行会报 `src/manifest.json ENOENT`（既有配置问题，未改仓库）。使用 `UNI_INPUT_DIR=.` 指向根目录后构建成功，产物写入 `/tmp/mp-dist`，不污染仓库；见 implementation_plan DEV-3。

### 小程序现有测试

```bash
cd miniprogram && npm test
# Test Files 22 passed (22)
#      Tests 154 passed (154)
```

环境说明：`miniprogram/node_modules` 初始缺失，使用 `npm ci --legacy-peer-deps` 安装（uni-app 依赖存在 peer 冲突）；未修改 `package.json`/锁文件。

## 按模块评审

### MOD-215 / MOD-218 身份能力派生

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 9/10 | 10/10 | 9/10 | 9/10 |

- `isCommittee` 与后端 `IsCommitteeMember` 同口径（CHAIR/VICE_CHAIR/MEMBER）；`isRepresentative` 对应 `CommitteeQuery.is_representative`，未把代表误判为委员。
- `ownerUnits` 只收 HEAD/OWNER，与 `pending_review_count` 的后端统计口径一致（`backend/apps/residency/housing.py:164-174`）。
- 纯 getter，无副作用；`me` 为空时安全默认值。

### MOD-216 / MOD-219 首页编排

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 8/10 | 8/10 | 8/10 | 8/10 |

- 顺序表与 module_design 一致；任务模块按 `pendingTasks → pendingVotes → pendingReview` 插入，逐角色满足 AC-354~359。
- 首屏请求按能力裁剪：非委员不请求 `/approval/tasks`，无 HEAD/OWNER 房屋不请求 `/me/housing`（测试已断言请求列表）。
- 内容类模块保留空态（投票、公开决议、信息公开），任务类 0 隐藏（C-397）。
- 财务公开：所有登录用户可见合计 + 报表入口；游客不渲染逐账户行（D-RH-03）。
- 待我表决：仅前 3 条 OPEN+REP_VOTE 并行取详情，`allSettled` 单条失败降级“状态待确认”，请求数有上界。
- 公开决议：`Resolution` 标 `业委会决议`，`CLOSED REP_VOTE` 标 `业主代表决议`，合并倒序取 5 条（ADR-197，A-01）。

**CR 问题表**

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-001 | MAJOR | `frontend/src/portal/Home.vue` onMounted（修复前） | 决议/投票/信息原用单个 `try` + `Promise.all`：任一失败会把 `polls` 置空，导致投票模块误显示空态并丢失业主代表投票入口 | FIXED（改为 `Promise.allSettled`，分别降级） |
| CR-002 | MINOR | `Home.vue` / `index.vue` pendingReview 卡 | 复用 `.home-todo` 类使非委员首页看起来存在“待办卡”，与语义/旧测试冲突 | FIXED（取消 `.home-todo`，仅任务审批使用） |
| CR-003 | MINOR | `miniprogram/pages/index/index.vue` finance 卡（修复前） | 卡片点击跳 `/pages/reports/detail` 但无 `id`，必然失败 | FIXED（移除无参跳转，仅保留合计与明细） |
| CR-004 | MINOR | 两端 `CONTENT_ORDER` | 模块顺序常量在 Web/小程序各存一份，存在漂移风险 | OPEN（架构 ADR-200 已接受；GROUP_D 增加两端顺序一致性用例） |

### MOD-217 骨架样式

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 8/10 | 10/10 | 10/10 | 9/10 | 8/10 |

- 新增 `.home-half`（span 2）与 `.home-full`（≥768px span 4）；三主题 4 栏由现有生成物提供，未手改生成 CSS。
- 偏差 DEV-1：Hero 维持主题既有的 `span 2 / row span 2`，未强制 `span 4`，避免改动三套主题源并改变构图；不影响 4 栏骨架与 AC。
- 未删除旧 `.home-stat`/`.home-quick` 样式：当前无模板引用，保留可降低对未知页面的影响；后续可由样式清理任务处理。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无（仅 1 条 MAJOR 已修复）。

## 缺陷修复

不适用（本次为首次实现，非缺陷修复模式）。

## 现有测试调整

| 文件 | 调整原因 |
|---|---|
| `frontend/tests/ui_blocks.spec.js` | 旧断言要求 4 张统计卡与 ≥6 个快捷入口；新需求删除统计卡/宫格。改为断言角色化模块、空态与“任务 0 隐藏” |
| `frontend/tests/finance_accounts_ui.spec.js` | 模块标题“账户余额”→“财务公开” |
| `frontend/tests/identity_display.spec.js` | 旧“认证房屋”统计卡改为“我的房屋 · N”卡；游客旧“去认证产权”改为欢迎卡“去认证” |
| `frontend/tests/identity_property_e2e.spec.js` | 游客“去认证产权”→“去认证”；“待审批同住人申请：1”→“去处理”链接 `/units` |
| `frontend/tests/identity_property_identity_page.spec.js` | 统计卡断言改为“我的房屋 · N”；待审链接文案与目标改为“待我处理 · N”/`/units` |
| `frontend/tests/layout_pages.spec.js` | 源码断言更新为信息公开模块 `/info`、待我处理 `/units`、游客 `/units/pick` |
| `frontend/tests/pages.spec.js` | 移除 Hero 手机号断言（REQ-FUNC-374）；增加决议来源标签与“收入表”入口断言 |
| `frontend/tests/product_review_core.spec.js` | “待审批同住人申请：2”→“待我处理 · 2”；0 条时不显示 |
| `miniprogram/tests/identity_display.spec.js` | 游客“共 0 套”空态改为“不显示我的房屋 + 去认证” |
| `miniprogram/tests/identity_property_pages.spec.js` | 待审链接改为“待我处理 · 2”卡片，点击目标不变 |
| `miniprogram/tests/pages.spec.js` | 决议请求增加 `page_size: 5`；待办 403 时任务卡隐藏而非“暂无审批待办” |
| `miniprogram/tests/product_review_ui.spec.js` | 待审提示改为“待我处理 · 2”卡片；委员 0 待办不渲染卡；快捷宫格断言改为“管理快捷” |
| `miniprogram/tests/ui_blocks.spec.js` | 删除统计卡/7 入口断言，改为角色化模块与空态 |
