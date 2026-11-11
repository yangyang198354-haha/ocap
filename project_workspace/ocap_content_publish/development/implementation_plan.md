<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T13:20:58+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>3.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/architecture_design.md</file><file>architecture/module_design.md</file><file>architecture/tech_stack.md</file><file>development/implementation_plan.md (1.0.0 APPROVED，被本版本返工)</file><file>phase_status.md (GR-C-002、GR-B-002)</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：信息公开与多平台内容中心（GROUP_C，返工 1.1.0）

## 实现概览

- 触发：GR-C-002 FAIL，用户 2026-11-11 "1. 返工，2. B"，`REWORK_AUTHORIZED`；依据 architecture 2.0.0（ADR-060~063、module_design"1.1.0 修订"）。
- 范围：F01~F05、F06（按用户选 B，ADR-060 全量实现；ADR-061 仅签名/stub/关闭的开关）、F07。MOD-062、MOD-063 新建；MOD-039/040 外的 MOD-041/042/044/045/046/049/050/052/053/056/057/059/061 修改。
- 拓扑顺序（被依赖的先实现）：MOD-056/041/039 → MOD-042 → MOD-044 → MOD-046 → MOD-063 → MOD-062 → MOD-049/050 → MOD-045 → MOD-052/053 → MOD-054/057 → MOD-059/061（前端/小程序）。
- 文件：后端新建 3、修改 18；前端新建 3、修改 5；小程序修改 1。不改 `backend/apps/registry`（工作区既有未提交改动保持原样）。
- ADR-061（封面、正文图片上传、视频嵌入）阻塞于用户提供微信官方文档（Q-B1）：只写签名、`TODO(IFC-239): [UNSOURCED]` stub 与缺省关闭的开关（`upload_cover`/`upload_content_images`/`require_cover` = false）；`auth_errcodes`、`token_errcodes` 缺省保持 `[]`；未联网搜索。

## 改动清单（按拓扑顺序）

| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-056 | backend/apps/core/audit.py | 修改 | — | L | `AUDIT_ACTIONS` 增 `CONTENT_PLATFORM_AUTH_EXPIRED`（共 13 项） | DONE |
| 2 | MOD-039 | backend/apps/content/models.py；migrations/0002_platformaccount_token_cache.py | 修改+新建 | — | M | `PlatformAccount` 增 token_blob/token_expires_at/token_refreshed_at/token_lock_until（可空）；0002 手写 4×AddField + 可选 RunPython（旧公众号账户置 UNSET，只读 secret_keys）；反向 noop | DONE |
| 3 | MOD-041 | backend/apps/content/conf.py | 修改 | — | L | 新增 7 项参数：ip_errcodes（缺省 [40164]）、token_errcodes（[]）、token_margin_seconds（300）、refresh_cooldown_seconds（60）、upload_cover/upload_content_images/require_cover（false）；errcode 清单统一校验 1~999999、≤50 项 | DONE |
| 4 | MOD-042 | backend/apps/content/richtext/{schema,render,convert,__init__}.py | 修改 | — | H | 宽容模式 `validate_doc_ex` + `normalize_color` + `ValidationResult`；严格模式 `validate_doc` 行为不变；`DocValidationError` 增 block_index/block_type；渲染：块级行距、引用/列表内任意深度媒体、下划线+删除线合并；`extract_paragraphs` | DONE |
| 5 | MOD-044 | backend/apps/content/media.py | 修改 | MOD-056 | M | **F01** `list`→`list_items`；`delete(media_id, *, admin)` 同事务写 `CONTENT_MEDIA_DELETED`、文件 on_commit 删除；新增 `discard` 供视频失败回收 | DONE |
| 6 | MOD-046 | backend/apps/content/jobs.py | 修改 | — | L | `JobContext.heartbeat` 以当前时间续租 | DONE |
| 7 | MOD-063 | backend/apps/integrations/wechat_mp.py | 新建 | MOD-040 | M | `WechatMpApi` Protocol、`HttpWechatMpApi`（取令牌 [CODE: wechat.py:97-103]、draft/add [P11: publishers.py:76-87]）、`upload_cover/upload_content_image` 仅签名（抛 NotImplementedError，`TODO(IFC-239): [UNSOURCED]`）、`get_/set_` 注入点；异常只用脱敏文本 | DONE |
| 8 | MOD-062 | backend/apps/content/wechat_token.py | 新建 | MOD-039/040/041/063 | H | `WechatTokenService.get_token/get_token_ex/invalidate/classify`：加密缓存、提前量、条件 UPDATE 单飞锁（等待 ≤10s 后 TOKEN_BUSY）、冷却、强制刷新、失败分类、finally 释放锁、凭据被覆盖时丢弃结果 | DONE |
| 9 | MOD-049 | backend/apps/integrations/draft.py | 修改 | MOD-062/063 | H | 公众号适配器重写：凭据 appid/appsecret；令牌错误（HTTP 401/403、token_errcodes、空配置时的保守兜底）强制刷新重发至多一次；NETWORK 不重发；IP 白名单单独分类；开关关闭时不触发封面/图片上传；`DraftPayload` 增 html_for/cover；`save_draft` 增 `account_id` | DONE |
| 10 | MOD-050 | backend/apps/integrations/fakes.py | 修改 | MOD-049/063 | M | 新增 `FakeWechatMpApi`；`FakeDraftAdapter.save_draft` 增 `account_id` 并记录 `received_account_ids` | DONE |
| 11 | MOD-045 | backend/apps/content/posts.py | 修改 | MOD-042 | M | `_validate_doc` 改宽容模式并带 block_index/block_type；`create/update` 返回 `(post, warnings, warning_total)`；`render_preview` 返回 warnings；`UNTITLED_PLACEHOLDER` 发布视为缺标题 | DONE |
| 12 | MOD-052 | backend/apps/content/ai_jobs.py | 修改 | MOD-042/044 | M | `build_scenes` 按段落列表；`submit_video` 用 `extract_paragraphs`；视频片段先 CANDIDATE 全部成功后统一转 SAVED，失败回收并 `Fail("DOWNLOAD_FAILED")`，每片段前 heartbeat | DONE |
| 13 | MOD-053 | backend/apps/content/{platforms,drafts,export_pack}.py | 修改 | MOD-049/062 | H | 账户：appid/appsecret 校验、凭据覆盖时 invalidate、`mark_expired` 仅 NORMAL→EXPIRED 并写审计；批次：start_batch 事务内、无自动行直接 `audit_batch`、payload 带 batch_id；`audit_batch` 幂等汇总全部行；handler 传 account_id、逐行 heartbeat、AUTH_EXPIRED 标失效、结束/中断写批次审计；导出改匿名临时文件 | DONE |
| 14 | MOD-054 | backend/apps/content/views_admin.py | 修改 | MOD-044/045 | L | `list_items`、`delete(admin=…)`、create/update 响应附加 warnings/warning_total | DONE |
| 15 | MOD-057 | backend/apps/content/management/commands/run_content_worker.py | 修改 | MOD-046 | L | 移除 `--concurrency`；JobRun 心跳至多每 60 秒（单调时钟）+ 启停各一次 | DONE |
| 16 | MOD-059 | frontend/src/admin/editor/{colors,pasteGuard,contentText}.js（新）、RichEditor.vue、Toolbar.vue、extensions/Video.js、AdminContentEditor.vue、AdminPlatforms.vue | 新建+修改 | MOD-058 | H | 取色器、粘贴守卫、heading 1–4、颜色解析归一化、warnings/400 定位提示、保存失败中止发布/确认、revokeObjectURL 延后、推送结果中文状态、平台页 AppID/AppSecret 与 IP 白名单提示 | DONE |
| 17 | MOD-061 | miniprogram/components/RichBlocks.vue | 修改 | — | L | 块级行距；下划线+删除线合并（列表/引用内媒体由后端补 src 后经递归组件渲染） | DONE |
| 18 | MOD-058 | frontend/src/shared/api.js、miniprogram/utils/api.js | 不变 | — | — | 本次无新增/变更 API 路径，契约测试无需改动 | DONE |

## 需求追溯

标注 **[1.1.0]** 的为本次改动涉及的 AC；其余沿用 1.0.0 实现（位置按函数/组件级给出，已复核仍存在）。

| US | AC | 实现位置（文件:函数/组件，含客户端） | 状态 | 说明 |
|---|---|---|---|---|
| US-105 | AC-105-01 | content/views_admin.py:PostListView.post → posts.py:PostService.create；AdminContentPosts.vue:创建 | DONE | **[1.1.0]** 创建响应附加 warnings |
| US-105 | AC-105-02 | views_admin.py:PostDetailView.patch → PostService.update；AdminContentEditor.vue:saveDraft | DONE | **[1.1.0]** saveDraft 返回成败，失败提示带位置 |
| US-105 | AC-105-03 | posts.py:PostService.publish（`UNTITLED_PLACEHOLDER`）；AdminContentEditor.vue:publish | DONE | **[1.1.0]** 默认标题"未命名内容"发布时视为缺标题；保存失败不再继续发布（F02） |
| US-106 | AC-106-01 | posts.py:PostService.publish；views_admin.py:PostPublishView；AdminContentPosts.vue | DONE | 沿用 |
| US-106 | AC-106-02 | posts.py:PostService.offline；PostOfflineView；AdminContentPosts.vue | DONE | 沿用 |
| US-106 | AC-106-03 | posts.py:PostService.delete；PostDetailView.delete；AdminContentPosts.vue | DONE | 沿用 |
| US-106 | AC-106-04 | posts.py:PostService.update（PUBLISHED 写 CONTENT_POST_UPDATED）；AdminContentEditor.vue:saveDraft | DONE | 沿用 |
| US-107 | AC-107-01 | posts.py:PostService.render_for_member；views_member.py:InfoListView/InfoDetailView；portal/InfoList.vue、InfoDetail.vue | DONE | 沿用 |
| US-107 | AC-107-02 | richtext/render.py:render_html/_block_html；InfoDetail.vue | DONE | **[1.1.0]** 块级行距、下划线+删除线合并为单个 text-decoration |
| US-107 | AC-107-03 | richtext/render.py:_resolve_media（任意深度）/_block_html image、video；InfoDetail.vue | DONE | **[1.1.0]** 引用/列表内图片视频完整渲染，素材缺失原位提示 |
| US-107 | AC-107-04 | richtext/paginate.py:paginate；richtext/convert.py:render_pages；InfoDetail.vue | DONE | 沿用 |
| US-108 | AC-108-01 | views_member.py:InfoDetailView（fmt=blocks）；miniprogram/pages/info/{index,detail}.vue | DONE | 沿用 |
| US-108 | AC-108-02 | richtext/render.py:render_blocks；miniprogram/components/RichBlocks.vue:blockStyle/inlineStyle | DONE | **[1.1.0]** `Block.lh` 行距；下划线+删除线合并 |
| US-108 | AC-108-03 | richtext/render.py:_resolve_media；RichBlocks.vue（递归 `<rich-blocks>` 渲染 image/video 的 src） | DONE | **[1.1.0]** 列表/引用内 image/video 块现带 src |
| US-108 | AC-108-04 | richtext/paginate.py；miniprogram/pages/info/detail.vue | DONE | 沿用 |
| US-109 | AC-109-01 | richtext/schema.py:_norm_node；editor/RichEditor.vue（StarterKit）、Toolbar.vue | DONE | **[1.1.0]** 标题限 1–4 级（`heading.levels`），服务端 >4 钳为 4 并提示 |
| US-109 | AC-109-02 | richtext/schema.py:_norm_marks；Toolbar.vue:run | DONE | 沿用 |
| US-109 | AC-109-03 | schema.py:_norm_marks(link)；RichEditor.vue:requestLink | DONE | **[1.1.0]** 非法链接在宽容模式丢弃标记并 warning（javascript: 仍不进入输出） |
| US-109 | AC-109-04 | RichEditor.vue:clearFormat；Toolbar.vue | DONE | 沿用 |
| US-110 | AC-110-01 | schema.py:normalize_color/_norm_marks(textStyle)；Toolbar.vue:setColor/setBackground（`el-color-picker`）；colors.js:toHexColor | DONE | **[1.1.0]** 取色器替换文本框；rgb()/rgba()→#hex；非法颜色丢弃 |
| US-110 | AC-110-02 | schema.py:_norm_marks(fontSize/lineHeight)；Toolbar.vue:setFontSize/setLineHeight | DONE | **[1.1.0]** 越界属性丢弃并提示（不再整篇 400） |
| US-110 | AC-110-03 | schema.py:_norm_node(textAlign)；Toolbar.vue:run('setTextAlign') | DONE | 沿用 |
| US-110 | AC-110-04 | schema.py:ALLOWED_TYPES（无表格/公式）；RichEditor.vue extensions | DONE | **[1.1.0]** 粘贴守卫 `pasteGuard.js:guardPastedHtml` 去脚本/外链图片/外部视频 |
| US-111 | AC-111-01 | media.py:MediaService.upload；editor/MediaPicker.vue；RichEditor.vue:insertMedia | DONE | 沿用 |
| US-111 | AC-111-02 | posts.py:PostService._sync_media；RichEditor.vue | DONE | 沿用 |
| US-111 | AC-111-03 | schema.py:_norm_node(image/video，无有效 mediaId 丢弃)；pasteGuard.js | DONE | **[1.1.0]** 外链/data: 图片丢弃并提示，不转存 |
| US-112 | AC-112-01 | styles.py:StyleService.list_all/resolve_tokens；AdminContentEditor.vue(styleKey) | DONE | 沿用 |
| US-112 | AC-112-02 | posts.py:PostService.render_preview；AdminContentEditor.vue:preview | DONE | **[1.1.0]** 预览返回/展示 warnings |
| US-112 | AC-112-03 | styles.py:StyleService.create/update/delete | DONE | 沿用 |
| US-112 | AC-112-04 | styles.py:StyleService.create（STYLE_NAME_REQUIRED/EXISTS） | DONE | 沿用 |
| US-113 | AC-113-01 | richtext/paginate.py:paginate | DONE | 沿用 |
| US-113 | AC-113-02 | richtext/convert.py:render_pages；InfoDetail.vue；pages/info/detail.vue | DONE | 沿用 |
| US-113 | AC-113-03 | paginate.py（pageBreak） | DONE | 沿用 |
| US-113 | AC-113-04 | InfoDetail.vue（page_count=1 不显示翻页） | DONE | 沿用 |
| US-114 | AC-114-01 | ai_jobs.py:AiGenerationService.submit_text；AdminContentEditor.vue:generateText | DONE | 沿用 |
| US-114 | AC-114-02 | ai_jobs.py:TextJobHandler.run；AdminContentEditor.vue:poll | DONE | 沿用 |
| US-114 | AC-114-03 | ai_jobs.py:compose_messages/_params | DONE | 沿用 |
| US-114 | AC-114-04 | ai_jobs.py:_limit；services_config.py:resolve_llm | DONE | 沿用 |
| US-114 | AC-114-05 | ai_jobs.py:TextJobHandler.run（LlmError→Fail） | DONE | 沿用 |
| US-115 | AC-115-01 | posts.py:PostService.confirm_text；PostConfirmView；AdminContentEditor.vue:confirmText | DONE | **[1.1.0]** 保存失败即中止确认（F02） |
| US-115 | AC-115-02 | posts.py:PostService.is_text_confirmed | DONE | 沿用（`render_text` 输出未改，确认哈希保持有效） |
| US-115 | AC-115-03 | posts.py:PostService.is_confirmed；drafts.py:start_batch（POST_NOT_CONFIRMED） | DONE | 沿用 |
| US-116 | AC-116-01 | ai_jobs.py:submit_image | DONE | 沿用 |
| US-116 | AC-116-02 | ai_jobs.py:ImageJobHandler.run | DONE | 沿用 |
| US-116 | AC-116-03 | media.py:MediaService.save_candidate；MediaSaveView | DONE | 沿用 |
| US-116 | AC-116-04 | media.py:MediaService.housekeeping | DONE | 沿用 |
| US-117 | AC-117-01 | services_config.py:ServiceConfigService.list_all；AdminAiServices.vue | DONE | 沿用 |
| US-117 | AC-117-02 | services_config.py:save（secrets 覆盖式、只写不读） | DONE | 沿用 |
| US-117 | AC-117-03 | vault.py:CredentialVault.encrypt | DONE | 沿用 |
| US-117 | AC-117-04 | services_config.py:save（审计 CONTENT_SERVICE_CONFIG_CHANGED） | DONE | 沿用 |
| US-117 | AC-117-05 | services_config.py:save（MISSING_FIELDS） | DONE | 沿用 |
| US-118 | AC-118-01 | services_config.py:test；ServiceTestView | DONE | 沿用 |
| US-118 | AC-118-02 | services_config.py:llm_options | DONE | 沿用 |
| US-118 | AC-118-03 | services_config.py:resolve_llm | DONE | 沿用 |
| US-118 | AC-118-04 | services_config.py:test（审计 CONTENT_SERVICE_TESTED） | DONE | 沿用 |
| US-119 | AC-119-01 | media.py:MediaService.upload/_store；MediaListView.post | DONE | 沿用 |
| US-119 | AC-119-02 | media.py:_store（魔数/大小/配额） | DONE | 沿用 |
| US-119 | AC-119-03 | media.py:MediaService.list_items；MediaListView.get；AdminMedia.vue | DONE | **[1.1.0]** F01：`list`→`list_items`，Python 3.12 可导入 |
| US-119 | AC-119-04 | media.py:MediaService.rename；MediaDetailView.patch | DONE | 沿用 |
| US-120 | AC-120-01 | ai_jobs.py:ImageJobHandler.run → MediaService.store_stream(CANDIDATE) | DONE | 沿用 |
| US-120 | AC-120-02 | MediaService.save_candidate；AdminContentEditor.vue:saveCandidate | DONE | 沿用 |
| US-120 | AC-120-03 | ai_jobs.py:VideoJobHandler.run（片段统一转 SAVED） | DONE | **[1.1.0]** 全成功才入库 |
| US-121 | AC-121-01 | editor/MediaPicker.vue | DONE | 沿用 |
| US-121 | AC-121-02 | posts.py:_sync_media | DONE | 沿用 |
| US-121 | AC-121-03 | media.py:MediaService.published_usage | DONE | 沿用 |
| US-122 | AC-122-01 | media.py:MediaService.published_usage；media_out.in_use | DONE | 沿用 |
| US-122 | AC-122-02 | media.py:MediaService.delete（MEDIA_IN_USE，不写审计） | DONE | 沿用 |
| US-122 | AC-122-03 | media.py:MediaService.delete（`transaction.atomic` 内 `AuditService.record(CONTENT_MEDIA_DELETED)`，文件 `on_commit` 删除）；MediaDetailView.delete | DONE | **[1.1.0]** F03 补审计 |
| US-122 | AC-122-04 | media.py:delete（引用关系清理） | DONE | 沿用 |
| US-122 | AC-122-05 | AdminMedia.vue（拒绝提示） | DONE | 沿用 |
| US-123 | AC-123-01 | RichEditor.vue:insertMedia(video)；extensions/Video.js | DONE | **[1.1.0]** Video 节点 mediaId/src 可从 HTML 回读 |
| US-123 | AC-123-02 | schema.py:_norm_node(video) | DONE | 沿用 |
| US-123 | AC-123-03 | render.py:_block_html(video) | DONE | **[1.1.0]** 任意深度渲染 |
| US-124 | AC-124-01 | ai_jobs.py:submit_video | DONE | **[1.1.0]** 分镜按文档段落（`extract_paragraphs`） |
| US-124 | AC-124-02 | ai_jobs.py:AiGenerationService.build_scenes | DONE | **[1.1.0]** 入参改为段落列表，空→POST_INCOMPLETE |
| US-124 | AC-124-03 | ai_jobs.py:VideoJobHandler.run（SUBMITTING/POLLING） | DONE | 沿用 |
| US-124 | AC-124-04 | ai_jobs.py:VideoJobHandler.run（下载、DOWNLOAD_FAILED、回收） | DONE | **[1.1.0]** 全有或全无；片段前 `ctx.heartbeat()` |
| US-124 | AC-124-05 | jobs.py:JobContext.heartbeat；run_content_worker.py | DONE | **[1.1.0]** 心跳用当前时间续租；worker 单线程、JobRun 60 秒 |
| US-124 | AC-124-06 | ai_jobs.py:submit_video / VideoJobHandler.run（CONTENT_VIDEO_REQUESTED/COMPLETED） | DONE | 沿用 |
| US-124 | AC-124-07 | jobs.py:requeue_expired（视频 on_interrupted） | DONE | 沿用 |
| US-125 | AC-125-01 | services_config.py:secrets_for；vault.py | DONE | 沿用 |
| US-125 | AC-125-02 | vault.py:SecretRedactor | DONE | 沿用 |
| US-125 | AC-125-03 | services_config.py:_out（无凭据字段） | DONE | 沿用 |
| US-126 | AC-126-01 | platforms.py:PlatformAccountService.create；PlatformListView；AdminPlatforms.vue | DONE | 沿用 |
| US-126 | AC-126-02 | platforms.py:create（PLATFORM_ACCOUNT_EXISTS） | DONE | 沿用 |
| US-126 | AC-126-03 | platforms.py:update/delete（审计 CONTENT_PLATFORM_ACCOUNT_CHANGED） | DONE | **[1.1.0]** update 只写改动列 |
| US-126 | AC-126-04 | platforms.py:list_platforms | DONE | 沿用 |
| US-127 | AC-127-01 | platforms.py:_validate_credentials（appid/appsecret）/create；draft.py:WechatMpDraftAdapter.credential_fields；AdminPlatforms.vue | DONE | **[1.1.0]** 凭据字段改 AppID/AppSecret（ADR-060） |
| US-127 | AC-127-02 | platforms.py:_out（secret_saved，不回显）；wechat_token.py:_store（令牌加密落库） | DONE | **[1.1.0]** 令牌缓存加密，序列化器不输出 token_* |
| US-127 | AC-127-03 | wechat_token.py:WechatTokenService.classify/get_token_ex；draft.py:_token_failure；drafts.py:DraftPushHandler.run → platforms.py:mark_expired | DONE | **[1.1.0]** 取令牌 errcode∈auth_errcodes→AUTH_EXPIRED→标 EXPIRED 并写 `CONTENT_PLATFORM_AUTH_EXPIRED`；**auth_errcodes 缺省 `[]`（[UNSOURCED]，Q-B1），真实环境不会自动触发**，仅替身可验 |
| US-127 | AC-127-04 | platforms.py:update（凭据覆盖→NORMAL，invalidate 令牌） | DONE | **[1.1.0]** |
| US-127 | AC-127-05 | AdminPlatforms.vue（无"检测有效性"按钮，页面提示 IP 白名单） | DONE | **[1.1.0]** |
| US-128 | AC-128-01 | drafts.py:DraftPushService.start_batch/build_payload；draft.py:WechatMpDraftAdapter.save_draft；AdminContentEditor.vue:pushDrafts | DONE | **[1.1.0]** 公众号经令牌服务调用 draft/add；封面/图片上传 **未实现（ADR-061，Q-B1）** |
| US-128 | AC-128-02 | drafts.py:start_batch（MANUAL/NO_CREDENTIALS 行） | DONE | 沿用 |
| US-128 | AC-128-03 | drafts.py:DraftPushHandler.run（平台间隔离） | DONE | **[1.1.0]** 逐行 heartbeat |
| US-128 | AC-128-04 | drafts.py:DraftPushHandler.on_interrupted（UNKNOWN） | DONE | **[1.1.0]** 中断后同样写批次审计 |
| US-128 | AC-128-05 | drafts.py:retry | DONE | **[1.1.0]** 重试自成新批次 |
| US-128 | AC-128-06 | AdminContentEditor.vue（pushResults 表） | DONE | **[1.1.0]** 中文状态/原因（成功/失败/需人工粘贴/结果未知…） |
| US-128 | AC-128-07 | drafts.py:DraftPushService.start_batch（无自动行时事务内 `audit_batch`）/ `audit_batch`（幂等，全部行）/ DraftPushHandler.run、on_interrupted | DONE | **[1.1.0]** F03：每批次恰 1 条 `CONTENT_DRAFT_PUSHED`，`object_id=batch_id`，含人工/无凭据行 |
| US-129 | AC-129-01 | drafts.py:history；DraftHistoryView；AdminContentEditor.vue:openHistory | DONE | **[1.1.0]** 中文状态 |
| US-129 | AC-129-02 | drafts.py:history(batch_id) | DONE | 沿用 |
| US-129 | AC-129-03 | drafts.py:_out | DONE | 沿用 |
| US-129 | AC-129-04 | views_admin.py:DraftHistoryView（分页） | DONE | 沿用 |
| US-130 | AC-130-01 | export_pack.py:ExportPackService.build_zip；ExportPackView | DONE | **[1.1.0]** 匿名临时文件（F05） |
| US-130 | AC-130-02 | export_pack.py:build_zip（content.txt/html/media） | DONE | 沿用 |
| US-130 | AC-130-03 | export_pack.py:copy_payload；CopyPackView；AdminContentEditor.vue:copyPack | DONE | 沿用 |
| US-130 | AC-130-04 | export_pack.py:build_zip（构建成功后写 CONTENT_PACK_EXPORTED，失败不写） | DONE | **[1.1.0]** 审计顺序明确 |
| US-130 | AC-130-05 | export_pack.py:_prepare（POST_NOT_CONFIRMED）；AdminContentEditor.vue:exportPack（downloadBlob，延后 revoke） | DONE | **[1.1.0]** revokeObjectURL 延后（F07） |
| US-131 | AC-131-01 | core/permissions.py:IsAdmin；views_admin.py:AdminOnly | DONE | 沿用 |
| US-131 | AC-131-02 | views_member.py:InfoListView/InfoDetailView（IsMember） | DONE | 沿用 |
| US-131 | AC-131-03 | views_member.py:MediaFileView（签名授权） | DONE | 沿用 |
| US-131 | AC-131-04 | content/urls.py | DONE | 沿用 |

## 迁移

- `backend/apps/content/migrations/0002_platformaccount_token_cache.py`：手写，文件头无 "Generated by Django"；`dependencies=[("content","0001_initial")]`；4×`AddField`（token_blob/token_expires_at/token_refreshed_at/token_lock_until，均可空、无缺省）+ `RunPython(mark_legacy_wechat_accounts_unset, noop)`（wechat_mp 账户 secret_keys 缺 appid/appsecret 时 auth_status 置 UNSET，只读 secret_keys，不解密）。可逆：`RemoveField`×4，数据步骤反向 no-op；不涉及凭据密文，无 `[MANUAL_ROLLBACK_REQUIRED]`；回滚到 0001 须同时回退 1.0.0 代码。
- 校验：Django 5.2.19 / Python 3.12 下 `makemigrations --check --dry-run --settings=config.test_settings` → `No changes detected`。迁移本身未在 MySQL 上执行（测试不跑迁移，画像 P8 禁止连接测试机库）。

## 架构偏差

| 偏差 | 原 ADR/IFC | 原因 | 影响 |
|---|---|---|---|
| 粘贴守卫保留带 `data-media-id` 的 `<video>`（外部/无 mediaId 的 video 仍移除） | IFC-242 第 2 条"移除所有 `<video>`" | 编辑器自身输出的视频节点在编辑器内复制粘贴时否则被静默删除；与对 `<img>` 的处理口径一致；服务端对无有效 mediaId 的 video 本就丢弃，安全性不降 | 仅编辑器内部复制粘贴视频；`Video.js` 同步补了 `data-media-id`/`src` 的 parseHTML |
| 宽容模式把 `null`/空串的 textStyle 属性视为"未设置"，不产生警告 | IFC-169 规则表未写 | Tiptap 对无该属性的 textStyle 标记输出 `color:null`、`fontSize:""`，否则每次保存都产生无意义警告；严格模式行为不变 | 无安全影响 |
| `get_token_ex()` 作为 `get_token()` 的内部扩展，多返回"本次是否新取" | IFC-240 只有 `get_token` | 适配器按 ADR-060 第 5 条的保守兜底（令牌取自缓存才重取）需要此信息 | `get_token` 签名与语义不变 |
| 视频下载失败统一 `Fail("DOWNLOAD_FAILED")`，消息区分"格式不支持/下载失败"（原 `BAD_FORMAT`/`UPSTREAM`） | IFC-184 1.1.0 下载口径 | 设计规定 | 既有无测试断言旧码 |

## 开放问题

1. **[UNSOURCED] 封面/正文图片上传（Q-B1，ADR-061）**：`wechat_mp.py:HttpWechatMpApi.upload_cover/upload_content_image` 抛 `NotImplementedError("UNSOURCED: Q-B1")`，`DraftArticle.thumb_media_id` 字段名无出处因而**不会写进请求体**；开关 `upload_cover`/`upload_content_images`/`require_cover` 缺省 false。开关被误开时，公众号推送返回 `FAILED(IMAGE_UPLOAD_FAILED)`，不会发出草稿。等待用户提供微信官方文档。
2. **[UNSOURCED] `auth_errcodes`、`token_errcodes` 缺省 `[]`**：AppSecret 错误会表现为 `UPSTREAM`（带 errcode），**不会自动标失效**；草稿接口令牌类错误只在"HTTP 401/403"或"令牌取自缓存且有非零 errcode"时重取一次。真实环境 AC-127-03 无法自动触发，仅替身可验。
3. **[UNSOURCED] 错误描述字段名**：按名为 `errmsg` 的键读取（仓库 draft.py 1.0.0 既有做法），读不到则只展示 errcode。
4. **[ASSUMPTION] AppID/AppSecret 格式**：仅字符集与长度约束（`^[A-Za-z0-9_-]{1,64}$`；可见 ASCII ≤128），不断言微信的格式。
5. **[ASSUMPTION] 视频嵌入公众号草稿**：仍沿用 A-5（不随正文发送，作为"不能保留"提示）。
6. **既有测试因有意行为变化失败（留给 test-engineer 更新，本次未改测试代码）**：见 code_review_report"现有测试调整"。
7. 未做 Python 3.13 验证（本机仅有 3.12）；CI 为 3.13，需 GROUP_D / CI 复核。
8. 0002 迁移未在 MySQL 上实跑（P8）；`TokenService` 的锁与缓存仅在 SQLite 测试库验证。

## DEF-014~016 修复（2.1.0，缺陷回流第 1 次，REWORK_AUTHORIZED）

| DEF | 级别 | 文件:函数 | 改动 | 状态 |
|---|---|---|---|---|
| DEF-014 | MAJOR | backend/apps/content/posts.py:`PostService.render_for_member` | fmt=blocks 时用递归 `_strip` 处理顶层、`children`、`items`（块列表的列表）任意深度的 `src`，统一去掉 `CONTENT_MEDIA_PATH_PREFIX`（AC-108-01、IFC-233） | DONE |
| DEF-015 | MINOR | frontend/src/admin/editor/RichEditor.vue:`requestLink` | `if (!url) return` 改为 `if (url === null) return`：取消静默；空串落入协议校验，提示"网址无效"、不加链接（AC-109-03） | DONE |
| DEF-016 | MINOR | frontend/src/admin/AdminContentEditor.vue:`pushDrafts` 与按钮 | 去掉按钮 `:disabled`；`pushDrafts` 开头未选平台时 `ElMessage.warning('请至少选择一个平台')` 并返回，不发请求（AC-128-04）；后端 NO_PLATFORM_SELECTED 不变 | DONE |

追溯：AC-108-01 → posts.py:`render_for_member`；AC-109-03 → RichEditor.vue:`requestLink`；AC-128-04 → AdminContentEditor.vue:`pushDrafts`，均 DONE。无迁移、无架构偏差、无新增开放问题。
