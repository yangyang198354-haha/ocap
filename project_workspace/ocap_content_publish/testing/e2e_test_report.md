<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-11T13:32:21+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files><file>testing/test_plan.md（1.3.0）</file><file>requirements/user_stories.md</file><file>development/implementation_plan.md</file><file>testing/integration_test_report.md（1.2.0）</file></input_files>
  <phase>PHASE_09</phase>
  <status>APPROVED</status>
</file_header>

# E2E 测试报告（PHASE_09）— 1.2.0（回流 2：DEF-014~016 复测（GC-3 修复后））

## 摘要

critical path 口径：替代（完整 API 旅程 `backend/tests/e2e`；项目无浏览器 E2E 框架。前端调用的路径 / 方法由 `test_frontend_contract` 契约测试保证，前端关键交互由 vitest 组件用例保证）

- 执行时间：2026-11-11 13:28–13:31（Asia/Shanghai）；环境：Python 3.12.3 + Django 5.2.19 原样运行，SQLite 内存库，外部服务全部替身
- 范围：`backend/tests/e2e` 全量 33 个（基线 29，**新增 4**：TC-E2E-305~308；既有 301~304 保持）
- 命令：`(cd backend && python manage.py test tests.e2e --settings=config.test_settings)`

**metrics**：total = pass + fail + skip + blocked + not_testable = 33 = 33 + 0 + 0 + 0 + 0

通过率 = 33 / 33 = **100%**；critical path 覆盖率 = 24 / 24 = **100%**（Must Have 故事均被下表某条旅程实际执行，见“旅程覆盖”）；critical path 通过率 = **100%**（本层 33 个全部 PASS）

**本层门控：PASSED**——单元层（170/170）与集成层（342 PASS + 1 BLOCKED 数据缺失项）门控均 PASSED，本层 33/33 通过；既有用例新增失败 0；前后端契约由 `test_frontend_contract`（14 个）全部通过保证。DEF-014 的嵌套媒体前缀一致性由 TC-INT-388 守护（已 PASS）。

## 全量回归

| 命令 | 计数 | 相对基线新增失败（既有用例） |
|---|---|---|
| `(cd backend && python manage.py test --settings=config.test_settings)` | `Ran 519 tests in 32.361s` / `OK` | **0**（基线 430 + 新增 89 = 519；新写失败 0） |
| 分层 | unit 138（OK）、integration 342（OK）、e2e 33（OK）、smoke 6（OK）；138 + 342 + 33 + 6 = 519 | |
| `(cd frontend && npx vitest run --passWithNoTests)` | `Test Files  16 passed (16)` / `Tests  154 passed (154)` | **0**（基线 131 全部通过 + 新增 23） |
| `(cd miniprogram && npx vitest run --passWithNoTests)` | `Test Files  11 passed (11)` / `Tests  75 passed (75)` | **0**（基线 71 + 新增 4） |
| `(cd frontend && npm run build -- --base=/ocap/)` | `✓ built in 32.61s` | — |
| `(cd backend && python manage.py check …)` / `makemigrations --check --dry-run …` / `python -m compileall -q backend` | no issues / No changes detected / 无输出 | — |

相对基线：**既有用例新增失败 0**；新写用例失败 0（DEF-014/015/016 均已修复并复测通过；TC-UNIT-404 为过期用例，已更新）。Python 3.13 本机没有，**由 CI 验证**。

## 旅程覆盖（Must Have 故事 → 实际执行的 E2E 旅程）

| Must Have US | 旅程 | 说明 |
|---|---|---|
| US-105 | TC-E2E-301、305 | 创建 / 保存 / 发布（无审批） |
| US-106 | TC-E2E-301 | 下线后成员不可见 |
| US-107、US-108 | TC-E2E-301、305、306 | 门户 HTML、小程序 blocks 读取 |
| US-109 | TC-E2E-301、305、308 | 对齐 / 颜色 / 链接 / 粘贴来源颜色归一化 |
| US-110 | TC-E2E-308 | 基础格式清单全部项 保存无 warnings → 发布 → 渲染 |
| US-111 | TC-E2E-301、303、305 | 图片插入并显示 |
| US-112、US-113 | TC-E2E-301 | 自定义样式模板、分页 |
| US-114、US-115 | TC-E2E-302 | 文案生成、放入草稿 |
| US-116 | TC-E2E-304 | 文生图 |
| US-117 | TC-E2E-302 | 模型配置 + 连通测试 |
| US-119 | TC-E2E-301、303、306 | 上传 |
| US-120 | TC-E2E-304 | AI 素材入库 |
| US-121 | TC-E2E-303 | 复用 |
| US-123 | TC-E2E-306 | 上传视频→插入→发布→两端读取→签名地址 200 / Range 206 |
| US-124、US-125 | TC-E2E-304 | 视频生成（含视频服务配置） |
| US-126、US-127、US-128、US-130 | TC-E2E-302 | 账户、认证信息、一键保存（自动 + 人工）、导出内容包 |
| US-131 | TC-E2E-307 | 整条管理链路：未登录 401 / 游客 403 / 业主 403 且无写入；另一管理员同链路成功 |

注：E2E-302 以 `FakeDraftAdapter` 替换公众号适配器；**真实适配器 + 令牌服务 + `FakeWechatMpApi`** 的链路由 TC-INT-373~380 覆盖（集成层）。

## 用户旅程

### TC-E2E-301: 富文本 → 自定义样式 → 发布 → Web/小程序阅读 → 下线（既有）

- 关联：US-105/106/107/108/109/111/112/113/119；环境：API 级，SQLite
- 步骤与结果：创建自定义样式 → 含加粗 / 居中 / 图片 / 分页的正文 → 发布 → 成员 Web 详情 2 页、`text-align:center`、`font-size:20px`、`<img` → `fmt=blocks` src 以 `/content/media/` 开头、含 theme → 下线 → 成员 404 → **PASS**

### TC-E2E-302: 模型配置 → 生成文案 → 确认 → 一键保存（自动 + 人工）→ 内容包（既有）

- 关联：US-114/115/117/126/127/128/129/130
- 步骤与结果：保存 DeepSeek 密钥 → 测试连通 → 可选模型 1 个 → 文案任务 → 转文档 → 确认 → 发布 → 勾选公众号（替身 SAVED）+ 小红书（人工）→ 历史 SAVED / MANUAL_REQUIRED → 导出 ZIP 含生成文案 → **PASS**

### TC-E2E-303: 素材复用与删除保护（既有）

- 关联：US-119/121/122
- 步骤与结果：上传 → 复用到两条内容并发布 → 仍 1 条 → 删除被拒（列出内容标题）→ 下线一条仍拒绝 → 全部下线后删除成功 → **PASS**

### TC-E2E-304: AI 文生图与视频生成入库（既有）

- 关联：US-116/120/124/125
- 步骤与结果：配置图像 / 视频服务 → 文生图（替身 URL + 远程下载替身）→ 保存候选 → 确认文案 → 视频任务提交（Wait）→ 轮询完成 → 视频入库 AI_GENERATED → **PASS**

### TC-E2E-305: 编辑 → 保存（含 warnings）→ 发布 → 门户 / 小程序读取（新增，契约型 critical path）

- 关联：US-105/107/108/109/111；AC-107-04、AC-108-04、AC-109-01；环境：API 级
- 契约：请求体 `{title, doc, style_key}` 与 `AdminContentEditor.vue` 的 `admin.updateContentPost` 一致；响应字段 `doc / warnings[{block_index, reason, action}] / warning_total` 与前端 `warningsMessage()` 读取的字段一致

| 步骤 | 操作 | 期望响应 | 实际响应 | 结果 |
|---|---|---|---|---|
| 1 | 上传 PNG；创建内容：rgb(255,0,0) 文字、javascript: 链接、引用内图片、无 mediaId 外链图片 | 201；warnings 含 COLOR/NORMALIZED 与 LINK/DROPPED，均带 block_index，warning_total=len(warnings)；doc 不含 javascript，含 #ff0000 | 同期望 | PASS |
| 2 | PATCH 以规范化后的 doc 再保存并改标题 | 200，warnings=[]（规范化结果稳定） | 同期望 | PASS |
| 3 | 发布 | 200 | 同期望 | PASS |
| 4 | 成员读取门户 HTML | 不含 `javascript:`；含 `color:#ff0000`；“坏链接”文字保留；不含 evil.example；引用块内含 `<img` | 同期望 | PASS |
| 5 | 成员读取 `fmt=blocks` | 不含 `javascript:`；引用块 children 含 image，src 含 `/content/media/<id>/file?sig=` | 同期望（嵌套前缀一致性由 TC-INT-388 守护，已 PASS） | PASS |
| 6 | 成员列表 | 标题为改后的“热点公告（改）” | 同期望 | PASS |

- 结论：**PASS**

### TC-E2E-306: 上传视频 → 插入 → 发布 → 门户 / 小程序读取 → 播放地址（新增）

- 关联：US-123；AC-123-01、AC-123-02
- 步骤与结果：上传 mp4（VIDEO / UPLOAD）→ 含视频块的内容发布 → 门户 HTML 含 `<video` 与签名地址 → blocks 含 video（media_id、src 以 `/content/media/<id>/file?sig=` 开头）→ 无登录头取回签名地址 200、内容与原文件一致 → `Range: bytes=0-3` 返回 206 与前 4 字节 → **PASS**

### TC-E2E-307: 仅管理员可管理（新增）

- 关联：US-131；AC-131-01~03
- 步骤与结果：对 8 种管理操作（建稿、改稿、发布、删除、服务配置、建平台账户、AI 文案、导出内容包）分别用未登录（期望 401）、游客（403）、业主（403）发起 → 全部符合，且内容 / 素材 / 平台账户 / 系统配置计数前后不变，原稿标题未被篡改 → 另一管理员账号同链路（建稿、发布、服务配置、平台账户）全部成功，成员可读 `/info/posts` → **PASS**

### TC-E2E-308: 基础格式清单经保存、发布、渲染全部保持（新增）

- 关联：US-110、US-109；AC-110-01、AC-109-01
- 步骤与结果：创建含 标题 1 / 4、加粗 + 斜体 + 下划线 + 删除线、右对齐 + 文字色 + 背景色 + 字号 + 行距、超链接、无序 / 有序列表、引用、分割线、分页 的内容 → 201 且 warnings=[] → 发布 → 门户 page_count=2，第 1 页包含 `<h1>`、`<h4>`、`font-weight:700;font-style:italic;text-decoration:underline line-through`（合并为一个 text-decoration）、`text-align:right`、`color:#ff0000`、`background-color:#ffff00`、`font-size:20px`、`line-height:1.5`、`href`、`<ul><li>`、`<ol><li>`、`<blockquote`、`<hr`，第 2 页含“第二页”，无 `<table` → **PASS**

## 缺陷

| DEF | 级别 | 现象 | 复现用例 | 疑似位置 |
|---|---|---|---|---|
无未关闭缺陷。已修复并复测：

| DEF | 级别 | 现象 | 复测用例 | 结果 |
|---|---|---|---|---|
| DEF-014 | MAJOR | `fmt=blocks` 嵌套媒体 src 保留 `/api/v1` 前缀 | TC-INT-388 | 已修复，PASS |
| DEF-015 | MINOR | 链接对话框网址为空时未提示“网址无效”（AC-109-03） | TC-UNIT-393 | 已修复，PASS |
| DEF-016 | MINOR | 未选平台时“开始保存”禁用且无提示（AC-128-04） | TC-UNIT-404（更新） | 已修复，PASS |

## 人工验证清单

自动化无法覆盖（无浏览器 E2E 框架 / 不得调用真实平台）的部分，部署后在测试环境人工核对：

| 编号 | 对应 AC / TC | 步骤 | 期望结果 | 所需设备或环境 | 是否 critical path |
|---|---|---|---|---|---|
| M-01 | AC-107-01、AC-109-01/02/04、AC-110-01 | 在管理端编辑器实际设置对齐 / 颜色 / 链接，回车分段，预览中点击链接 | 视觉与公众号编辑页等价；点击跳转到所设地址；保存后重新打开回显一致 | 浏览器（Chrome / Edge） | 否（逻辑已由 TC-UNIT-383~392、TC-E2E-305/308 覆盖） |
| M-02 | AC-107-03、AC-108-03、AC-131-04 | 未登录访问门户 / 小程序信息公开；用业主 / 游客账号查看门户与小程序界面 | 跳转登录页 / 引导登录；界面无任何管理入口 | 浏览器 + 微信开发者工具 | 否 |
| M-03 | AC-113-01/02 | 在门户和小程序阅读含分页标记的长内容 | 出现页码或“下一页 / 上一页”控件，位置与分页标记一致；单页内容无控件 | 浏览器 + 微信开发者工具 | 否 |
| M-04 | AC-127-03、AC-128-01 | 用真实公众号 AppID / AppSecret 一键保存；把本服务器出口 IP 加入白名单前后各试一次；故意填错 AppSecret；记录微信返回的 errcode | 白名单前提示“服务器出口 IP 未加入公众号 IP 白名单”；错误 AppSecret 的真实 errcode 若加入 `auth_errcodes` 后账户被标“失效”；草稿箱出现内容。**并核对封面 / 正文图片上传**：TC-INT-395 BLOCKED，`[DATA_REQUIRED: 微信官方文档]`（端点、字段、限制），开关缺省关闭 | 真实公众号账号与 IP 白名单权限；官方文档 | 否（上线前必验） |
| M-05 | AC-114-01、AC-116-01、AC-124-02/03 | 配置真实 DeepSeek / 火山方舟 / 即梦账号并各发起一次 | 成功入库；失败显示原因；密钥不回显 | 各服务账号与额度 | 否 |
| M-06 | AC-108-01、AC-123-01 | 小程序真机查看含图片 / 视频（含引用内媒体，DEF-014 已修复，仍需真机确认）的信息公开 | 图片 / 视频显示与播放，链接复制提示 | 微信开发者工具 / 真机 | 否 |
| M-07 | AC-130-03、AC-116-01 | 内容包页点击“一键复制”；AI 配图结果区点击“插入” | 剪贴板含正文并提示“已复制”；图片插入光标处 | 浏览器 | 否 |
