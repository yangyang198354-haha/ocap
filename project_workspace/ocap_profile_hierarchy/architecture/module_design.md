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
    <file>backend/apps/accounts/views.py</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：个人主页信息层级与实名认证徽章

## 模块总览

| MOD | 名称 | 文件（新建/修改） | 职责 | 覆盖需求/US | 依赖 |
|---|---|---|---|---|---|
| MOD-164 | Web 个人主页展示层级 | `frontend/src/portal/UserProfile.vue`（修改） | 重排“昵称 → 实名+徽章 → 身份”，增加实名徽章与样式区分 | REQ-FUNC-264/265/266/267；US-273/274/275 | IFC-378 |
| MOD-165 | 小程序“我的”页展示层级 | `miniprogram/pages/me/index.vue`（修改） | 调用本人 profile 获取实名、重排展示、增加徽章与失败降级 | REQ-FUNC-268；US-276 | IFC-377 |
| MOD-166 | Web 展示契约测试 | `frontend/tests/profile_ux.spec.js`（修改） | 覆盖顺序、徽章存在性、颜色/字体差异、无实名降级 | US-273/274/275 | MOD-164 |
| MOD-167 | 小程序“我的”页测试 | `miniprogram/tests/pages.spec.js`（修改） | 覆盖顺序、徽章、无实名与请求失败降级 | US-276 | MOD-165 |

## 模块详情

### MOD-164 Web 个人主页展示层级（修改）

- 文件：`frontend/src/portal/UserProfile.vue`。
- 展示结构（数据来自既有 `profile` 对象，不新增字段）：
  1. 头像（`AuthImage`，沿用）。
  2. 主标题：`profile.nickname || '未设置昵称'`，沿用 `h3.title`。
  3. 实名行：仅当 `profile.real_name` 非空时渲染；文本 `实名：{profile.real_name}`，紧随一个认证徽章。
  4. 身份行：`el-tag`（`type="info"`，`size="small"`），文案 `profile.identity?.label || '游客'`。
  5. 签名档与编辑入口不变。
- DOM/样式契约（IFC-379）：
  - `.profile-meta` 内元素顺序：`h3.profile-name` → `.real-name`（含 `.verified-badge`）→ `.identity-tag`。
  - `.real-name`：`color: var(--text)`，`font-weight: 650`，`font-size: 14px`。
  - `.verified-badge`：`el-tag`，`type="success"`、`effect="plain"`、`size="small"`，文案 `✓ 已实名认证`。
  - `.identity-tag`：`el-tag type="info"`，默认 12px；不得带 `.real-name` 的字重。
  - 容器允许换行（`flex-wrap: wrap`），窄屏下实名行可换至下一行，不改变顺序。
- 鉴权：页面由既有路由守卫控制；数据来自 `meApi.userProfile`，后端 `IsMember`。
- 输入校验：本模块不接收用户输入；`profile.real_name` 按后端白名单原样展示，不做本地拼接。

### MOD-165 小程序“我的”页展示层级（修改）

- 文件：`miniprogram/pages/me/index.vue`。
- 数据：`load()` 中在 `auth.fetchMe()` 与 `api.housing()` 之外，调用既有 `api.profile()`（`GET /me/profile`，IFC-377），独立 try/catch：
  - 成功：记录 `realName = data.real_name || ''`。
  - 失败：`realName = ''`，不弹提示（AC-276-03）。
- 展示顺序（在“我的”卡片的第二个卡片内）：
  1. 昵称：`auth.me?.profile?.nickname || '业主'`，沿用 `.title`。
  2. 实名行：仅 `realName` 非空时渲染；`view.real-name` 文本 `实名：{realName}`，后接 `view.tag.is-success` 徽章 `✓ 已实名认证`。
  3. 身份行：`view.tag`（muted）文案 `{identitySummary.label}`，不再使用“身份：”前缀拼接在同一行。
  4. 房屋列表与手机号顺序不变。
- 样式契约（IFC-380）：
  - `.real-name`：`color: var(--text)`、`font-weight: 650`、`font-size: 26rpx`。
  - 身份 `.tag` 保持 `var(--muted)`、22rpx；认证徽章 `.tag.is-success` 继承全局 success 语义色（`miniprogram/App.vue:23`）。
  - 主信息容器 `display:flex; flex-wrap:wrap; align-items:center; gap:8rpx`，允许窄屏换行。
- 鉴权：`api.profile()` 使用既有 token；未登录由 `http` 统一跳转。
- 输入校验：无用户输入；服务端已按 `real_name_visible` 决定是否返回实名，客户端不推断。

### MOD-166 / MOD-167 测试

- MOD-166：在 `frontend/tests/profile_ux.spec.js` 增加 TC-UNIT-1509（实名可见：顺序与徽章、身份样式不同）、TC-UNIT-1510（`real_name: null` 时不渲染实名与徽章）。
- MOD-167：在 `miniprogram/tests/pages.spec.js` 增加 TC-UNIT-1511（实名可见顺序与徽章）、TC-UNIT-1512（`api.profile()` reject 时无实名/徽章且页面正常）。
- 测试路径遵守画像 P3。

## 接口契约

### IFC-377（沿用）`GET /api/v1/me/profile`

- 方法/路径：`GET /api/v1/me/profile`。
- 鉴权：登录成员（`IsMember`），Bearer token。
- 响应字段（本次使用）：`real_name: string | null`、`real_name_visible: boolean`、`can_show_real_name: boolean`；其余字段不变。
- 错误：401 未登录（既有统一错误体）。
- 消费方：小程序 MOD-165（新增调用）；Web 本人资料页沿用。

### IFC-378（沿用）`GET /api/v1/users/{user_id}/profile`

- 方法/路径：`GET /api/v1/users/{user_id}/profile`。
- 鉴权：登录成员（`IsMember`）。
- 响应字段（本次使用）：`nickname: string`、`avatar_url: string | null`、`identity: {code: string, label: string}`、`real_name: string | null`、`signature: string`、`is_self: boolean`；白名单不变。
- 消费方：Web MOD-164。

### IFC-379（前端展示契约）Web 个人主页 DOM

- 顺序：`h3.profile-name` → `.real-name`（可选，内含 `.verified-badge`）→ `.identity-tag`。
- 约束：`.real-name` 与 `.identity-tag` 的文字颜色不同，字重或字号至少一项不同。
- 校验：测试以 `wrapper.findAll` 的元素索引与计算样式（jsdom 可读 class/CSS）断言。

### IFC-380（前端展示契约）小程序“我的”页

- 顺序：`.title`（昵称）→ `.real-name`（可选）→ `.tag`（身份）。
- 约束：`.real-name` 非空时才渲染 `.tag.is-success` 徽章；`api.profile()` 失败时两者均不渲染。
- 校验：组件测试挂载页面，断言元素顺序与文本。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-264 | US-273、US-276 | MOD-164、MOD-165 |
| REQ-FUNC-265 | US-274、US-276 | MOD-164、MOD-165 |
| REQ-FUNC-266 | US-275 | MOD-164、MOD-165 |
| REQ-FUNC-267 | US-273、US-274、US-275 | MOD-164 |
| REQ-FUNC-268 | US-276 | MOD-165 |

## 依赖关系

- MOD-164 → IFC-378（读取公开 profile）。
- MOD-165 → IFC-377（读取本人 profile）。
- MOD-166 → MOD-164（测试覆盖）。
- MOD-167 → MOD-165（测试覆盖）。

已检查：无循环依赖。

## 数据迁移

无。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 操作 |
|---|---|---|
| Web 前端 | `UserProfile.vue` 改动 | `npm run build` 后发布静态产物，需刷新浏览器缓存 |
| 微信小程序 | “我的”页改动 | `uni build -p mp-weixin` 重新构建并在微信开发者工具验证/上传 |
| 后端 API | 无代码改动 | 不重启 |
| 定时任务 | 无 | 不涉及 |

## 领域与外部依赖出处

不适用（画像 P11 为无）。
