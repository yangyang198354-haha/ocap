<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-21T11:44:58+08:00</timestamp>
  <project_name>ocap_profile_hierarchy</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>project_workspace/ocap_profile_hierarchy/requirements/requirements_spec.md</file>
    <file>project_workspace/ocap_profile_hierarchy/requirements/user_stories.md</file>
    <file>frontend/src/portal/UserProfile.vue</file>
    <file>miniprogram/pages/me/index.vue</file>
    <file>miniprogram/utils/api.js</file>
    <file>backend/apps/identity/services.py</file>
  </input_files>
  <phase>PHASE_03</phase>
  <status>APPROVED</status>
</file_header>

# 架构设计：个人主页信息层级与实名认证徽章

## 架构概览

INCREMENTAL，改动位于现有展示层：Web 端 `frontend/src/portal/UserProfile.vue` 与小程序“我的”页 `miniprogram/pages/me/index.vue`。后端契约与数据模型不变，复用现有 `GET /me/profile`（本人）与 `GET /users/{id}/profile`（他人）。

关键质量属性：
- 一致性：Web 与小程序使用相同的展示顺序与徽章规则（REQ-FUNC-264～268）。
- 隐私：实名仍只由 `real_name_visible` 与有效产权实名决定，不扩大公开白名单（C-87）。
- 可降级：小程序实名数据获取失败时隐藏实名与徽章，不影响昵称与身份（AC-276-03）。

## 部署视图

| 组件 | 运行单元 | 环境 |
|---|---|---|
| Web 前端 | Vite 构建产物，由 nginx 提供 `/ocap/` 静态资源 | 树莓派测试环境（画像 P7） |
| 后端 API | gunicorn `ocap-backend`（本次无改动，不重启） | 树莓派测试环境 |
| 微信小程序 | uni-app 构建 `mp-weixin`，微信开发者工具预览/上传 | 微信开发者工具/微信平台 |

## ADR

### ADR-156: 多端统一“昵称 → 实名（含徽章）→ 身份”的信息层级
- Status: Proposed
- Type: constraint-driven
- Context: REQ-FUNC-264、REQ-FUNC-267、REQ-FUNC-268、US-273、US-276。用户明确要求先昵称/实名、后身份，并已确认“昵称为主、实名紧随其后”（D-02）。
- 被排除方案：
  - “实名替换昵称作为主标题”：用户 2026-11-21 明确否决（D-02），且会改变现有昵称识别。
  - 保持现状（昵称 → 身份 → 实名）：不满足用户对顺序的要求。
- Decision: 昵称固定在主标题位；实名存在时紧随昵称（同一主信息区），随后才是身份标记；两端一致。
- Consequences: 正向——两端规则统一、实现集中；负向——主信息行元素增多，窄屏需要允许换行（module_design 中给出布局约束）。

### ADR-157: 小程序实名数据来源复用 `GET /me/profile`
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-268、AC-276-01、AC-276-03。`/me` 的 `profile` 不含 `real_name`（`backend/apps/identity/services.py:64-71`），而 `/me/profile` 已返回 `real_name`、`real_name_visible`、`can_show_real_name`（`backend/apps/accounts/views.py:280-291`）；小程序已有 `api.profile()`（`miniprogram/utils/api.js:20`）。
- Options:
  - A 复用 `GET /me/profile`：优——零后端改动、无需后端发布与重启；请求失败可与 `auth.fetchMe()` 隔离，天然满足 AC-276-03；缺——“我的”页多一次请求（仅该页，单次）。
  - B 在 `/me` 的 `profile` 中补充 `real_name`/`real_name_visible`：优——少一次请求；缺——需改后端序列化并重新发布后端，扩大本批部署面；`/me` 是高频接口，改动影响面大于本次收益。
- Decision: 选择 A。本次为展示层增量，优先最小改动与失败隔离。
- Consequences: 正向——不触碰后端契约与公开白名单；负向——“我的”页加载多一次并行请求，需在 `onShow` 中容错（失败隐藏实名）。

### ADR-158: 身份与实名/徽章复用现有标签与主题令牌
- Status: Proposed
- Type: decision
- Context: REQ-FUNC-265、REQ-FUNC-266、AC-275-01、AC-275-02。现有 Web 有 `el-tag` 与 `.tag` 体系（`frontend/src/shared/style.css:32-39`），小程序有全局 `.tag` / `.tag.is-success`（`miniprogram/App.vue:21-24`），主题令牌含 `--text`、`--muted`、`--success`、`--success-bg`。
- Options:
  - A 复用现有标签与主题令牌：实名用正文色 + 加粗；认证徽章用 success 标签；身份沿用 info/muted 标签。优——零新依赖、自动适配全部主题；缺——样式区分度受现有令牌限制。
  - B 新增自定义徽章组件与专属色值：优——视觉自由度大；缺——需要在 Web/小程序各实现一次并逐主题校验，违背最小改动。
- Decision: 选择 A。身份保持 `type="info"`/`.tag`（muted，小字号）；实名文本使用 `var(--text)`、字重 650；认证徽章使用 success 语义色。由此满足“颜色与字体至少各一项不同”。
- Consequences: 正向——与主题系统一致、测试可断言计算样式差异；负向——徽章语义色与业务状态色共用 success 令牌，后续若调整状态色会同时影响徽章。

### ADR-159: 小程序实名请求失败时静默降级
- Status: Proposed
- Type: constraint-driven
- Context: AC-276-03。`/me/profile` 与 `/me` 是独立请求，失败不应阻断“我的”页。
- 约束来源：现有 `load()` 已对 `housing()`、`reports` 做独立 try/catch（`miniprogram/pages/me/index.vue:85-101`）。
- Decision: `/me/profile` 失败时把实名状态置空并隐藏徽章，不弹出错误提示；昵称与身份仍来自 `auth.me`。
- Consequences: 正向——页面可用性不受次要请求影响；负向——用户可能短暂看不到实名，需下次进入页面重试。

## 开放问题 / ASSUMPTION

| ID | 内容 | 类型 |
|---|---|---|
| AS-01 | 徽章文案采用“已实名认证”，对勾使用字符“✓”，作为前端常量，后续可替换为设计稿文案 | [ASSUMPTION] |
| AS-02 | 实名文本保留“实名：”前缀（与现状一致），徽章紧随实名值之后 | [ASSUMPTION] |
| OQ-01 | 身份标签是否需要在暗色主题下额外提高对比度 | 开放问题（由测试覆盖现有主题后确认） |
