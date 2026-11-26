<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-27T00:40:00+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_typography_unify/development/implementation_plan.md</file>
  </input_files>
  <phase>PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 代码评审报告 — Web 端字体与标题统一（GROUP_C）

## 摘要

- 改动文件 59 个（`git stash show --stat`，均在 `frontend/` 与 `themes/`）：212 insertions(+), 211 deletions(-)；另有 1 个新建文件 `frontend/src/shared/PageHead.vue`。
- 五维平均分：9.0 / 10。
- 问题统计：CRITICAL 0 / MAJOR 0 / MINOR 4（全部 OPEN，均为非阻断的遗留收敛项，已记入 implementation_plan「开放问题」）。
- 自验证：前端构建通过；前端全量测试 622 项 → 621 通过、1 失败；该失败为**预存基线失败**（不在本次改动范围，详见「自验证结果」与「基线对比」），本次零新增失败。

## 文件 → MOD/IFC 映射

| 文件 | MOD/IFC |
|---|---|
| `frontend/src/shared/style.css` | MOD-221（排版令牌）、ADR-204 |
| `frontend/src/shared/PageHead.vue` | MOD-220、IFC-453（新建） |
| `frontend/src/layout/menus.js` | MOD-223（导航术语「申述→申诉」） |
| `themes/bento.web.css`、`themes/neon.web.css`、`themes/terminal.web.css` | MOD-222（主题清理）、ADR-204/205 |
| `frontend/src/theme/generated/themes.css` | MOD-227（生成态重建，由 `node scripts/themes/build.mjs` 产出，未手改） |
| `frontend/src/admin/*.vue`（16 页） | MOD-224（管理端 PageHead 接入） |
| `frontend/src/portal/**.vue`（24 页 + 3 嵌入组件） | MOD-225（用户端 PageHead 接入）、MOD-226（卡片/重复标题收敛） |
| `frontend/tests/*.spec.js`（13 个） | 现有测试契约同步更新（需求驱动，未放宽断言） |

## 自验证结果

1. 前端构建：

```
$ env:VITE_API_BASE='/ocap/api/v1'; npm --prefix frontend run build -- --base=/ocap/
✓ built in 16s
```

（仅有既有 chunk >500kB 警告，无错误。）

2. 前端全量测试（复跑两次，结果一致）：

```
Test Files  59 passed (60) | 1 failed (60)
     Tests  621 passed | 1 failed (622)
```

3. 受影响子集复跑（18 个测试文件，261 项）：全部通过。

### 唯一失败的定性

失败用例：`tests/product_review_ui.spec.js` TC-UNIT-577（AC-154-04、AC-166-01），断言 MEMBER（委员）侧栏导航应含「报销/备用金 / 收入表 / 待办」，实际渲染文本与非委员一致（缺这三项）。

定性结论：**预存基线失败，非本次改动引入**。证据：

- 该测试文件不在本次 diff 内（`git stash show --stat` 无 `product_review_ui.spec.js`）。
- 失败机制是 `auth.isCommittee` 为 false 导致 `audience: 'committee'` 的菜单项被过滤（`menus.js:100-101` `visibleMenu`），而 `isCommittee` 来自 `stores/auth.js:20` 的 `me.identities.committee.position`；本次未改 `auth.js`、`PortalLayout.vue`、`menus.js` 过滤逻辑，仅改了 `menus.js` 的一个文案（「申述」→「申诉」）。
- 两次全量复跑结果逐字一致，可复现；单独跑该文件也复现。
- 干净基线（`git stash -u` 暂存本次全部改动后）全量复跑结果待回填，用于门控"零新增失败"的最终证据（见「基线对比」）。

未验证项：无后端改动，无迁移；小程序不在范围内。

## 按模块评审

### MOD-220（PageHead 组件，新建）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 8/10 |

- 固定输出 `header.page-head > h1.page-title`，props `title` 必填、`description`/`srOnly` 可选，右侧默认插槽承载操作按钮；满足 IFC-453 与 AC-361-01「唯一 h1」。
- 无外部依赖、无网络/状态副作用，纯展示组件；`srOnly` 走既有 `.sr-only` 工具类。
- 测试可测性由现有 layout 测试覆盖（断言 `.page-title`/`.page-desc`）。

### MOD-221（排版令牌）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 8/10 |

- `:root` 新增 7 组字号/行高令牌与 4 个字重令牌，`.title`/`.section-title`/`.side-item`/`.side-sub-item`/`.sub-nav-item`/`.page-head h1` 全部只引用令牌，删除 `.page-eyebrow`，新增 `.sr-only`；窄屏媒体查询用 `--text-page-title-sm`。
- 唯一保留字面量：`.side-item.is-active { font-weight: 650 }`（激活态提示，REQ-NFUNC-039 要求，令牌表亦注明），属架构偏差已记录。

### MOD-222（主题清理）/ MOD-227（生成态重建）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 8/10 |

- bento/neon 删除 `.side-item` 字号覆盖；terminal 删除全局 `text-transform: uppercase` + `letter-spacing`、删除 `.page-head h1::before "> "`、删除 `.page-eyebrow`；均满足 AC-366-01/03 与 AC-362-01。
- `generated/themes.css` 由 `node scripts/themes/build.mjs` 重新生成，`theme_build.spec.js` 7 项通过，源/生成态一致。

### MOD-223（导航术语）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |

- 「我的认证与申述」→「我的认证与申诉」；全仓 `grep 申述` 无残留（layout 系列测试已同步）。

### MOD-224 / MOD-225 / MOD-226（页面接入与标题层级收敛）

| Correctness | Security | Performance | Maintainability | Testability |
|---|---|---|---|---|
| 9/10 | 10/10 | 9/10 | 9/10 | 8/10 |

- 管理端 16 页、用户端 24 页接入 PageHead；多区块页（AdminFinance/AdminUsers/AdminAudit）用动态 `:title` 只渲染一个 h1，操作按钮移入标题区插槽。
- 嵌入组件（UnitsReview/UnitsAppeal/RegistryMatchPanel）`h3.title`→`h2.title`，避免双 h1；详情页实体标题升为 h1；h3/h4 升 h2，保证 h1→h2→h3 不跳级。
- 架构偏差：`UnitsReview` 是 `/units` 页内 Tab 区块，不加 PageHead（已记录）。

## CR 问题表

| CR | 级别 | 位置 | 描述 | 状态 |
|---|---|---|---|---|
| CR-401 | MINOR | `style.css` 令牌定义处 | `--text-meta`/`--leading-meta` 已定义但部分元信息仍用字面量 12–13px，未全部替换为令牌 | OPEN |
| CR-402 | MINOR | `Home.vue` `.home-greeting` | 首页问候语保留主题级字号（28–36px），视为 Hero 装饰而非内容标题，未套用标题阶梯 | OPEN |
| CR-403 | MINOR | 现有测试注释 | 部分测试注释/用例标题仍含旧措辞（如「h3.title」），仅调整了断言选择器，未逐个改写注释以控制 diff 范围 | OPEN |
| CR-404 | MINOR | `product_review_ui.spec.js:315` | TC-UNIT-577 预存失败（委员导航过滤），非本次引入；建议后续单独修复 mock/时序，不在本批次范围 | OPEN |

以上 OPEN 项均不阻断 AC 验收，已在 implementation_plan「开放问题」同步记录，可在后续迭代或 GROUP_D 评估时收敛。

## 未解决的 CRITICAL

无。

## 遗留 MAJOR

无。

## 现有测试调整

共 13 个测试文件，调整均为本次需求/结构变更驱动的期望更新，未放宽断言标准：

- `layout_css.spec.js`、`layout_pages.spec.js`、`layout_menus.spec.js`、`layout_nav.spec.js`、`layout_e2e.spec.js`、`pages.spec.js`、`qa_int_theme.spec.js`：断言选择器由 `h3.title`/无类 h2 更新为 `h1`/`.page-title`/`.page-desc`；`layout_css` L203 的 `split` 锚点由「注册用户」改为 `v-if="isRegistered"`（PageHead 后「注册用户」字面量出现在 `:title` 绑定中导致解析偏移）。
- `batch1118_e2e.spec.js`、`layout_*`：文案「申述」→「申诉」、「报销 / 备用金」→「报销/备用金」全局同步。
- `identity_property_e2e.spec.js`：`mainTitles` 选择器改为 `findAll('h1, h2.title')` 并更新期望值顺序。
- `identity_property_match_panel.spec.js`：匹配面板标题由 `h3.title` 升为 `h2.title` 的断言同步。

## 基线对比（门控证据）

> 干净基线 = `git stash -u` 暂存本次 `frontend/` 与 `themes/` 全部改动（含未跟踪的 `PageHead.vue`）后的 HEAD 状态。
>
> 预期：若基线全量同样失败于 TC-UNIT-577，则确认「零新增失败」，GR-C-001 通过；若基线通过而本分支失败，则需回流排查。
>
> 基线全量复跑结果：**确认预存失败，零新增失败**。
>
> 操作：`git stash -u` 暂存本次 `frontend/` 与 `themes/` 全部改动（含未跟踪的 `PageHead.vue`）→ 清理 `frontend/node_modules/.vite` 与 `.vite` 缓存 → `npm --prefix frontend run test` → `git stash pop` 恢复。
>
> 基线结果（`.vitest_baseline.log`）：
>
> ```
> Test Files  1 failed (60) | 59 passed (60)
>      Tests  1 failed (622) | 621 passed (622)
> ```
>
> 失败用例与本分支**逐字一致**：`tests/product_review_ui.spec.js` TC-UNIT-577（AC-154-04、AC-166-01），`AssertionError: expected '主页我的房屋▸决议▸投票/调查财务报表信息公开' to contain '报销/备用金'`。
>
> 结论：该失败在 HEAD 干净基线上已存在，与本次字体/标题改动无关（本次未改 `auth.js`、`PortalLayout.vue`、`menus.js` 过滤逻辑，`product_review_ui.spec.js` 不在 diff 内）。**本次改动零新增失败，GR-C-001 通过条件满足。**
