<file_header>
  <author_agent>requirement-analyst</author_agent>
  <timestamp>2026-11-26T23:45:32+08:00</timestamp>
  <project_name>ocap_typography_unify</project_name>
  <version>1.0.0</version>
  <input_files><file>project_workspace/ocap_typography_unify/requirements/requirements_spec.md</file></input_files>
  <phase>PHASE_02</phase>
  <status>APPROVED</status>
</file_header>

# 用户故事 — Web 端字体与标题统一

## 角色 × 功能矩阵

| 角色 | 页面标题 | 导航字体 | 卡片标题 | 术语一致 | 详情页标题 |
|---|---|---|---|---|---|
| 游客 | US-361、US-362、US-363 | US-366 | US-367 | US-364 | US-369 |
| 产权业主 | US-361、US-363 | US-366 | US-367 | US-364 | US-369 |
| 同住人 | US-361、US-363 | US-366 | US-367 | US-364 | US-369 |
| 业委会成员 | US-361、US-363、US-368 | US-366 | US-367 | US-364 | US-369 |
| 管理员 | US-361、US-363、US-368 | US-366 | US-367 | US-364 | US-369 |
| 设计/前端维护者 | US-365 | US-366、US-368 | US-367 | — | — |

## 用户故事

### US-361: 每个页面都有统一的页面标题
- 故事：As a 任意 Web 用户, I want to 在每个页面顶部看到同一套式样的页面标题, so that 我能立刻确认自己在哪个页面
- 关联需求：REQ-FUNC-376；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-361-01：Given 已登录用户访问 `/polls`、`/tasks`、`/admin/registry`、`/units` 等任一路由, When 页面完成渲染, Then 页面内存在且仅存在 1 个 `h1`，且该 `h1` 位于页面标题区（`.page-head`）内。
- AC-361-02：Given 访问 `/`（首页）, When 页面完成渲染, Then 存在 1 个仅供屏幕阅读器识别的 `h1`（文本"主页"），可见问候语不再是 `h2` 兼作页面标题。
- AC-361-03：Given 访问登录、注册、微信回调、管理端登录页, When 页面渲染, Then 不要求可见页面标题，但不得出现 `h2` 充当页面主标题。

### US-362: 页面标题只使用中文
- 故事：As a 任意 Web 用户, I want to 页面主标题始终是中文, so that 中英文混排不会让我误判层级
- 关联需求：REQ-FUNC-377；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-362-01：Given 依次访问 `/info`、`/polls`、`/reports`、`/resolutions`、`/me`, When 页面渲染, Then `h1` 文本为中文，页面中不存在英文眉标元素（`.page-eyebrow`）。
- AC-362-02：Given 页面包含品牌区, When 渲染, Then 英文品牌名只出现在品牌标识（`.brand` / `.side-brand`），不出现在任何 `h1`/`h2` 标题中。
- AC-362-03：Given 管理端 `/admin/content/services`, When 渲染, Then `h1` 为「AI 服务配置」，"模型与生成服务/提示词模板"作为说明行或 Tab，而不是拼接在主标题中。

### US-363: 缺失标题的页面补齐中文标题
- 故事：As a 任意 Web 用户, I want to 每个页面都有明确的标题, so that 我不需要靠导航高亮猜当前页面
- 关联需求：REQ-FUNC-378；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-363-01：Given 访问 `/units`（我的身份与房屋）、`/units/appeal`（我的认证与申诉）、`/tasks`、`/income`、`/historical-expenses`、`/me/profile`、`/me/settings`, When 渲染, Then 每个页面 `h1` 文本与《标题文案表》一致。
- AC-363-02：Given 访问管理端 13 个页面（registry/appeals/memberships/seats/flows/finance/finance-limit/finance-accounts/users/users-registered/audit/audit-logs/content-styles）, When 渲染, Then 每页都有 `h1`，且不再用无类 `h2` 作页面标题。
- AC-363-03：Given 访问 `/me`（窄屏聚合页）, When 渲染, Then 页面只有一个"我的"页面标题，正文不再重复一个同文案的 `h3`。

### US-364: 导航与页面标题使用同一术语
- 故事：As a 任意 Web 用户, I want to 导航名称和页面标题叫法一致, so that 我能确信点进去的是同一个功能
- 关联需求：REQ-FUNC-379；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-364-01：Given 打开任意页面, When 读取侧边导航与页面 `h1`, Then "投票/调查""报销/备用金"在导航与标题中完全一致，斜杠两侧无空格。
- AC-364-02：Given 打开 `/units/appeal`, When 渲染, Then 导航项文本为「我的认证与申诉」，代码中不存在"申述"字符串。
- AC-364-03：Given 用户端与管理员同时可访问的"信息公开", When 分别在两端渲染, Then 两端 `h1` 文本一致（"信息公开"），不出现"信息公开"与"内容管理"以外的别名。

### US-365: 统一字号阶梯
- 故事：As a 设计/前端维护者, I want 全站使用同一套字号与字重阶梯, so that 新页面直接复用而不再逐页调样式
- 关联需求：REQ-FUNC-380；优先级：Must Have；故事点：5 [ESTIMATE]
- AC-365-01：Given 页面标题区, When 渲染, Then `.page-head h1` 计算字号为 24px、字重 700；窄屏（<768px）为 22px。
- AC-365-02：Given 任意卡片标题, When 渲染, Then 使用统一卡片标题类，字号 18px、字重 650；首页卡片标题同样为 18px（bento 主题不再单独放大到 20px）。
- AC-365-03：Given 页面内出现 `h2`/`h3`, When 渲染, Then 其字号来自阶梯（页面标题 24 / 卡片 18 / 分区 14），不出现浏览器默认字号。

### US-366: 一级/二级导航字体统一
- 故事：As a 任意 Web 用户, I want to 导航一级与二级菜单字号层级清晰且三套主题一致, so that 我切换主题后不会觉得导航忽大忽小
- 关联需求：REQ-FUNC-381、REQ-NFUNC-080；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-366-01：Given 切换 bento/neon/terminal 三套主题, When 读取生成的 CSS, Then `.side-item` 字号均为 15px、字重 600，主题样式中不存在覆盖为 16px/17px 的规则。
- AC-366-02：Given 展开任一二级菜单, When 渲染, Then `.side-sub-item` 与窄屏 `.sub-nav-item` 字号均为 13px、字重 500，且小于一级菜单。
- AC-366-03：Given terminal 主题, When 渲染中文导航与标题, Then 字体为 `--mono` 栈，但 `text-transform: uppercase` 与 0.06em 字距只作用于英文内容，中文标题宽度与 bento/neon 一致（误差 ≤ 2px）。

### US-367: 卡片标题统一
- 故事：As a 任意 Web 用户, I want to 所有卡片标题看起来是同一层级, so that 我不用猜哪块内容更重要
- 关联需求：REQ-FUNC-382；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-367-01：Given 首页信息卡与详情页卡片, When 渲染, Then 卡片标题均带统一卡片标题类，字号/字重/颜色一致。
- AC-367-02：Given 管理端页面, When 渲染, Then 不存在无类的 `h2` 作为卡片标题；原 6 处 `h2` 已替换为页面标题或卡片标题类。
- AC-367-03：Given terminal 主题, When 渲染卡片标题, Then 中文标题不被强制大写（视觉上无全角拉宽），字号仍为 18px。

### US-368: 管理端与用户端页面标题一致
- 故事：As a 管理员, I want to 管理端页面标题与用户端采用同一套规范, so that 我在两端之间切换时视觉连续
- 关联需求：REQ-FUNC-383；优先级：Must Have；故事点：3 [ESTIMATE]
- AC-368-01：Given 访问 `/admin/registry` 与 `/info`, When 渲染, Then 两页 `h1` 的字号、字重、上边距一致。
- AC-368-02：Given 管理端某页有多个区块（如财务页的"财务"与"金额上限"）, When 渲染, Then 只有页面标题为 `h1`，区块标题使用分区标题级 `h2`/`h3`，层级不颠倒。

### US-369: 详情页标题层级正确
- 故事：As a 任意 Web 用户, I want to 详情页把标题作为页面主标题, so that 长标题不会显示成卡片小标题或浏览器默认大标题
- 关联需求：REQ-FUNC-384；优先级：Should Have；故事点：2 [ESTIMATE]
- AC-369-01：Given 打开 `/resolutions/:id`、`/polls/:id`、`/info/:id`、报表详情, When 渲染, Then 实体标题为 `h1`（24px/700），元信息行使用辅助字号（12–13px）。
- AC-369-02：Given 标题长度 ≥ 40 个汉字, When 在 375px 宽视口渲染, Then 标题换行显示，页面无横向滚动条，`h1` 无 `text-overflow: ellipsis`。

## 汇总

| 优先级 | 故事数 | 故事点合计 |
|---|---|---|
| Must Have | 8 | 30 |
| Should Have | 1 | 2 |
| 合计 | 9 | 32 |
