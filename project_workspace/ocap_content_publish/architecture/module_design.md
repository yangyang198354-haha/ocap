<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-11T11:27:44+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>2.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (1.1.0 DRAFT)</file>
    <file>architecture/module_design.md (1.0.0 APPROVED，被本版本返工)</file>
    <file>phase_status.md (GR-C-002；clarification 2026-11-11T11:23:30)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：信息公开发布与多平台内容中心（INCREMENTAL）

> 编号：MOD-039~061、IFC-165~238（接续基线 MOD-038 / IFC-164）。模块 = 本次新增/修改的代码单元，均注明"新建"或"修改现有"。只写签名、字段、契约，不含函数体。路径相对仓库根；`B/` = `backend/apps/content/`。
> 外部接口出处 `[P11: 文件:行]` 中的文件均位于 `/root/myproject/GenPlatform/project_workspace/content_gen_platform/src/backend/apps/` 下（下称"参考实现"，仓库外，画像 P11-3）。
> 通用约定（所有 HTTP 接口）：错误体 `{code, message, details?}`（`backend/apps/core/errors.py:6-31`，`ApiError`）；分页沿用 `page_response`（`core/serializers.py:4-12`，`page`/`page_size≤100`，响应 `{count,page,page_size,results}`）；认证为 `Authorization: Bearer <token>`（`accounts/authentication.py`）；管理接口用 `IsAdmin`（未登录 401 `UNAUTHORIZED`、业主/游客 403 `FORBIDDEN`，`core/permissions.py:19-25`）；用户接口用 `IsMember`（`:28-34`）；时间为 ISO8601 字符串。

## 1.1.0 修订

> 触发：GR-C-002 FAIL 与用户 2026-11-11 答复（`REWORK_AUTHORIZED`）。编号续接：MOD-062~063、IFC-239~242（`git grep` 核实此前最大为 MOD-061 / IFC-238 / ADR-059）。对应 ADR：ADR-060~063（architecture_design 1.1.0）。**下文凡出现 `[UNSOURCED]` 的接口签名，开发不得实现其 HTTP 细节（阻塞于 Q-B1），可实现其余部分。**

| 变更项 | 模块 / 接口 | 性质 |
|---|---|---|
| 公众号令牌自动获取、缓存、失效口径 | **新建** MOD-062（IFC-240）、MOD-063（IFC-239）；修改 MOD-039（IFC-165 加 4 列 + 0002）、MOD-041（IFC-168 新增 7 项参数、改 1 项语义）、MOD-049（IFC-180）、MOD-050（IFC-181）、MOD-053（IFC-185/186） | ADR-060 |
| 封面与正文图片 | MOD-063 `upload_cover`/`upload_content_image`、MOD-049 `DraftPayload`（均 `[UNSOURCED]`，开关默认关） | ADR-061，阻塞于 Q-B1 |
| 富文本颜色/粘贴/标题/错误定位 | 修改 MOD-042（IFC-169）、MOD-045/054（响应加 `warnings`，IFC-191/193/198）、MOD-059（IFC-237；新增 IFC-241、IFC-242） | ADR-062 |
| 审计落点 | 修改 MOD-044（IFC-173 `delete`）、MOD-053（IFC-186）、MOD-056（IFC-188 增 1 项并给出落点表） | ADR-063 |
| 导出临时文件 | 修改 MOD-053（IFC-187） | ADR-063 |
| worker 单线程、心跳频率 | 修改 MOD-046（IFC-176 `heartbeat`）、MOD-057（IFC-189） | ADR-063 |
| 行距、列表/引用内媒体、下划线+删除线、分镜口径 | 修改 MOD-042（IFC-170/171）、MOD-052（IFC-184）、MOD-061（IFC-238） | ADR-063 |
| `MediaService.list` 改名 `list_items` | 修改 MOD-044（IFC-173） | 规避类体内 `list` 遮蔽内建类型（F01 的设计侧成因） |

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-039 | 数据模型与迁移 | **新建** `B/__init__.py`、`B/apps.py`、`B/models.py`、`B/migrations/__init__.py`、`B/migrations/0001_initial.py`；**1.1.0 新建** `B/migrations/0002_platformaccount_token_cache.py`、**修改现有** `B/models.py`（`PlatformAccount` 加 4 列）；**修改现有** `backend/config/settings.py`（INSTALLED_APPS、4 个 env 读取） | 定义 9 张表、迁移、应用注册；1.1.0 加令牌缓存列 | 全部；REQ-FUNC-116 | — |
| MOD-040 | 凭据保险库与脱敏 | **新建** `B/vault.py` | AES-256-GCM 加解密、`SecretRedactor` | REQ-NFUNC-016；US-117/125/127 | — |
| MOD-041 | 内容中心参数 | **新建** `B/conf.py`；**1.1.0 修改现有**（公众号参数新增 7 项） | 参数默认值、范围校验、读写（基于 `SystemConfig`） | OQ-2、OQ-6；C-29；REQ-FUNC-116 | core |
| MOD-042 | 富文本引擎 | **新建** `B/richtext/{__init__,schema,render,paginate,convert}.py`；**1.1.0 修改现有** `schema.py`（宽容归一化、颜色）、`render.py`（行距、深层媒体、下划线+删除线）、`convert.py`（`extract_paragraphs`） | 文档白名单校验、HTML/块/纯文本渲染、分页、文本转文档 | REQ-FUNC-100~104、REQ-NFUNC-018 | — |
| MOD-043 | 样式模板 | **新建** `B/styles.py` | 内置模板常量、自定义模板 CRUD、令牌校验 | REQ-FUNC-104；US-112 | MOD-039 |
| MOD-044 | 素材库 | **新建** `B/media.py`；**1.1.0 修改现有**（`list`→`list_items`、`delete` 写审计） | 上传校验与分块落盘、配额、候选、签名 URL、Range 响应、远程下载守卫、删除保护 | REQ-FUNC-103、111~114；US-111/119~123 | MOD-039、041、056 |
| MOD-045 | 信息公开内容服务 | **新建** `B/posts.py` | 草稿/发布/下线/删除/确认文案、媒体引用同步、用户端渲染、预览 | REQ-FUNC-099、100、108；US-105~108、113、115 | MOD-039、041~044 |
| MOD-046 | 任务核心 | **新建** `B/jobs.py` | 任务入队/领取/租约/回收/查询、处理器注册表 | REQ-FUNC-117、118、120；ADR-049 | MOD-039、041 |
| MOD-047 | LLM 与文生图客户端 | **新建** `backend/apps/integrations/llm.py`、`backend/apps/integrations/imagegen.py` | Protocol + Http 实现 + `get_/set_` | REQ-FUNC-105、106、109、110 | MOD-040 |
| MOD-048 | 视频生成客户端 | **新建** `backend/apps/integrations/videogen.py` | 即梦提交/轮询（签名）Protocol + Http 实现 | REQ-FUNC-120、121 | MOD-040 |
| MOD-049 | 草稿箱适配器 | **新建** `backend/apps/integrations/draft.py`；**1.1.0 修改现有**（公众号适配器改用令牌服务，凭据字段改 appid/appsecret） | `DraftAdapter` Protocol、公众号适配器、小红书/头条人工适配器、注册表 | REQ-FUNC-116、117、122 | MOD-040、062、063 |
| MOD-050 | 测试替身 | **修改现有** `backend/apps/integrations/fakes.py`（1.1.0 再增 `FakeWechatMpApi`，`FakeDraftAdapter.save_draft` 增 `account_id`） | 新增 `FakeLlmClient`、`FakeImageGenClient`、`FakeVideoGenClient`、`FakeDraftAdapter`、`FakeRemoteFetcher`、`FakeWechatMpApi` | 画像 P4/P11-3 | MOD-044、047~049、063 |
| MOD-051 | 服务配置与提示词模板 | **新建** `B/services_config.py`、`B/prompts.py` | 4 类服务配置（只写凭据）、LLM 连通测试与可选清单、提示词模板 CRUD | REQ-FUNC-105、109、110、121；US-114、117、118、125 | MOD-039~041、047 |
| MOD-052 | AI 生成任务 | **新建** `B/ai_jobs.py`；**1.1.0 修改现有**（`build_scenes` 按段落、下载全有或全无） | 文案/配图/视频的提交校验与任务处理器、分镜构造 | REQ-FUNC-105~108、112、120；US-114~116、120、124 | MOD-041~046、048、051 |
| MOD-053 | 平台账户与草稿推送 | **新建** `B/platforms.py`、`B/drafts.py`、`B/export_pack.py`；**1.1.0 修改现有**三者（凭据变更清令牌缓存、批次审计、失效标记与审计、匿名临时文件） | 账户 CRUD、一键保存批次与重试、历史、内容包与复制 | REQ-FUNC-115~118、122；US-126~130 | MOD-039~046、049、062 |
| MOD-054 | 管理端 HTTP API | **新建** `B/views_admin.py`、`B/serializers.py`、`B/urls.py`；**修改现有** `backend/config/urls.py` | 全部 `/admin/content/*` 接口 | REQ-FUNC-099~122（管理侧）、119 | MOD-041、043~046、051~053 |
| MOD-055 | 用户端 HTTP API | **新建** `B/views_member.py`（含 `B/urls.py` 中用户路由） | `/info/posts*`、`/content/media/<id>/file` | REQ-FUNC-100；US-107/108/113 | MOD-044、045 |
| MOD-056 | 审计动作登记 | **修改现有** `backend/apps/core/audit.py`（`AUDIT_ACTIONS` 增 12 项；**1.1.0 再增 `CONTENT_PLATFORM_AUTH_EXPIRED`，共 13 项**） | 登记新审计动作 | REQ-NFUNC-017 | — |
| MOD-057 | Worker 入口与单元 | **新建** `B/handlers.py`、`B/management/{__init__,commands/__init__,commands/run_content_worker}.py`、`deploy/systemd/ocap-content-worker.service`；**1.1.0 修改现有** `run_content_worker.py`（去 `--concurrency`、心跳 60 秒） | 常驻 worker 命令、处理器注册、housekeeping、systemd 单元模板 | REQ-FUNC-117、118、120；ADR-049、063 | MOD-044、046、052、053 |
| MOD-058 | 前端契约文件 | **修改现有** `frontend/src/shared/api.js`、`miniprogram/utils/api.js` | 新增调用；保持契约测试可解析 | 画像 P6 | — |
| MOD-059 | Web 管理端页面 | **新建** `frontend/src/admin/{AdminContentPosts,AdminContentEditor,AdminMedia,AdminAiServices,AdminPlatforms,AdminContentSettings}.vue`、`frontend/src/admin/editor/{RichEditor.vue,extensions/Video.js,extensions/PageBreak.js,Toolbar.vue,MediaPicker.vue}`；**修改现有** `frontend/src/router/index.js`、`frontend/src/admin/AdminLayout.vue`、`frontend/package.json`；**1.1.0 新建** `frontend/src/admin/editor/{colors.js,pasteGuard.js}`，**修改现有** `RichEditor.vue`、`Toolbar.vue`、`AdminContentEditor.vue`、`AdminPlatforms.vue` | 编辑器（颜色取色器、粘贴守卫）、素材库、AI 生成、平台账户（AppID/AppSecret 表单与白名单提示）、一键保存、参数页 | REQ-FUNC-099~122（界面侧） | MOD-058 |
| MOD-060 | Web 门户页面 | **新建** `frontend/src/portal/{InfoList,InfoDetail}.vue`；**修改现有** `frontend/src/router/index.js`、`frontend/src/portal/Home.vue` | 信息公开列表与分页阅读 | REQ-FUNC-100、104；US-107、113 | MOD-058 |
| MOD-061 | 小程序页面 | **新建** `miniprogram/pages/info/{index,detail}.vue`、`miniprogram/components/RichBlocks.vue`；**修改现有** `miniprogram/pages.json`、`miniprogram/pages/index/index.vue`；**1.1.0 修改现有** `RichBlocks.vue`（行距、深层媒体、装饰线合并） | 信息公开列表、块渲染、分页 | REQ-FUNC-100、104；US-108、113 | MOD-058 |
| MOD-062 | 公众号令牌服务（**1.1.0 新建**） | **新建** `B/wechat_token.py` | 取令牌、加密缓存、单飞刷新、冷却、错误分类 | REQ-FUNC-116、117；REQ-NFUNC-016；US-127、128 | MOD-039、040、041、063 |
| MOD-063 | 公众号接口客户端（**1.1.0 新建**） | **新建** `backend/apps/integrations/wechat_mp.py` | `WechatMpApi` Protocol + `HttpWechatMpApi`（取令牌、`draft/add`）+ `get_/set_` 注入点；封面/正文图片上传仅签名占位（`[UNSOURCED]`） | REQ-FUNC-117；REQ-NFUNC-016 | MOD-040 |

测试文件规划（画像 P3）：后端 `backend/tests/unit/test_content_{richtext,vault_redact,settings_styles,media_rules,jobs,scenes}.py`；`backend/tests/integration/test_content_{admin_api,member_api,ai_jobs_api,drafts_api,contract}.py`；`backend/tests/e2e/test_content_flows.py`；`backend/tests/smoke/test_content_smoke.py`；前端 `frontend/tests/{content_api,rich_editor}.spec.js`；小程序 `miniprogram/tests/rich_blocks.spec.js`。外部服务只经 MOD-050 的替身。

## 模块详情

### MOD-039 数据模型与迁移

职责：9 张新表与迁移，注册 app。文件见总览。

**IFC-165 数据模型契约**（Django 模型字段；表名前缀 `content_`；`created_by_admin_id` 为 `IntegerField`，不建外键，见 ADR-045）：

| 模型 | 字段 | 约束 / 索引 |
|---|---|---|
| `ContentPost` | `id` BigAuto；`title` Char(200)；`doc` JSON（规范化后的文档）；`style_key` Char(64) 缺省 `builtin:classic`；`status` Char(10) ∈ `DRAFT/PUBLISHED/OFFLINE`；`published_at` DateTime null；`text_confirmed_hash` Char(64) 空串缺省（"确认文案"时的纯文本 sha256）；`text_confirmed_at` DateTime null；`created_by_admin_id` Int；`created_by_label` Char(64)；`updated_by_admin_id` Int null；`created_at`、`updated_at` | 索引 `(status, published_at)` |
| `ContentPostMedia` | `post` FK→ContentPost CASCADE；`media` FK→MediaItem CASCADE | 唯一 `(post, media)` |
| `MediaItem` | `id` UUID pk；`media_type` ∈ `IMAGE/VIDEO`；`source` ∈ `UPLOAD/AI_GENERATED`；`state` ∈ `SAVED/CANDIDATE`；`title` Char(255)；`original_name` Char(255)；`content_type` Char(100)；`size` BigInt；`sha256` Char(64)；`storage_path` Char(255)（相对 `MEDIA_ROOT`）；`ai_job` FK→ContentJob SET_NULL null；`created_by_admin_id` Int；`created_at`、`updated_at` | 索引 `(state, media_type, source, created_at)` |
| `StyleTemplate` | `id` BigAuto；`name` Char(64)；`tokens` JSON；`created_by_admin_id`；`created_at`、`updated_at` | 唯一 `name` |
| `PromptTemplate` | `id`；`name` Char(64)；`prompt` Text；`params` JSON；`created_by_admin_id`；时间戳 | 唯一 `name` |
| `ServiceConfig` | `id`；`service_type` Char(16) ∈ `LLM_DEEPSEEK/LLM_VOLCANO/IMAGE_ARK/VIDEO_JIMENG`；`params` JSON（如 `{"model": "..."}`，非敏感）；`secret_blob` Binary null；`secret_keys` JSON（已保存的凭据键名列表）；`is_default` Bool；`last_test_ok` Bool null；`last_tested_at` DateTime null；`last_test_error` Char(32) 空串缺省；`updated_by_admin_id`；`updated_at` | 唯一 `service_type` |
| `PlatformAccount` | `id`；`platform` Char(16) ∈ `wechat_mp/xiaohongshu/toutiao`；`display_name` Char(64)；`secret_blob` Binary null；`secret_keys` JSON；`auth_status` Char(8) ∈ `UNSET/NORMAL/EXPIRED`；`created_by_admin_id`；`created_at`、`updated_at`；**1.1.0 新增（0002，均可空、无缺省值）**：`token_blob` Binary null（加密的 `{"access_token": …}`，AAD context `content_platformaccount_token|<pk>`）、`token_expires_at` DateTime null、`token_refreshed_at` DateTime null、`token_lock_until` DateTime null（单飞锁） | 唯一 `platform`（每平台至多 1 个账户，AC-126-02）；令牌列仅 `wechat_mp` 使用，其他平台恒为 NULL；**任何序列化器不得输出这 4 列** |
| `ContentJob` | `id` BigAuto；`kind` Char(16) ∈ `LLM_TEXT/IMAGE_GEN/VIDEO_GEN/DRAFT_PUSH`；`status` Char(16) ∈ `QUEUED/RUNNING/WAITING_REMOTE/SUCCEEDED/FAILED`；`payload` JSON（**不含凭据**）；`state` JSON（处理器私有断点，如视频 `task_id`）；`result` JSON null；`error_code` Char(32)；`error_message` Char(500)（已脱敏）；`attempts` SmallInt；`max_attempts` SmallInt；`lease_token` Char(32)；`lease_until` DateTime null；`next_run_at` DateTime；`subject_type` Char(24)、`subject_id` Char(64)；`created_by_admin_id`；`created_by_label` Char(64)；`created_at`、`started_at`、`finished_at` | 索引 `(status, next_run_at)`、`(kind, created_at)` |
| `DraftPush` | `id`；`post` FK→ContentPost CASCADE；`account` FK→PlatformAccount SET_NULL null；`platform` Char(16)；`batch_id` UUID；`mode` Char(6) ∈ `AUTO/MANUAL`；`status` Char(16) ∈ `PENDING/SENDING/SAVED/FAILED/UNKNOWN/MANUAL_REQUIRED`；`error_code` Char(32)；`error_message` Char(500)（已脱敏）；`remote_ref` Char(128)（平台返回的草稿 id，非凭据）；`unsupported` JSON（不能保留的样式项）；`retry_of` FK→self SET_NULL null；`job` FK→ContentJob SET_NULL null；`created_by_admin_id`、`created_by_label`；`created_at`、`finished_at` null | 索引 `(post, created_at)`、`(batch_id)` |

**设置变更**（`backend/config/settings.py`，修改现有）：`INSTALLED_APPS` 追加 `"apps.content"`；读取环境变量 `CONTENT_CRED_ENC_KEY`、`CONTENT_CRED_ENC_KEY_PREV`（缺省空串）、`CONTENT_MEDIA_PATH_PREFIX`（缺省 `/api/v1`）、`CONTENT_PUBLIC_BASE_URL`（缺省空串）；`DJANGO_ALLOW_EPHEMERAL_SECRET=1`（测试设置）时 `CONTENT_CRED_ENC_KEY` 缺失则生成进程内随机钥（同 `settings.py:9-18` 的做法）。`apps.py` 的 `ready()` 注册 Django system check：密钥未配置时给 Warning（`content.W001`，非 Error，ADR-050）。

外部依赖：Django 5.2 ORM；MySQL `JSONField`（现有 `AuditLog.detail` 已用，`core/models.py:18`）。

### MOD-040 凭据保险库与脱敏

职责：加解密与脱敏，不接触业务模型。文件 `B/vault.py`。依赖：`cryptography`（新增，ADR-050）。

**IFC-166 `CredentialVault`**
```python
class CredentialVaultError(Exception):
    code: Literal["NOT_CONFIGURED", "DECRYPT_FAILED"]

class CredentialVault:
    @staticmethod
    def is_configured() -> bool: ...
    @staticmethod
    def encrypt(values: Mapping[str, str], *, context: str) -> bytes: ...
        # 明文=JSON(UTF-8)；AES-256-GCM；输出 b"\x01" + nonce(12) + ct||tag；AAD = ("ocap.content|" + context)
        # context 形如 "content_platformaccount|<pk>"；先建行再加密（pk 已知）
    @staticmethod
    def decrypt(blob: bytes, *, context: str) -> dict[str, str]: ...
        # 先试主钥，再试 CONTENT_CRED_ENC_KEY_PREV；失败抛 DECRYPT_FAILED（不回显密文）
```
输入校验：键名 `^[a-z_]{1,32}$`，值 1~4096 字符；密钥须为 base64 编码的 32 字节，否则视为 `NOT_CONFIGURED`。

**IFC-167 `SecretRedactor`**
```python
class SecretRedactor:
    def __init__(self, secrets: Iterable[str]) -> None: ...
    def redact(self, text: str, *, max_len: int = 500) -> str: ...
        # 1) 把长度≥6 的已知凭据值替换为 "***"
        # 2) 正则替换 URL 查询串/表头中的 access_token|api_key|secret|signature|authorization=... 与 "Bearer xxx"
        # 3) 截断到 max_len
def redact_url(url: str) -> str: ...      # 仅用于日志：返回 scheme://host/path，丢弃查询串
```
使用规则：所有 `Http*` 客户端/适配器捕获 `requests.RequestException` 时，只用 `redact(str(exc))` 的结果构造自家异常；`ContentJob.error_message`、`DraftPush.error_message`、日志、审计 `detail` 只接受已脱敏文本。

### MOD-041 内容中心参数

职责：参数默认值、规则与读写。文件 `B/conf.py`。依赖 `apps.core.config.SystemConfig`、`apps.core.errors.ApiError`。

**IFC-168 `ContentSettings`**
```python
class SettingItem(TypedDict):
    key: str; value: Any; default: Any; type: Literal["int", "str", "list", "bool"]
    min: int | None; max: int | None; confirmed: bool; note: str

class ContentSettings:
    @staticmethod
    def get(key: str) -> Any: ...                    # key 为完整键，如 "content.media.image_max_bytes"
    @staticmethod
    def all_items() -> list[SettingItem]: ...
    @staticmethod
    def update(values: Mapping[str, Any], *, admin_id: int) -> list[str]: ...   # 返回已改键；非法 → ApiError("INVALID_VALUE", 400, details={"key": ...})
```
读取时同样套用规则：库内值非法则回落默认（防止直接改库）。**缺省值表**（`confirmed=false` 为待用户确认，ADR-058）：

| 键 | 缺省 | 范围 / 规则 | 状态 / 依据 |
|---|---|---|---|
| `content.media.image_max_bytes` | 10485760 | 1 MiB~50 MiB | 已确认（C-29，沿用 C-12） |
| `content.media.image_exts` | `["jpg","jpeg","png"]` | 子集 {jpg,jpeg,png} | 已确认（C-29） |
| `content.media.video_max_bytes` | 10485760 | 1 MiB~200 MiB | 待确认（OQ-6：C-18 无视频口径，10 MB 偏小） |
| `content.media.video_exts` | `["mp4"]` | 子集 {mp4,mov} | 待确认（OQ-6） |
| `content.media.ai_image_max_bytes` | 10485760 | 1~50 MiB | 待确认 |
| `content.media.ai_video_max_bytes` | 52428800 | 1~500 MiB | 待确认 `[ESTIMATE]` |
| `content.media.total_quota_bytes` | 1073741824 | 0（不限）或 ≥ 64 MiB | 待确认（OQ-6 配额未给）`[ESTIMATE]` |
| `content.media.min_free_bytes` | 536870912 | ≥ 0 | 待确认 `[ESTIMATE]`（磁盘剩余低于此值拒绝写入） |
| `content.media.candidate_ttl_hours` | 24 | 1~720 | 待确认 |
| `content.media.url_ttl_seconds` | 3600 | 60~86400 | 待确认 |
| `content.media.push_url_ttl_seconds` | 86400 | 3600~604800 | 待确认 |
| `content.post.max_doc_bytes` | 1048576 | 64 KiB~8 MiB | 待确认（OQ-2） |
| `content.page.default_chars` | 1500 | 200~20000 | 待确认（OQ-2） |
| `content.ai.rate_limit_per_hour` | 30 | 1~600 | 待确认 |
| `content.ai.max_prompt_chars` | 4000 | 100~20000 | 待确认 |
| `content.job.retention_days` | 30 | 1~365 | 待确认 |
| `content.job.lease_seconds` | 300 | 60~1800，须大于任一单次外部调用超时 | 设计值（ADR-049） |
| `content.llm.timeout_seconds` | 120 | 10~300 | 出处 [P11: llm_gateway/providers.py:129] |
| `content.image.timeout_seconds` | 120 | 10~300 | 出处 [P11: image_generator/doubao_image_client.py:33] |
| `content.image.default_size` | `"2048x2048"` | `^\d{3,4}x\d{3,4}$` | 出处 [P11: doubao_image_client.py:97] |
| `content.video.max_scenes` | 5 | 1~10 | 待确认（A-6） |
| `content.video.scene_seconds` | 5 | 2~10 | 待确认（A-6；取值范围来自非 P11 文件，`[UNSOURCED]`） |
| `content.video.transition` | `"cut"` | `^[a-z_]{1,16}$` | 待确认（A-6，`[UNSOURCED]`） |
| `content.video.poll_interval_seconds` | 15 | 5~120 | 待确认 |
| `content.video.max_wait_seconds` | 1800 | 120~7200 | 待确认 |
| `content.video.max_text_chars` | 2000 | 50~10000 | 待确认 |
| `content.wechat_mp.timeout_seconds` | 30 | 5~120 | 出处 [P11: publisher/publishers.py:72] |
| `content.wechat_mp.auth_errcodes` | `[]` | 整数列表，每项 1~999999，≤50 项 | `[UNSOURCED]`（Q-B1 第 4 项）；**1.1.0 语义改为**：取令牌时命中即视为"凭据被拒"→ 账户标失效（ADR-060） |
| `content.wechat_mp.ip_errcodes`（1.1.0） | `[40164]` | 整数列表，同上 | 缺省值出处 [CODE: backend/apps/integrations/wechat.py:13]；命中 → `IP_NOT_WHITELISTED`，不标失效 |
| `content.wechat_mp.token_errcodes`（1.1.0） | `[]` | 整数列表，同上 | `[UNSOURCED]`（Q-B1 第 4 项）；草稿接口命中 → 强制刷新令牌并重发一次；为空时用 ADR-060 第 5 条的保守兜底 |
| `content.wechat_mp.token_margin_seconds`（1.1.0） | 300 | 60~1800 | 缺省值出处 [CODE: wechat.py:94]（现有 300 秒提前量） |
| `content.wechat_mp.refresh_cooldown_seconds`（1.1.0） | 60 | 10~600 | 设计值（ADR-060 第 5 条）；待确认 |
| `content.wechat_mp.upload_cover` / `upload_content_images` / `require_cover`（1.1.0） | `false` / `false` / `false` | bool | 设计开关；对应接口 `[UNSOURCED]`，Q-B1 定稿前保持关闭（ADR-061） |

### MOD-042 富文本引擎

职责：纯函数，无数据库、无 I/O。目录 `B/richtext/`。

**文档格式**（ProseMirror/Tiptap JSON 子集，IFC-169 的输入输出）：
```python
Mark = TypedDict("Mark", {"type": Literal["bold","italic","underline","strike","link","textStyle"], "attrs": dict})
Node = TypedDict("Node", {"type": str, "attrs": dict, "content": list["Node"], "marks": list[Mark], "text": str}, total=False)
# 允许的 type: doc, paragraph, heading, bulletList, orderedList, listItem, blockquote, horizontalRule,
#              hardBreak, image, video, pageBreak, text
# 允许的 attrs（其余一律丢弃）:
#   paragraph/heading: textAlign ∈ {left,center,right,justify}; heading: level ∈ 1..4; lineHeight 可选
#   orderedList: start (int 1..9999)
#   image: mediaId (UUID 字符串), alt (≤200 字符)      # src 丢弃
#   video: mediaId (UUID 字符串)
#   link:  href (协议 ∈ {http, https, mailto, tel}, ≤2048 字符, 无空白/控制字符)
#   textStyle: color / backgroundColor (^#[0-9a-fA-F]{3}|{6}|{8}$), fontSize (^\d{2}(\.\d)?px$ 且 10..48), lineHeight (数字 1.0..3.0)
```
限制：序列化后字节数 ≤ `content.post.max_doc_bytes`；深度 ≤ 12；节点数 ≤ 20000；`text` 节点总字符数 ≤ 100000。

**IFC-169 `validate_doc`**（`schema.py`）
```python
class DocValidationError(ValueError):
    path: str          # 如 "content[3].marks[0].attrs.href"
    reason: Literal["TYPE","ATTR","LINK","COLOR","SIZE","LIMIT","MEDIA_ID"]
    block_index: int | None    # 1.1.0：顶层块序号（从 0 起）；doc 级错误为 None
    block_type: str | None     # 1.1.0：该顶层块的节点类型，如 "paragraph"

def validate_doc(doc: Any, *, max_bytes: int) -> Node: ...
    # 严格模式（1.0.0 行为不变，保留给单元测试与内部调用）：返回规范化后的新文档（深拷贝、剔除未知节点/属性、合并空 text）；非法 → DocValidationError
    # 空文档 {"type":"doc","content":[]} 合法（草稿可为空）

# ---- 1.1.0 新增（ADR-062） ----
class DocWarning(TypedDict):
    path: str; block_index: int | None
    reason: Literal["COLOR", "SIZE", "LINK", "TYPE", "MEDIA_ID", "LEVEL"]
    action: Literal["DROPPED", "NORMALIZED", "CLAMPED"]

@dataclass(frozen=True)
class ValidationResult:
    doc: Node
    warnings: tuple[DocWarning, ...]     # 至多 50 条
    warning_total: int                   # 实际总数（可大于 50）

def validate_doc_ex(doc: Any, *, max_bytes: int) -> ValidationResult: ...
    # 宽容模式：HTTP 视图（IFC-191/193/198）一律调用本函数；规则表见下；结构类与资源类问题仍抛 DocValidationError
def normalize_color(value: Any) -> str | None: ...
    # 输入 str。#rgb/#rrggbb/#rrggbbaa → 原样（不改大小写）；rgb(r, g, b) / rgba(r, g, b, a) → "#rrggbb" / "#rrggbbaa"；其余 → None
    # 严格正则：^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*(\d(?:\.\d+)?|\.\d+)\s*)?\)$ ；通道>255 或 a∉[0,1] → None
    # a<1 时 aa = floor(a*255 + 0.5)（四舍五入取半向上，前后端一致，不用 Python `round`）的两位小写十六进制；a==1 不带 aa；输出必须再次匹配 COLOR_RE（断言）
```
宽容模式规则（与 ADR-062 表一致）：

| 位置 | 严格模式 | 宽容模式 |
|---|---|---|
| `textStyle.color` / `backgroundColor` | 非 `#hex` → `COLOR` | `normalize_color`；`None` → 丢弃该属性（`DROPPED`/`COLOR`）；rgb 转换 → `NORMALIZED` |
| `textStyle.fontSize` / `lineHeight`、段落/标题 `lineHeight` | 越界/格式错 → `SIZE` | 丢弃该属性（`DROPPED`/`SIZE`） |
| `heading.level` | ∉1..4 → `ATTR` | >4 钳为 4（`CLAMPED`/`LEVEL`）；<1 或非数字 → 缺省 1（`DROPPED`/`LEVEL`） |
| `link.href` | 协议/空白/长度不合 → `LINK` | 丢弃该 `link` 标记（`DROPPED`/`LINK`），文字保留 |
| `image`/`video` 的 `mediaId` 缺失或非 UUID | `MEDIA_ID` | 丢弃该节点（`DROPPED`/`MEDIA_ID`）；`src`、`href` 外链图片同此处理，**不下载不转存** |
| 未知节点 `type` | `TYPE` | 丢弃该节点及子树（`DROPPED`/`TYPE`） |
| 深度/节点数/字符数/字节数超限、根非 `doc`、`content` 非数组、`text` 非字符串、`attrs` 非对象 | `LIMIT`/`TYPE`/`ATTR` | **仍抛 `DocValidationError`**（视图映射为 `CONTENT_INVALID_DOC`，`details` 增 `block_index`、`block_type`） |

**共享测试向量**（后端 `backend/tests/unit/test_content_richtext_lenient.py` 与前端 `frontend/tests/rich_colors.spec.js` 必须使用同一组）：`rgb(255, 0, 0)→#ff0000`；`rgb(0,128,255)→#0080ff`；`rgba(0, 0, 0, 0.5)→#00000080`；`rgba(1, 2, 3, 1)→#010203`；`#F00→#F00`；`#12345678→#12345678`；`rgb(256, 0, 0)→None`；`rgba(0,0,0,1.5)→None`；`red→None`；`hsl(0,100%,50%)→None`；`rgb(10%, 0, 0)→None`；`rgb(1 2 3)→None`；`var(--x)→None`；`url(javascript:alert(1))→None`；`#ggg→None`；`""→None`；`None→None`。

**IFC-170 渲染**（`render.py`）
```python
class StyleTokens(TypedDict, total=False):
    font_family_key: Literal["sans", "serif"]; font_size: int; line_height: float
    paragraph_spacing: int; text_color: str; heading_color: str; link_color: str
    quote_border_color: str; accent_color: str; page_chars: int

@dataclass(frozen=True)
class MediaRef:
    url: str; media_type: Literal["IMAGE", "VIDEO"]; title: str

MediaResolver = Callable[[UUID], MediaRef | None]     # None=素材已不存在

class Inline(TypedDict, total=False):
    text: str; bold: bool; italic: bool; underline: bool; strike: bool
    color: str; bg: str; size: int; lh: float; href: str

class Block(TypedDict, total=False):
    type: Literal["paragraph","heading","bullet_list","ordered_list","quote","hr","image","video"]
    align: Literal["left","center","right","justify"]; level: int; start: int
    inlines: list[Inline]; items: list[list["Block"]]; children: list["Block"]
    src: str; alt: str
    lh: float                                   # 1.1.0：段落/标题的块级行距（1.0~3.0）

def render_html(doc: Node, tokens: StyleTokens, *, mode: Literal["web", "inline"],
                resolve: MediaResolver) -> str: ...
    # web: <article class="rt-article" style="--rt-…"> + 带 class 的元素；inline: 所有样式内联、无 class/<style>/<script>
    # 所有文本与属性值经 html.escape；a 标签固定加 rel="noopener noreferrer nofollow" target="_blank"
    # 素材缺失：image/video 渲染为 "[素材已删除]" 文本段，不输出空 src
def render_blocks(doc: Node, resolve: MediaResolver) -> list[Block]: ...
def render_text(doc: Node) -> str: ...        # 纯文本，段落间空行；用于复制、内容包、摘要、文案确认摘要
```
**1.1.0 渲染口径（ADR-063 第 7 条；三种输出 `web`/`inline`/`blocks` 一致）**：
1. 段落/标题的 `attrs.lineHeight` 输出为该块元素上的 `line-height:<数字>`（数值已被校验为 1.0~3.0 的浮点；`web` 模式也用块上的 `style` 属性，仅此一项）；`blocks` 模式输出 `Block.lh`。行内 `textStyle.lineHeight`（`Inline.lh`）作用于该文字片段，不覆盖块级值。
2. 图片/视频节点在**任意深度**（顶层、`blockquote`、`listItem`）都经同一个 `resolve` 解析并渲染为完整的 `<img>`/`<video>`（`blocks` 为 `image`/`video` 块，带 `src`、`alt`）；素材已不存在时，在原位置渲染"[素材已删除]"段落（不输出空 `src`）。`extract_media_ids`、`media_url_map` 同样遍历到任意深度（现有 `extract_media_ids` 已递归，`backend/apps/content/richtext/convert.py:41-56`，保持）。
3. 同时有 `underline` 与 `strike` 时，输出**一个**样式声明 `text-decoration: underline line-through`（`blocks` 中由 `RichBlocks.vue` 合并两个标志；不得出现两个互相覆盖的 `text-decoration`）。
4. `render_text` 的输出**不变**（`ContentPost.text_confirmed_hash` 依赖它）。

**IFC-171 分页与转换**（`paginate.py`、`convert.py`）
```python
def paginate(doc: Node, page_chars: int) -> list[Node]: ...
    # 先按 pageBreak 切；再按顶层块累计 text 字符数，≥ page_chars 即在该块之后换页；不拆分单个块；空页丢弃；至少返回 1 页
def text_to_doc(text: str) -> Node: ...        # 空行分段→paragraph；以 "#"~"####" 开头的行→heading；其余行内换行→hardBreak
def extract_media_ids(doc: Node) -> list[UUID]: ...
def extract_paragraphs(doc: Node) -> list[str]: ...
    # 1.1.0：按文档顺序返回每个 paragraph/heading（含 blockquote、listItem 内的）的纯文本；hardBreak 记为 "\n"；
    # 去首尾空白后为空的丢弃；image/video/horizontalRule/pageBreak 不产出；供视频分镜切分（IFC-184），不替代 render_text
def unsupported_features(doc: Node, *, platform_unsupported: frozenset[str]) -> list[str]: ...
    # 特征名: "page_break","video","text_align","text_color","background_color","font_size","line_height","blockquote"
    # 返回文档中实际出现且平台不能保留的特征（去重、固定顺序）
def render_pages(doc: Node, tokens: StyleTokens, *, fmt: Literal["html", "blocks"],
                 resolve: MediaResolver, page_chars: int) -> list[dict]: ...
    # [{"index": 0, "html": str} | {"index": 0, "blocks": list[Block]}]
```
外部依赖：仅标准库（`html`、`re`、`json`、`uuid`）。

### MOD-043 样式模板

职责：内置模板（代码常量）、自定义模板 CRUD、令牌校验。文件 `B/styles.py`。依赖 MOD-039。

**IFC-172 `StyleService`**
```python
BUILTIN_TEMPLATES: Mapping[str, StyleTemplateDef]      # 键 "builtin:classic" | "builtin:notice" | "builtin:formal"（缺省 3 套，待确认）

class StyleTemplateDef(TypedDict):
    key: str; name: str; builtin: bool; tokens: StyleTokens

class StyleService:
    @staticmethod
    def list_all() -> list[StyleTemplateDef]: ...
    @staticmethod
    def resolve_tokens(style_key: str) -> StyleTokens: ...     # 未知/已删除→回落 builtin:classic；page_chars 缺省取 content.page.default_chars
    @staticmethod
    def validate_tokens(tokens: Mapping[str, Any]) -> StyleTokens: ...   # 未知键丢弃；越界→ApiError("STYLE_INVALID", 400, details={"field": ...})
    @staticmethod
    def create(*, name: str, tokens: Mapping[str, Any], admin_id: int) -> StyleTemplateDef: ...
    @staticmethod
    def update(template_id: int, *, name: str | None, tokens: Mapping[str, Any] | None) -> StyleTemplateDef: ...
    @staticmethod
    def delete(template_id: int) -> None: ...
```
令牌范围：`font_size` 12..24、`line_height` 1.2..2.4、`paragraph_spacing` 0..32、颜色 `^#[0-9a-fA-F]{6}$`、`page_chars` 200..20000、`font_family_key ∈ {sans,serif}`。`name` 去空白后 1~64 字符，空 → `STYLE_NAME_REQUIRED`（AC-112-04）；重名 → `STYLE_NAME_EXISTS` 409。

### MOD-044 素材库

职责：素材全生命周期。文件 `B/media.py`。依赖 MOD-039、041、`apps.core`（`ApiError`）。

**IFC-173 `MediaService`**
```python
class MediaService:
    @staticmethod
    def upload(*, file: UploadedFile, title: str | None, admin_id: int) -> MediaItem: ...
        # 类型由扩展名判定: image_exts→IMAGE, video_exts→VIDEO，其余 FILE_TYPE_NOT_ALLOWED(400)
        # 分块写盘并计数/sha256；超 image_max_bytes/video_max_bytes → FILE_TOO_LARGE(413)；魔数不符 → FILE_TYPE_NOT_ALLOWED
        # 魔数: jpg/jpeg FFD8FF；png 89504E470D0A1A0A；mp4/mov 偏移 4..8 == b"ftyp"
        # 配额/磁盘: 已用(SAVED+CANDIDATE 总字节)+本文件 > total_quota_bytes → MEDIA_QUOTA_EXCEEDED(413)；shutil.disk_usage 剩余 < min_free_bytes → MEDIA_QUOTA_EXCEEDED
        # 结果 state=SAVED, source=UPLOAD；失败时删除半成品文件
    @staticmethod
    def store_stream(*, chunks: Iterable[bytes], media_type: Literal["IMAGE", "VIDEO"], source: Literal["UPLOAD", "AI_GENERATED"],
                     state: Literal["SAVED", "CANDIDATE"], title: str, original_name: str, max_bytes: int,
                     ai_job_id: int | None, admin_id: int) -> MediaItem: ...      # AI 结果入库用，校验同上
    @staticmethod
    def fetch_remote(url: str, *, max_bytes: int, timeout_seconds: int) -> Iterator[bytes]: ...
        # 经 get_remote_fetcher() 取；Http 实现: 仅 https；解析主机后所有地址须为公网（拒绝环回/私网/链路本地/保留）；
        # 不自动跟随重定向；超 max_bytes 抛 MediaFetchError；超时 timeout_seconds
    @staticmethod
    def list_items(*, media_type: str | None, source: str | None, q: str | None) -> QuerySet[MediaItem]: ...   # 仅 state=SAVED
        # 1.1.0：原名 list 改为 list_items——类体内的 staticmethod `list` 会使同一类体里的注解 `list[...]` 在 Python 3.12/3.13 求值时报
        # TypeError: 'staticmethod' object is not subscriptable（GR-C-002-F01）。所有调用点（views_admin、测试）同步改名。
        # 规则：类体内不得定义名为 list/dict/set/tuple/str/int 的成员（实现缺陷已由 GROUP_C 修复时，也可另加 `from __future__ import annotations` 作为第二道保险，但以改名为准）
    @staticmethod
    def rename(media_id: UUID, title: str) -> MediaItem: ...
    @staticmethod
    def save_candidate(media_id: UUID) -> MediaItem: ...       # CANDIDATE→SAVED；已 SAVED 幂等
    @staticmethod
    def published_usage(media_id: UUID) -> list[tuple[int, str]]: ...   # 引用它的 PUBLISHED 内容 (id, title)
    @staticmethod
    def delete(media_id: UUID, *, admin) -> None: ...  # 1.1.0：参数由 admin_id 改为 admin（审计需要操作人名称）
        # 有已发布引用 → ApiError("MEDIA_IN_USE", 409, details={"posts": [{"id","title"}...≤10]})，不写审计；
        # 成功路径（AC-122-03）：transaction.atomic 内 删 ContentPostMedia + 删行 + AuditService.record(
        #   actor=AuditActor("ADMIN", admin.id, admin.username), action="CONTENT_MEDIA_DELETED", object_type="content_media",
        #   object_id=str(media_id), result="SUCCESS", detail={"title","media_type","source","size"})；文件在 transaction.on_commit 中删除（提交前不删文件）
    @staticmethod
    def housekeeping(now: datetime) -> int: ...                # 清理超过 candidate_ttl_hours 且未被任何内容引用的 CANDIDATE；返回删除数

class MediaFetchError(Exception): code: Literal["SCHEME", "PRIVATE_ADDRESS", "TOO_LARGE", "TIMEOUT", "HTTP"]

class RemoteFetcher(Protocol):
    def fetch(self, url: str, *, max_bytes: int, timeout_seconds: int) -> Iterator[bytes]: ...
def get_remote_fetcher() -> RemoteFetcher: ...
def set_remote_fetcher(fetcher: RemoteFetcher | None) -> None: ...
```
**IFC-174 签名 URL 与文件响应**
```python
def sign_media_url(media_id: UUID, *, ttl_seconds: int | None = None, absolute: bool = False) -> str: ...
    # 值=django.core.signing.dumps({"m": str(id), "e": 过期 epoch 秒}, salt="ocap.content.media")
    # 相对: f"{CONTENT_MEDIA_PATH_PREFIX}/content/media/{id}/file?sig={sig}"；absolute=True 时前缀换成 CONTENT_PUBLIC_BASE_URL + "/api/v1"
def verify_media_sig(media_id: UUID, sig: str, *, now: float | None = None) -> bool: ...
def serve_media_file(request: HttpRequest, media: MediaItem) -> HttpResponse: ...
    # 200 完整 / 206 单段 Range / 416；头: Accept-Ranges: bytes, Content-Type, Content-Length,
    # X-Content-Type-Options: nosniff, Cache-Control: private, max-age=300, Content-Disposition: inline
    # 仅支持单段 "bytes=a-b"、"bytes=a-"、"bytes=-n"；多段或非法 → 416
```
外部依赖：`UploadedFile.chunks()`；标准库 `socket`、`ipaddress`、`shutil`、`hashlib`、`requests`（Http 远程下载实现，已在 `requirements.txt:3`）。

### MOD-045 信息公开内容服务

职责：内容状态机、引用同步、用户端与预览渲染。文件 `B/posts.py`。依赖 MOD-039、041~044，`apps.core.audit`。

状态机：`DRAFT --publish--> PUBLISHED --offline--> OFFLINE --publish--> PUBLISHED`；`PATCH` 作用于 `PUBLISHED` 即时生效并记"修改"审计（A-2）；任意状态可删除。

**IFC-175 `PostService`**
```python
class PostService:
    @staticmethod
    def create(*, title: str, doc: Mapping, style_key: str, admin) -> ContentPost: ...        # 状态 DRAFT；doc 经 validate_doc
    @staticmethod
    def update(post_id: int, *, title: str | None, doc: Mapping | None, style_key: str | None, admin) -> ContentPost: ...
        # 同步 ContentPostMedia；引用的 CANDIDATE 素材升为 SAVED；PUBLISHED 时写审计 CONTENT_POST_UPDATED
    @staticmethod
    def publish(post_id: int, admin) -> ContentPost: ...
        # 校验: 标题非空、正文含文字或图片/视频，否则 ApiError("POST_INCOMPLETE", 400, details={"missing": ["title"|"body"]})；
        # 引用素材全部存在，否则 POST_MEDIA_MISSING(400)；写审计 CONTENT_POST_PUBLISHED；published_at=now
    @staticmethod
    def offline(post_id: int, admin) -> ContentPost: ...      # 仅 PUBLISHED，否则 POST_STATE_INVALID(409)；审计 CONTENT_POST_OFFLINED
    @staticmethod
    def delete(post_id: int, admin) -> None: ...              # 审计 CONTENT_POST_DELETED（detail 含标题）
    @staticmethod
    def confirm_text(post_id: int, admin) -> ContentPost: ... # 记录 text_confirmed_hash=sha256(render_text(doc))，文案为空 → POST_INCOMPLETE
    @staticmethod
    def is_confirmed(post: ContentPost) -> bool: ...          # status∈{PUBLISHED,OFFLINE} 或 hash 与当前纯文本一致
    @staticmethod
    def is_text_confirmed(post: ContentPost) -> bool: ...     # 仅看 hash（视频生成用）
    @staticmethod
    def admin_queryset(status: str | None, q: str | None) -> QuerySet[ContentPost]: ...
    @staticmethod
    def get(post_id: int) -> ContentPost: ...                 # 不存在 → NotFound
    @staticmethod
    def member_queryset() -> QuerySet[ContentPost]: ...       # 仅 PUBLISHED，按 published_at 倒序
    @staticmethod
    def render_for_member(post: ContentPost, fmt: Literal["html", "blocks"]) -> dict: ...
        # {"id","title","published_at","page_count","pages":[…],"theme": StyleTokens(blocks 时必带)}
    @staticmethod
    def render_preview(*, doc: Mapping, style_key: str, fmt: Literal["html"] = "html") -> dict: ...   # 不落库
    @staticmethod
    def media_url_map(doc: Mapping, *, ttl_seconds: int | None = None) -> dict[str, str]: ...   # {mediaId: 签名 URL}
    @staticmethod
    def summary(post: ContentPost, n: int = 80) -> str: ...
```
输入校验：`title` 去空白后 ≤200 字符（草稿允许为空）；`style_key` 必须形如 `builtin:<name>`（存在于常量）或 `custom:<int>`（存在），否则 `STYLE_INVALID`；`doc` 非法 → `ApiError("CONTENT_INVALID_DOC", 400, details={"path":…, "reason":…})`。

### MOD-046 任务核心

职责：任务表上的队列语义。文件 `B/jobs.py`。依赖 MOD-039、041。不依赖任何处理器（依赖倒置，处理器经注册表挂入）。

**IFC-176 `JobService`**
```python
@dataclass(frozen=True)
class JobContext:
    job: ContentJob; now: datetime
    def save_state(self, state: Mapping[str, Any]) -> None: ...    # 持久化断点（租约内）
    def heartbeat(self) -> None: ...                               # 延长租约：lease_until = 当前时间 + lease_seconds（1.1.0：不再用任务开始时间 ctx.now）；处理器在阶段边界调用

class JobOutcome: ...   # Done(result: dict) | Wait(next_run_at: datetime, progress: dict | None) | Fail(code: str, message: str)
class JobHandler(Protocol):
    kind: str
    idempotent: bool                                              # True=中断后可重新入队一次
    def run(self, ctx: JobContext) -> JobOutcome: ...
    def on_interrupted(self, job: ContentJob) -> None: ...        # 租约过期且不重试时调用（如把 SENDING 置 UNKNOWN）

class JobService:
    @staticmethod
    def register_handler(handler: JobHandler) -> None: ...
    @staticmethod
    def enqueue(*, kind: str, payload: Mapping, admin_id: int, admin_label: str,
                subject_type: str = "", subject_id: str = "", max_attempts: int = 2) -> ContentJob: ...
    @staticmethod
    def claim_next(*, now: datetime, lease_seconds: int) -> ContentJob | None: ...
        # 取 status∈{QUEUED, WAITING_REMOTE} 且 next_run_at<=now 的最早一条；以条件 UPDATE(status 与 lease_token 为条件)原子领取，
        # 影响行数=0 即被他人领走；SQLite/MySQL 通用，不依赖 select_for_update
    @staticmethod
    def run_one(job_id: int, *, now: datetime | None = None) -> ContentJob: ...   # 领取后调用处理器；异常→Fail(code="INTERNAL", 脱敏消息)；测试直接调用
    @staticmethod
    def requeue_expired(now: datetime) -> dict[str, int]: ...    # RUNNING 且 lease_until<now: idempotent 且 attempts<max → QUEUED；否则 on_interrupted + FAILED(INTERRUPTED)
    @staticmethod
    def view(job: ContentJob) -> dict: ...                         # JobOut（见 IFC-219）
    @staticmethod
    def get(job_id: int) -> ContentJob: ...                        # NotFound
    @staticmethod
    def purge(now: datetime) -> int: ...                           # 删除终态且超过 job.retention_days 的任务
```
外部依赖：无。

### MOD-047 LLM 与文生图客户端（`backend/apps/integrations/llm.py`、`imagegen.py`，新建）

**IFC-177 `LlmClient`**
```python
@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]; content: str

class LlmError(Exception):
    code: Literal["KEY_INVALID", "QUOTA_EXCEEDED", "UNREACHABLE", "UPSTREAM_ERROR", "EMPTY_RESPONSE"]
    message: str                                   # 已脱敏

@dataclass(frozen=True)
class LlmTestResult:
    ok: bool; error_code: str                       # "" | KEY_INVALID | QUOTA_EXCEEDED | UNREACHABLE

class LlmClient(Protocol):
    def test(self, *, service_type: Literal["LLM_DEEPSEEK", "LLM_VOLCANO"], api_key: str) -> LlmTestResult: ...
        # GET {base}/models，Authorization: Bearer，timeout 10 s；200→ok；401→KEY_INVALID；429→QUOTA_EXCEEDED；其余/网络→UNREACHABLE
    def generate(self, *, service_type: Literal["LLM_DEEPSEEK", "LLM_VOLCANO"], api_key: str, model: str,
                 messages: Sequence[ChatMessage], max_tokens: int, temperature: float, timeout_seconds: int) -> str: ...
        # POST {base}/chat/completions，stream=true；累积 choices[0].delta.content；"[DONE]" 结束；累积为空→EMPTY_RESPONSE

def get_llm_client() -> LlmClient: ...
def set_llm_client(client: LlmClient | None) -> None: ...
```
`base`：`LLM_DEEPSEEK`→`https://api.deepseek.com/v1`；`LLM_VOLCANO`→`https://ark.cn-beijing.volces.com/api/v3`（常量，不可配置）。使用 `requests`（`stream=True`，`timeout=(5, timeout_seconds)`）。

**IFC-178 `ImageGenClient`**
```python
class ImageGenError(Exception):
    code: Literal["AUTH", "QUOTA", "CONTENT_FILTER", "UPSTREAM", "BAD_RESPONSE"]; message: str

class ImageGenClient(Protocol):
    def generate(self, *, api_key: str, model: str, prompt: str, n: int, size: str, timeout_seconds: int) -> list[str]: ...
        # POST https://ark.cn-beijing.volces.com/api/v3/images/generations，Bearer，JSON {model,prompt,n,size,response_format:"url"}
        # 返回 data[].url 列表；401→AUTH；429→QUOTA；400 且含 content_filter/sensitive/审核/违规→CONTENT_FILTER；空列表→BAD_RESPONSE；其余→UPSTREAM
        # 网络超时/连接失败重试 1 次（间隔 5 s）；其余错误不重试
def get_imagegen_client() -> ImageGenClient: ...
def set_imagegen_client(client: ImageGenClient | None) -> None: ...
```

### MOD-048 视频生成客户端（`backend/apps/integrations/videogen.py`，新建）

**IFC-179 `VideoGenClient`**
```python
@dataclass(frozen=True)
class VideoScene:
    scene_index: int; scene_prompt: str; narration: str; duration_sec: int; transition: str

@dataclass(frozen=True)
class VideoTaskStatus:
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int                                   # 0..100
    clip_urls: tuple[str, ...]; error: str | None

class VideoGenError(Exception):
    code: Literal["AUTH", "UPSTREAM", "BAD_RESPONSE", "TIMEOUT"]; message: str

class VideoGenClient(Protocol):
    def submit(self, *, access_key: str, secret_key: str, scenes: Sequence[VideoScene]) -> str: ...      # 返回 task_id
    def poll(self, *, access_key: str, secret_key: str, task_id: str) -> VideoTaskStatus: ...
def get_videogen_client() -> VideoGenClient: ...
def set_videogen_client(client: VideoGenClient | None) -> None: ...
```
Http 实现：`https://visual.volcengineapi.com`，service `visual`、region `cn-north-1`、version `2024-05-01`，HMAC-SHA256 请求签名（算法按参考实现，仅用标准库 `hmac/hashlib/time`）；`submit` → `Action=CVSubmitTask`，body `{"req_key":"i2v_multi_scene","scenes":[{"prompt","narration","duration","transition"}…]}`，`task_id` 取 `data.task_id` 或顶层 `task_id`；`poll` → `Action=CVQueryTask`，body `{"task_id"}`，`data.status`：`queue→pending`、`processing`、`succeed→completed`、`failed`（其余视为 pending），`data.video_urls`、`data.progress`、`data.error_message`。超时 30 s。

### MOD-049 草稿箱适配器（`backend/apps/integrations/draft.py`，新建）

**IFC-180 `DraftAdapter` 与注册表**
```python
Capability = Literal["AUTO_DRAFT", "MANUAL_EXPORT"]

@dataclass(frozen=True)
class CredentialField:
    key: str; label: str; secret: bool = True; required: bool = True

@dataclass(frozen=True)
class MediaFile:
    media_id: str; path: str; content_type: str; media_type: Literal["IMAGE", "VIDEO"]; name: str

@dataclass(frozen=True)
class DraftPayload:
    title: str; html: str                 # inline 模式 HTML（媒体为 absolute 签名 URL）
    text: str; media: tuple[MediaFile, ...]
    html_for: Callable[[Mapping[str, str]], str] | None = None
        # 1.1.0：以 {mediaId: 替换后的图片地址} 重新渲染 inline HTML（ADR-061，仅在 upload_content_images 开启时被使用；
        # 由 DraftPushService.build_payload 提供，内部调用 render_html(mode="inline", resolve=…)）
    cover: MediaFile | None = None        # 1.1.0：封面候选 = 文档中按出现顺序的第一张图片；无图片为 None（设计口径，ADR-061）

@dataclass(frozen=True)
class DraftOutcome:
    status: Literal["SAVED", "AUTH_EXPIRED", "FAILED"]
    remote_ref: str = ""; error_code: str = ""; message: str = ""     # message 已脱敏
    # error_code 取值（1.1.0 汇总，空串=成功）：NO_CREDENTIALS | AUTH_EXPIRED | IP_NOT_WHITELISTED | TOKEN_BUSY | UPSTREAM | NETWORK
    #   | COVER_REQUIRED | IMAGE_UPLOAD_FAILED（后两项依赖 Q-B1，开关关闭时不会产生）

class DraftAdapter(Protocol):
    platform: str; label: str; capability: Capability
    credential_fields: tuple[CredentialField, ...]
    unsupported_features: frozenset[str]          # 见 IFC-171 的特征名
    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str], *, account_id: int | None = None) -> DraftOutcome: ...
        # 1.1.0：新增关键字参数 account_id（令牌缓存按账户存取；DraftPushHandler 总是传入，直接调用/旧测试可省略）
        # capability=="MANUAL_EXPORT" 的适配器：save_draft 抛 NotImplementedError，服务层从不调用

PLATFORMS: tuple[str, ...] = ("wechat_mp", "xiaohongshu", "toutiao")
def get_draft_adapter(platform: str) -> DraftAdapter: ...              # 未知平台 → KeyError（服务层转 PLATFORM_NOT_SUPPORTED）
def set_draft_adapter(platform: str, adapter: DraftAdapter | None) -> None: ...   # 测试/日后接入自动草稿
```
内置适配器：
- `WechatMpDraftAdapter`（**1.1.0 重写，ADR-060/061**）：`capability="AUTO_DRAFT"`；`credential_fields=(CredentialField("appid","AppID"), CredentialField("appsecret","AppSecret"))`（均 `secret=True`、`required=True`；原 `access_token` 字段作废）。`save_draft` 流程：
  1. 缺 `appid`/`appsecret` → `FAILED(NO_CREDENTIALS)`（不调用任何接口）。
  2. 经 `WechatTokenService.get_token(account_id, credentials)`（IFC-240）取令牌；`WechatTokenError` 按 ADR-060 第 6 条的分类表映射为 `DraftOutcome`（`AUTH_REJECTED`→`AUTH_EXPIRED`；`IP_NOT_WHITELISTED`、`UPSTREAM`、`NETWORK`、`TOKEN_BUSY`、`NO_CREDENTIALS`→`FAILED` 同名 `error_code`）。
  3. 〔`content.wechat_mp.upload_cover` 为真时〕上传封面（`WechatMpApi.upload_cover`，`[UNSOURCED]`）；`require_cover` 为真且 `payload.cover is None` → `FAILED(COVER_REQUIRED)`。
  4. 〔`content.wechat_mp.upload_content_images` 为真时〕逐张上传 `payload.media` 中的图片（`WechatMpApi.upload_content_image`，`[UNSOURCED]`），得到 `{mediaId: 微信侧地址}`，用 `payload.html_for(映射)` 重新渲染正文；任一张失败 → `FAILED(IMAGE_UPLOAD_FAILED)`（不发草稿）。两个开关都关闭时直接使用 `payload.html`。
  5. 调用 `WechatMpApi.add_draft(token, DraftArticle(title, content, author="", thumb_media_id=封面或 None))`（IFC-239）。成功判定：响应含非空 `media_id` → `SAVED(remote_ref=media_id)`（[P11: publishers.py:83-87]）。
  6. 令牌类错误（HTTP 401/403；`errcode` ∈ `token_errcodes`；`token_errcodes` 为空时的保守兜底见 ADR-060 第 5 条）→ `get_token(..., stale_token=旧令牌, force=True)`，重发**至多一次**；超时/连接中断不重发。
  7. 其余失败 → `FAILED(UPSTREAM, message=脱敏后的 errcode 与错误描述摘要≤200 字符，描述字段见 WechatMpApiError.errmsg 的说明)`；网络异常 → `FAILED(NETWORK)`，消息仅含 `redact_url(url)` 与经 `SecretRedactor([appsecret, token])` 脱敏的异常文本。
  **不调用 `freepublish/submit`**。`unsupported_features=frozenset({"page_break","video"})`（A-5，`[ASSUMPTION]`）。适配器不再直接 `import requests`，所有 HTTP 经 `WechatMpApi`（便于替身测试）。
- `ManualExportAdapter(platform, label)`：用于 `xiaohongshu`（"小红书"）、`toutiao`（"今日头条"）；`capability="MANUAL_EXPORT"`；`credential_fields=(CredentialField("credential","认证信息（预留）", required=False),)`（A-1）；`unsupported_features=frozenset()`（内容包的固有限制由服务层固定追加，见 IFC-186）。

### MOD-050 测试替身（`backend/apps/integrations/fakes.py`，修改现有）

**IFC-181 新增替身**（沿用 `FakeWeChatClient` 风格：内存记录调用、可编程失败、`reset()`）：
```python
class FakeLlmClient:        # 实现 LlmClient
    responses: list[str]; fail_code: str | None; test_result: LlmTestResult; calls: list[dict]   # calls 不记录 api_key 值，只记录其是否非空
    def reset(self) -> None: ...
class FakeImageGenClient:   # 实现 ImageGenClient；urls: list[str]；fail_code
class FakeVideoGenClient:   # 实现 VideoGenClient；submit_task_id: str；statuses: list[VideoTaskStatus]（逐次 poll 取下一个）；fail_on: Literal["submit","poll"] | None
class FakeDraftAdapter:     # 实现 DraftAdapter（1.1.0：save_draft 增加关键字参数 account_id，并记录到 received_account_ids）；构造参数 platform/capability/outcomes: list[DraftOutcome]；received: list[DraftPayload]；
                            # 用 set_draft_adapter 注入，可模拟 AUTH_EXPIRED / FAILED
class FakeRemoteFetcher:    # 实现 RemoteFetcher；payloads: dict[str, bytes]；未知 URL → MediaFetchError("HTTP")
class FakeWechatMpApi:      # 1.1.0：实现 WechatMpApi（IFC-239）
    token_results: list[TokenResponse | WechatMpApiError]     # 逐次 fetch_token 取下一个；用尽后重复最后一个
    draft_results: list[str | WechatMpApiError]               # 逐次 add_draft 取下一个（str=media_id）
    upload_cover_results / upload_image_results: list[str | WechatMpApiError]   # 占位：Q-B1 定稿前仅供开关开启的用例使用
    calls: list[dict]          # 记录 {"op", "appid_present": bool, "token_present": bool}，**不记录 secret 与令牌值**
    def reset(self) -> None: ...
    # 用法（覆盖 ADR-060 全部分支）：令牌过期前复用（calls 中 fetch_token 次数）、提前量刷新、草稿令牌错误→强制刷新重发一次、
    #   冷却内不重复取、单飞（预置 token_lock_until 未过期→TOKEN_BUSY）、errcode∈auth_errcodes→AUTH_EXPIRED、∈ip_errcodes→IP_NOT_WHITELISTED、
    #   凭据覆盖更新后缓存被清空。令牌缓存走真实的 SQLite 测试库（模型列与加密生效；测试不跑迁移，0002 由 `makemigrations --check` 无漂移与部署前 `migrate` 验证），仅 HTTP 层为替身
```
测试约束：任何用例不得走 `Http*` 实现；测试基类在 `setUp` 中 `set_*_client(Fake…)`，`tearDown` 复位为 `None`。

### MOD-051 服务配置与提示词模板

职责：凭据"只写不读"的配置存取、LLM 连通测试与可选清单、提示词模板。文件 `B/services_config.py`、`B/prompts.py`。依赖 MOD-039~041、047。

**IFC-182 `ServiceConfigService`**
```python
SERVICE_TYPES: tuple[str, ...] = ("LLM_DEEPSEEK", "LLM_VOLCANO", "IMAGE_ARK", "VIDEO_JIMENG")

@dataclass(frozen=True)
class ServiceSpec:
    service_type: str; label: str
    secret_fields: tuple[str, ...]                 # LLM_*: ("api_key",)；IMAGE_ARK: ("api_key",)；VIDEO_JIMENG: ("access_key","secret_key")
    default_params: Mapping[str, str]              # LLM_DEEPSEEK: {"model":"deepseek-chat"}；LLM_VOLCANO: {"model":"doubao-pro-4k"}；IMAGE_ARK: {"model":"doubao-seedream-4-5-251128"}；VIDEO_JIMENG: {}
    model_hints: tuple[str, ...]                   # 前端下拉提示，来自代码常量（可手填）
    testable: bool                                 # 仅 LLM_* 为 True

class ServiceConfigOut(TypedDict):
    service_type: str; label: str; configured: bool; params: dict; secret_saved: dict[str, bool]
    is_default: bool; last_test_ok: bool | None; last_tested_at: str | None; last_test_error: str; updated_at: str | None
    testable: bool; model_hints: list[str]; secret_fields: list[str]

class ServiceConfigService:
    @staticmethod
    def list_all() -> list[ServiceConfigOut]: ...
    @staticmethod
    def save(service_type: str, *, params: Mapping[str, str] | None, secrets: Mapping[str, str] | None,
             is_default: bool | None, admin) -> ServiceConfigOut: ...
        # secrets 为覆盖式更新（只写不读）：仅提供的键被覆盖，其余保留；首次保存时必填项缺失 → ApiError("MISSING_FIELDS", 400, details={"fields": [...]})
        # 变更 secrets 或 params.model 时 last_test_ok 置 None；is_default=True 时同类（LLM_*）其他项置 False
        # 加密失败（未配置密钥）→ ApiError("CREDENTIAL_VAULT_NOT_CONFIGURED", 503)；写审计 CONTENT_SERVICE_CONFIG_CHANGED（detail 只含键名 changed_fields）
    @staticmethod
    def test(service_type: str, admin) -> dict: ...                # {"ok","error_code","message"}；非 testable → ApiError("NOT_TESTABLE", 400)；写审计 CONTENT_SERVICE_TESTED；更新 last_test_*
    @staticmethod
    def llm_options() -> list[dict]: ...                           # last_test_ok=True 的 LLM 配置: [{"service_type","label","model","is_default"}]
    @staticmethod
    def resolve_llm(service_type: str | None) -> tuple[str, str]: ...   # → (service_type, model)；未指定=默认项（从未设置默认则 LLM_DEEPSEEK）；不可用 → ApiError("LLM_NOT_CONFIGURED", 409)
    @staticmethod
    def secrets_for(service_type: str) -> dict[str, str]: ...      # 仅供处理器内部使用，解密；缺失 → ApiError("<TYPE>_NOT_CONFIGURED", 409)
```
输入校验：`service_type ∈ SERVICE_TYPES` 否则 404；`params.model` 匹配 `^[A-Za-z0-9._:/-]{1,64}$`；secrets 各值 1~4096 字符、去除首尾空白后非空；未知键 400 `INVALID_VALUE`。

**IFC-183 `PromptTemplateService`**（`prompts.py`）
```python
class PromptTemplateService:
    @staticmethod
    def list_all() -> list[dict]: ...      # [{"id","name","prompt","params","updated_at"}]
    @staticmethod
    def create(*, name: str, prompt: str, params: Mapping | None, admin_id: int) -> dict: ...
    @staticmethod
    def update(template_id: int, *, name: str | None, prompt: str | None, params: Mapping | None) -> dict: ...
    @staticmethod
    def delete(template_id: int) -> None: ...
```
校验：`name` 1~64；`prompt` 1~`content.ai.max_prompt_chars`；`params` 经 `GenParams` 校验；重名 409 `PROMPT_NAME_EXISTS`。

### MOD-052 AI 生成任务

职责：提交校验 + 三类任务处理器 + 分镜构造。文件 `B/ai_jobs.py`。依赖 MOD-041~046、048、051、`apps.core.ratelimit`。

**IFC-184 `AiGenerationService` 与处理器**
```python
class GenParams(TypedDict, total=False):
    tone: Literal["FORMAL", "FRIENDLY", "CONCISE"]          # 语气（待确认，OQ-2）
    length: Literal["SHORT", "MEDIUM", "LONG"]              # 篇幅 → max_tokens 1024 / 2048 / 4096（待确认）
    temperature: float                                      # 0.0..1.5，缺省取服务缺省

class AiGenerationService:
    @staticmethod
    def submit_text(*, prompt: str, service_type: str | None, template_id: int | None, params: GenParams, admin) -> ContentJob: ...
        # 校验顺序: 限流(RateLimiter.hit "content_ai:<admin>" content.ai.rate_limit_per_hour/3600s → RateLimited) → prompt 去空白后非空(PROMPT_EMPTY 400)
        # → 长度 → resolve_llm(LLM_NOT_CONFIGURED 409)；payload={prompt, service_type, model, params}
    @staticmethod
    def submit_image(*, prompt: str, n: int, size: str | None, admin) -> ContentJob: ...
        # 限流 → prompt 1..500(PROMPT_EMPTY/INVALID_VALUE) → n 1..4 → 配置存在(IMAGE_NOT_CONFIGURED 409)
    @staticmethod
    def submit_video(*, post_id: int, admin) -> ContentJob: ...
        # 限流 → 配置存在(VIDEO_NOT_CONFIGURED 409) → 内容存在 → is_text_confirmed 否则 TEXT_NOT_CONFIRMED(409) → 纯文本 1..video.max_text_chars
        # payload={post_id, text_sha256, scenes: [VideoScene…]}；审计 CONTENT_VIDEO_REQUESTED（result=SUCCESS；校验失败时 result=DENIED 且不建任务）
    @staticmethod
    def build_scenes(paragraphs: Sequence[str], *, max_scenes: int, scene_seconds: int, transition: str) -> list[VideoScene]: ...
        # 1.1.0（ADR-063 第 8 条）：入参由整篇文本改为段落列表（来自 extract_paragraphs(post.doc)，IFC-171），不再对 render_text 的结果按 "\n\n" 切分
        # （render_text 以单个 "\n" 连接，原实现恒得 1 个分镜）；段数>max_scenes 时合并相邻段使总长最短的一对（合并处以 "\n" 连接）直到段数==max_scenes；
        # 每段 scene_prompt=narration=该段文本；duration_sec=scene_seconds；段落列表为空 → ApiError("POST_INCOMPLETE", 400)
        # submit_video 的"文案非空与长度"校验仍用 render_text(doc) 的长度与 text_sha256（口径不变）
    @staticmethod
    def compose_messages(prompt: str, params: GenParams) -> list[ChatMessage]: ...   # system 提示由服务端固定模板 + 语气/篇幅提示；user=prompt

class TextJobHandler:   kind="LLM_TEXT";   idempotent=True    # 结果 {"text","doc","service_type","model"}；LlmError→Fail(code 同 LlmError.code)
class ImageJobHandler:  kind="IMAGE_GEN";  idempotent=True    # 结果 {"media_ids":[uuid…]}；每个 URL 经 fetch_remote→store_stream(state=CANDIDATE, source=AI_GENERATED)；格式非 jpg/png → Fail("BAD_FORMAT")
class VideoJobHandler:  kind="VIDEO_GEN";  idempotent=False   # 见 ADR-055 状态机；断点 state={"task_id","phase","submitted_at"}；
                                                              # 成功后每个片段 → store_stream(VIDEO, CANDIDATE, AI_GENERATED, ai_video_max_bytes)，全部成功后统一转 SAVED（1.1.0，见下"下载口径"；1.0.0 为直接 SAVED）；写审计 CONTENT_VIDEO_COMPLETED（actor=任务创建者）
```
**1.1.0 下载口径（ADR-063 第 8 条）**：成功后各片段先以 `state=CANDIDATE` 逐个入库，**全部成功后**在一个事务内统一转 `SAVED`；任一片段下载/入库失败 → 删除本任务已入库的片段（行与文件）→ `Fail("DOWNLOAD_FAILED", 脱敏原因)`；`clip_urls` 与 `task_id` 写入 `ContentJob.state` 保留；每个片段下载前 `ctx.heartbeat()`。
`VideoJobHandler.run` 阶段：`submit`（调用前 `phase="SUBMITTING"`，拿到 `task_id` 立即 `save_state` 为 `phase="POLLING"`）→ `Wait(now+poll_interval)` → 轮询：`completed`→下载入库→`Done`；`failed`→`Fail("REMOTE_FAILED", 脱敏原因)`；超过 `max_wait_seconds`→`Fail("TIMEOUT")`；`on_interrupted` 且 `phase=="SUBMITTING"` → 失败原因 `SUBMIT_UNKNOWN`（"提交状态未知，请先到即梦控制台核对再重试"）。

### MOD-053 平台账户与草稿推送

职责：账户 CRUD（凭据只写不读）、一键保存批次、重试、历史、内容包、复制。文件 `B/platforms.py`、`B/drafts.py`、`B/export_pack.py`。依赖 MOD-039~046、049。

**IFC-185 `PlatformAccountService`**
```python
class PlatformAccountOut(TypedDict):
    id: int; platform: str; display_name: str; auth_status: Literal["UNSET", "NORMAL", "EXPIRED"]
    secret_saved: dict[str, bool]; updated_at: str

class PlatformAccountService:
    @staticmethod
    def list_platforms() -> list[dict]: ...
        # 每个平台一项: {"platform","label","capability","credential_fields":[{"key","label","secret","required"}],"account": PlatformAccountOut|None}
    @staticmethod
    def create(*, platform: str, display_name: str, credentials: Mapping[str, str] | None, admin) -> PlatformAccountOut: ...
        # 平台不在 PLATFORMS → PLATFORM_NOT_SUPPORTED(400)；已有账户 → PLATFORM_ACCOUNT_EXISTS(409,"每个平台只能有 1 个账户")
        # 必填凭据齐全 → NORMAL，否则 UNSET；写审计 CONTENT_PLATFORM_ACCOUNT_CHANGED(detail: action=create)
    @staticmethod
    def update(account_id: int, *, display_name: str | None, credentials: Mapping[str, str] | None, admin) -> PlatformAccountOut: ...
        # credentials 覆盖式合并；更新后必填齐全 → NORMAL（含从 EXPIRED 恢复，AC-127-04）；审计 detail.action ∈ {rename, credentials_updated}（不含值）
        # 1.1.0：凭据有任何覆盖时调用 WechatTokenService.invalidate(account_id) 清空令牌缓存 4 列（与凭据写入同一事务）；
        #        wechat_mp 的 appid、appsecret 只接受键名 appid/appsecret（旧键 access_token → INVALID_VALUE，details.key）
    @staticmethod
    def delete(account_id: int, admin) -> None: ...             # DraftPush.account 置空保留历史；审计
    @staticmethod
    def credentials_of(account_id: int) -> dict[str, str]: ...  # 仅内部使用
    @staticmethod
    def mark_expired(account_id: int, *, actor: AuditActor, reason: str) -> bool: ...
        # 1.1.0：仅当 auth_status 为 NORMAL 时置 EXPIRED 并写审计 CONTENT_PLATFORM_AUTH_EXPIRED
        # （object_type="platform_account"，detail={"platform","reason"}，actor=任务创建者）；返回是否发生了变更；已是 EXPIRED/UNSET 不重复写
```
输入校验：`display_name` 去空白后 1~64 字符；`credentials` 键须属于该平台 `credential_fields`，值 1~4096 字符，否则 `INVALID_VALUE`。**1.1.0 追加**：`appid` 须匹配 `^[A-Za-z0-9_-]{1,64}$`（仅字符集约束，不断言微信的 AppID 格式 `[ASSUMPTION]`）；`appsecret` 去空白后 1~128 个可见 ASCII 字符（无空白）；不符 → `INVALID_VALUE`（`details.key`，消息不回显值）。

**IFC-186 `DraftPushService`**
```python
class DraftPushOut(TypedDict):
    id: int; batch_id: str; platform: str; display_name: str; mode: Literal["AUTO", "MANUAL"]
    status: Literal["PENDING", "SENDING", "SAVED", "FAILED", "UNKNOWN", "MANUAL_REQUIRED"]
    error_code: str; error_message: str; unsupported: list[str]; remote_ref: str
    created_at: str; finished_at: str | None; operator: str

class DraftPushService:
    @staticmethod
    def start_batch(post_id: int, account_ids: Sequence[int], admin) -> tuple[str, int | None, list[DraftPushOut]]: ...
        # → (batch_id, job_id|None, pushes)
        # 校验: 账户列表非空(NO_PLATFORM_SELECTED 400)、≤3、账户存在；PostService.is_confirmed 否则 POST_NOT_CONFIRMED(409)
        # 每个账户建 DraftPush: capability==MANUAL_EXPORT → status=MANUAL_REQUIRED, mode=MANUAL, finished_at=now（不进任务）；
        #   AUTO 且必填凭据缺失 → FAILED(error_code="NO_CREDENTIALS")；AUTO 且齐全 → PENDING
        # unsupported = unsupported_features(doc, adapter.unsupported_features) + (MANUAL 时固定追加 "style_not_carried")
        # 存在 PENDING 行则入队一个 DRAFT_PUSH 任务（payload={"batch_id": str, "push_ids":[…]}；1.1.0 增 batch_id）
        # 1.1.0（AC-128-07，ADR-063 第 2 条）：整个方法在 transaction.atomic 内；**没有 PENDING 行（全为人工/无凭据）时，不入队，
        #   在同一事务内直接调用 DraftPushService.audit_batch(batch_id, actor=admin)** 写 1 条审计；有 PENDING 行时由 worker 写（见下）
        # 1.1.0：unsupported 计算须在渲染口径修订后仍一致（unsupported_features 仅看文档中实际出现的特征）
    @staticmethod
    def retry(push_id: int, admin) -> tuple[int, DraftPushOut]: ...   # 仅 FAILED/UNKNOWN 且 mode=AUTO；新建行(retry_of)+入队；否则 DRAFT_PUSH_STATE_INVALID(409)
    @staticmethod
    def history(post_id: int, *, batch_id: str | None) -> QuerySet[DraftPush]: ...
    @staticmethod
    def build_payload(post: ContentPost, adapter: DraftAdapter) -> DraftPayload: ...   # render_html(mode="inline")，媒体 URL 为 absolute 签名 URL(push_url_ttl_seconds)
        # 1.1.0：同时填 DraftPayload.html_for（以 {mediaId: 地址} 覆盖后重新渲染）与 DraftPayload.cover（文档顺序第一张图片的 MediaFile，无则 None）
    @staticmethod
    def audit_batch(batch_id: str, *, actor: AuditActor) -> None: ...
        # 1.1.0：汇总该 batch_id 下**全部** DraftPush 行（AUTO/MANUAL/无凭据，不限于某个任务）写 1 条审计：
        #   action="CONTENT_DRAFT_PUSHED", object_type="content_draft_batch", object_id=batch_id（原为 job.id，作废）,
        #   result="SUCCESS"（无 FAILED/UNKNOWN 行）否则 "FAILURE"（仍属一次完成的批次），
        #   detail={"post_id": int, "results": [{"platform","mode","status","error_code"}…]}（不含 error_message，防止泄露；顺序按创建顺序）
        # 同一 batch_id 只写一次：以 AuditLog(action, object_id) 是否已存在做幂等判断

class DraftPushHandler:   kind="DRAFT_PUSH"; idempotent=False
    # 逐行处理: 置 SENDING → 解密凭据 → adapter.save_draft(payload, credentials, account_id=account.id) → 置 SAVED/FAILED/（AUTH_EXPIRED: FAILED + PlatformAccountService.mark_expired(actor=任务创建者, reason="AUTH_REJECTED")）
    # 每处理一行前 ctx.heartbeat()（延长租约）
    # 单行异常不影响其他行；全部结束调用 DraftPushService.audit_batch(payload["batch_id"], actor=任务创建者)（1.1.0：汇总全批次，不只本任务的行）
    # on_interrupted: 仍为 SENDING 的行置 UNKNOWN（"结果未知，请到平台草稿箱核对后重试"），PENDING 的行置 FAILED(INTERRUPTED)；随后同样调用 audit_batch（1.1.0）
    # retry(): 新建的重试行自成新 batch_id、payload 带该 batch_id，结束时同样写 1 条（1.1.0）
```
**IFC-187 `ExportPackService`**
```python
class ExportPackService:
    @staticmethod
    def build_zip(post: ContentPost, platform: str, admin) -> tuple[IO[bytes], str]: ...
        # 返回 (临时文件对象, 下载文件名)；内含 content.txt、content.html、media/NN_<name>、README.txt；媒体用 ZIP_STORED
        # 1.1.0（F05，ADR-063 第 4 条）临时文件生命周期：用 tempfile.TemporaryFile("w+b")（匿名文件，POSIX 上创建即无目录项，close 或进程退出即回收），
        #   ZipFile 直接写该文件对象；构建过程任何异常 → finally 中 close 后再抛；成功时 seek(0) 返回，视图把它交给 FileResponse，由响应关闭文件；
        #   禁止 NamedTemporaryFile(delete=False)、禁止在磁盘上留下命名文件；验收：构建前后 tempfile.gettempdir() 下新增文件数为 0（成功、构建失败、客户端中断三种路径）
        #   审计 CONTENT_PACK_EXPORTED 在 zip 构建成功之后、返回之前写入（构建失败不写）
        # 平台须在 PLATFORMS 且 capability=="MANUAL_EXPORT"（AUTO 平台也允许导出，供失败兜底，不限制）
        # PostService.is_confirmed 否则 POST_NOT_CONFIRMED；写审计 CONTENT_PACK_EXPORTED
    @staticmethod
    def copy_payload(post: ContentPost, platform: str) -> dict: ...      # {"text": str, "html": str, "unsupported": list[str]}
```
外部依赖：标准库 `zipfile`、`tempfile`；`requests`（仅 `WechatMpDraftAdapter`）。

### MOD-054 管理端 HTTP API

职责：薄视图，权限 `IsAdmin`，序列化，错误码映射。`B/urls.py` 由 `backend/config/urls.py` 以 `path("api/v1/", include("apps.content.urls"))` 引入（修改现有）。路径中 `<id>` 为整数，`<uuid>` 为 UUID。**所有接口鉴权：`IsAdmin`（沿用现有管理员令牌，`core/permissions.py:19-25`）；未登录 401、非管理员 403。**

以下表格给出请求/响应契约；"校验"列为输入校验，"错误"列为 `code (HTTP)`。

**1.1.0 附加字段 `warnings`（IFC-191/193/198 的响应，ADR-062）**：`warnings: DocWarning[]`（至多 50 条，结构见 IFC-169）与 `warning_total: int`；无警告时为 `[]` 与 `0`；GET 类接口不含该字段。该附加字段不改变路径、方法与权限，不影响 `test_frontend_contract.py` 的解析（`backend/tests/integration/test_frontend_contract.py:30-97` 只比对路径与权限）。`PostService.create/update/render_preview` 因此返回 `(post, ValidationResult.warnings, warning_total)` 或等价结构（IFC-175 的返回类型随之调整，由开发按此契约落实）。发布/确认（IFC-194/197）读取库内已规范化的文档，不再产生警告；**发布时 `title` 等于服务端常量 `UNTITLED_PLACEHOLDER = "未命名内容"` 视为标题缺失**（`POST_INCOMPLETE`，`details.missing=["title"]`，ADR-063 第 9 条）。

**内容（posts）**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-190 | GET `/admin/content/posts` | query: `status?`(DRAFT\|PUBLISHED\|OFFLINE)、`q?`(≤100)、`page`、`page_size` | 分页；项 `{id,title,status,style_key,published_at,updated_at,created_by_label,text_confirmed}`（不含 doc） | status 枚举外→400 | `INVALID_QUERY (400)` |
| IFC-191 | POST `/admin/content/posts` | `{title?: str≤200, doc?: object, style_key?: str}` | 201 `PostOut` + `warnings` | `doc` 缺省为空文档；经 `validate_doc_ex`（宽容模式，IFC-169）；style_key 校验 | `CONTENT_INVALID_DOC (400, details:{path,reason,block_index,block_type})`、`STYLE_INVALID (400)` |
| IFC-192 | GET `/admin/content/posts/<id>` | — | `PostOut` = `{id,title,status,style_key,doc,published_at,created_at,updated_at,created_by_label,text_confirmed,media_urls:{<mediaId>:<签名URL>}}` | — | `NOT_FOUND (404)` |
| IFC-193 | PATCH `/admin/content/posts/<id>` | `{title?, doc?, style_key?}`（至少一项） | `PostOut` + `warnings` | 同 IFC-191；空体→400 | `CONTENT_INVALID_DOC`、`STYLE_INVALID`、`INVALID_VALUE (400)`、`NOT_FOUND` |
| IFC-194 | POST `/admin/content/posts/<id>/publish` | `{}` | `PostOut` | — | `POST_INCOMPLETE (400, details.missing)`、`POST_MEDIA_MISSING (400)`、`NOT_FOUND` |
| IFC-195 | POST `/admin/content/posts/<id>/offline` | `{}` | `PostOut` | — | `POST_STATE_INVALID (409)` |
| IFC-196 | DELETE `/admin/content/posts/<id>` | — | 204 | — | `NOT_FOUND` |
| IFC-197 | POST `/admin/content/posts/<id>/confirm-text` | `{}` | `PostOut` | 文案纯文本须非空 | `POST_INCOMPLETE (400)` |
| IFC-198 | POST `/admin/content/preview` | `{doc: object, style_key?: str}` | `{page_count, pages:[{index,html}], media_urls, warnings}` | 同 IFC-191；不落库 | `CONTENT_INVALID_DOC`、`STYLE_INVALID` |

**样式模板**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-199 | GET `/admin/content/style-templates` | — | `[{key,name,builtin,tokens}]`（内置在前） | — | — |
| IFC-200 | POST `/admin/content/style-templates` | `{name, tokens}` | 201 `{key:"custom:<id>",name,builtin:false,tokens}` | name 1~64（空→`STYLE_NAME_REQUIRED`）；tokens 范围见 IFC-172 | `STYLE_NAME_REQUIRED (400)`、`STYLE_NAME_EXISTS (409)`、`STYLE_INVALID (400)` |
| IFC-201 | PUT `/admin/content/style-templates/<id>` | `{name?, tokens?}` | 同上 | 同上 | 同上、`NOT_FOUND` |
| IFC-202 | DELETE `/admin/content/style-templates/<id>` | — | 204 | — | `NOT_FOUND` |

**素材库**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-203 | GET `/admin/content/media` | query: `media_type?`(IMAGE\|VIDEO)、`source?`(UPLOAD\|AI_GENERATED)、`q?`≤100、`page`、`page_size` | 分页；项 `MediaOut` | 枚举外→400 | `INVALID_QUERY (400)` |
| IFC-204 | POST `/admin/content/media` | multipart: `file`(必填)、`title?`(≤255) | 201 `MediaOut` | 扩展名/魔数/大小/配额见 IFC-173；解析器 `MultiPartParser`+`FormParser` | `FILE_TYPE_NOT_ALLOWED (400)`、`FILE_TOO_LARGE (413)`、`MEDIA_QUOTA_EXCEEDED (413)`、`INVALID_VALUE (400)` |
| IFC-205 | PATCH `/admin/content/media/<uuid>` | `{title: str 1~255}` | `MediaOut` | 去空白后非空 | `INVALID_VALUE`、`NOT_FOUND` |
| IFC-206 | DELETE `/admin/content/media/<uuid>` | — | 204 | — | `MEDIA_IN_USE (409, details.posts)`、`NOT_FOUND` |
| IFC-207 | POST `/admin/content/media/<uuid>/save` | `{}` | `MediaOut` | 仅 CANDIDATE→SAVED | `NOT_FOUND` |

`MediaOut = {id, media_type, source, state, title, original_name, size, content_type, url(签名,相对 CONTENT_MEDIA_PATH_PREFIX), created_at, in_use: bool}`。

**服务配置、LLM 选项、提示词模板**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-208 | GET `/admin/content/services` | — | `[ServiceConfigOut]`（4 项，**无任何凭据字段**） | — | — |
| IFC-209 | PUT `/admin/content/services/<service_type>` | `{params?: {model?: str}, secrets?: {<key>: str}, is_default?: bool}` | `ServiceConfigOut` | 见 IFC-182 | `MISSING_FIELDS (400)`、`INVALID_VALUE (400)`、`CREDENTIAL_VAULT_NOT_CONFIGURED (503)`、`NOT_FOUND` |
| IFC-210 | POST `/admin/content/services/<service_type>/test` | `{}` | `{ok, error_code, message}`（同步，≤10 s） | 仅 LLM_* | `NOT_TESTABLE (400)`、`LLM_NOT_CONFIGURED (409)`、`NOT_FOUND` |
| IFC-211 | GET `/admin/content/llm/options` | — | `[{service_type,label,model,is_default}]`（仅测试成功的配置） | — | — |
| IFC-212 | GET `/admin/content/prompt-templates` | — | `[{id,name,prompt,params,updated_at}]` | — | — |
| IFC-213 | POST `/admin/content/prompt-templates` | `{name, prompt, params?}` | 201 同项 | 见 IFC-183 | `PROMPT_EMPTY (400)`、`PROMPT_NAME_EXISTS (409)`、`INVALID_VALUE` |
| IFC-214 | PUT `/admin/content/prompt-templates/<id>` | `{name?, prompt?, params?}` | 同项 | 同上 | 同上、`NOT_FOUND` |
| IFC-215 | DELETE `/admin/content/prompt-templates/<id>` | — | 204 | — | `NOT_FOUND` |

**AI 生成与任务**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-216 | POST `/admin/content/ai/text` | `{prompt: str, service_type?: "LLM_DEEPSEEK"\|"LLM_VOLCANO", template_id?: int, params?: GenParams}` | 202 `JobOut` | prompt 去空白后 1~`content.ai.max_prompt_chars`；temperature 0~1.5 | `PROMPT_EMPTY (400)`、`LLM_NOT_CONFIGURED (409)`、`CODE_RATE_LIMITED (429)`、`INVALID_VALUE` |
| IFC-217 | POST `/admin/content/ai/image` | `{prompt: str, n?: int, size?: str}` | 202 `JobOut` | prompt 1~500；n 1~4；size 正则 `^\d{3,4}x\d{3,4}$` | `PROMPT_EMPTY`、`IMAGE_NOT_CONFIGURED (409)`、`CODE_RATE_LIMITED`、`INVALID_VALUE` |
| IFC-218 | POST `/admin/content/ai/video` | `{post_id: int}` | 202 `JobOut` | 内容存在；文案已确认且非空 | `TEXT_NOT_CONFIRMED (409)`、`VIDEO_NOT_CONFIGURED (409)`、`CODE_RATE_LIMITED`、`NOT_FOUND` |
| IFC-219 | GET `/admin/content/jobs/<id>` | — | `JobOut = {id,kind,status,progress:{step,percent?}\|null,result:object\|null,error_code,error_message,created_by_label,created_at,started_at,finished_at}` | — | `NOT_FOUND` |
| IFC-220 | GET `/admin/content/jobs` | query: `kind?`、`status?`、`page`、`page_size` | 分页 `JobOut`（倒序） | 枚举外→400 | `INVALID_QUERY` |

`JobOut.result` 形态：`LLM_TEXT`→`{text,doc,service_type,model}`；`IMAGE_GEN`→`{media:[MediaOut]}`；`VIDEO_GEN`→`{media:[MediaOut]}`；`DRAFT_PUSH`→`{batch_id}`。任务状态对前端的映射：`QUEUED/RUNNING/WAITING_REMOTE`→"生成中"，`SUCCEEDED`→"成功"，`FAILED`→"失败"+`error_message`。

**平台账户与草稿**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-221 | GET `/admin/content/platform-accounts` | — | `[{platform,label,capability,credential_fields[],account\|null}]`（3 项） | — | — |
| IFC-222 | POST `/admin/content/platform-accounts` | `{platform, display_name, credentials?: {<key>: str}}` | 201 `PlatformAccountOut` | platform ∈ 三者；display_name 1~64；credentials 见 IFC-185 | `PLATFORM_NOT_SUPPORTED (400)`、`PLATFORM_ACCOUNT_EXISTS (409)`、`CREDENTIAL_VAULT_NOT_CONFIGURED (503)`、`INVALID_VALUE` |
| IFC-223 | PATCH `/admin/content/platform-accounts/<id>` | `{display_name?, credentials?}` | `PlatformAccountOut` | 同上，至少一项 | 同上、`NOT_FOUND` |
| IFC-224 | DELETE `/admin/content/platform-accounts/<id>` | — | 204 | — | `NOT_FOUND` |
| IFC-225 | POST `/admin/content/posts/<id>/drafts` | `{account_ids: int[1..3]}` | 202 `{batch_id, job_id\|null, pushes:[DraftPushOut]}` | 非空、去重、均存在 | `NO_PLATFORM_SELECTED (400)`、`POST_NOT_CONFIRMED (409)`、`NOT_FOUND`、`INVALID_VALUE` |
| IFC-226 | POST `/admin/content/drafts/<push_id>/retry` | `{}` | 202 `{job_id, push: DraftPushOut}` | — | `DRAFT_PUSH_STATE_INVALID (409)`、`NOT_FOUND` |
| IFC-227 | GET `/admin/content/posts/<id>/drafts` | query: `batch_id?`(UUID)、`page`、`page_size` | 分页 `DraftPushOut`（倒序） | batch_id 须为 UUID | `INVALID_QUERY` |
| IFC-228 | GET `/admin/content/posts/<id>/export-pack` | query: `platform`(必填) | `application/zip` 附件 | platform ∈ PLATFORMS | `PLATFORM_NOT_SUPPORTED`、`POST_NOT_CONFIRMED (409)` |
| IFC-229 | GET `/admin/content/posts/<id>/copy` | query: `platform`(必填) | `{text, html, unsupported:[…]}` | 同上 | 同上 |

**参数**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-230 | GET `/admin/content/settings` | — | `[SettingItem]` | — | — |
| IFC-231 | PUT `/admin/content/settings` | `{values: {<完整键>: <值>}}` | `[SettingItem]` | 只接受 `content.` 前缀且在规则表中的键；逐键范围见 IFC-168 | `INVALID_VALUE (400, details.key)` |

### MOD-055 用户端 HTTP API

**IFC-232 `GET /info/posts`** — 鉴权：`IsMember`（任意已登录普通账号，含游客身份，REQ-FUNC-100）；未登录 401。query：`page`、`page_size`（≤100）。响应：分页，项 `{id,title,published_at,summary}`，仅 `PUBLISHED`，`published_at` 倒序。

**IFC-233 `GET /info/posts/<id>`** — 鉴权：`IsMember`。query：`fmt`（`html`|`blocks`，缺省 `html`，非法 400 `INVALID_QUERY`）。响应：`{id,title,published_at,page_count,pages:[{index,html}|{index,blocks}],theme?: StyleTokens}`；非 `PUBLISHED`（草稿、已下线）或不存在一律 `NOT_FOUND (404)`（不泄露存在性）。媒体地址为带签名的 URL（HTML 中为含 `CONTENT_MEDIA_PATH_PREFIX` 的绝对路径；`blocks` 中 `src` 为 API 相对路径 `"/content/media/<id>/file?sig=…"`，由小程序拼接自身 API 基址）。

**IFC-234 `GET /content/media/<uuid>/file?sig=<签名>`** — 鉴权：**不使用 Authorization 头**，由 `sig` 授权（限时、仅限该媒体；设计理由见 ADR-052，A-4 待用户确认）；`permission_classes=[AllowAny]`、`authentication_classes=[]`。输入校验：`sig` 必填、≤512 字符；签名无效/过期 → `MEDIA_SIGNATURE_INVALID (403)`；媒体不存在或为 CANDIDATE 且签名无效 → 404；`Range` 头见 IFC-174。响应：文件流（200/206/416）。

### MOD-056 审计动作登记

**IFC-188 `AUDIT_ACTIONS` 增量**（修改现有 `backend/apps/core/audit.py:10-23`）：
`CONTENT_POST_PUBLISHED`、`CONTENT_POST_UPDATED`、`CONTENT_POST_OFFLINED`、`CONTENT_POST_DELETED`、`CONTENT_SERVICE_CONFIG_CHANGED`、`CONTENT_SERVICE_TESTED`、`CONTENT_VIDEO_REQUESTED`、`CONTENT_VIDEO_COMPLETED`、`CONTENT_MEDIA_DELETED`、`CONTENT_PLATFORM_ACCOUNT_CHANGED`、`CONTENT_DRAFT_PUSHED`、`CONTENT_PACK_EXPORTED`。`object_type` 取值：`content_post`、`content_service`、`content_job`、`content_media`、`platform_account`、`content_draft_batch`、`content_pack`。操作人 `AuditActor("ADMIN", admin.id, admin.username)`；worker 内补记使用任务创建者身份。参数变更复用已有动作 `SYSTEM_CONFIG_CHANGED`（`audit.py:22`）。`detail` 禁止放凭据或其片段，仅放键名、对象标题、状态、错误码。

**1.1.0 增量**：`AUDIT_ACTIONS` 再加 `CONTENT_PLATFORM_AUTH_EXPIRED`（共 13 项；`audit.py:10-23` 的集合是 `AuditService.record` 的白名单，未登记会抛 `ValueError`，`audit.py:61-64`）。**审计落点表**（每条审计的唯一写入处与断言点，GROUP_D 据此逐条断言"恰好新增 1 条且 `detail` 不含凭据"；AC 编号取自 GR-C-002 所列）：

| AC / 场景 | 动作 | 写入处（唯一） | 备注 |
|---|---|---|---|
| 发布/修改/下线/删除内容 | `CONTENT_POST_PUBLISHED/UPDATED/OFFLINED/DELETED` | `PostService.publish/update/offline/delete` | 未变 |
| AC-117-04 保存服务凭据 | `CONTENT_SERVICE_CONFIG_CHANGED` | `ServiceConfigService.save` | `detail` 仅键名 |
| AC-118-04 连通测试 | `CONTENT_SERVICE_TESTED` | `ServiceConfigService.test` | |
| AC-124-06 视频申请/完成 | `CONTENT_VIDEO_REQUESTED` / `CONTENT_VIDEO_COMPLETED` | `AiGenerationService.submit_video` / `VideoJobHandler` | 完成由任务创建者身份补记 |
| **AC-122-03 删除素材** | `CONTENT_MEDIA_DELETED` | `MediaService.delete`（**1.1.0 补**） | 同事务；被引用拒绝时不写 |
| AC-126-01/03、AC-127-01 账户增改删与凭据更新 | `CONTENT_PLATFORM_ACCOUNT_CHANGED` | `PlatformAccountService.create/update/delete` | `detail.action ∈ {create, rename, credentials_updated, delete}` |
| 账户被系统置失效（1.1.0 新增） | `CONTENT_PLATFORM_AUTH_EXPIRED` | `PlatformAccountService.mark_expired` | 仅 NORMAL→EXPIRED 时写；actor=任务创建者 |
| **AC-128-07 一键保存批次** | `CONTENT_DRAFT_PUSHED` | 无自动行：`DraftPushService.start_batch`；有自动行：`DraftPushHandler`（含 `on_interrupted`）；均经 `DraftPushService.audit_batch` | **1.1.0：每批次恰 1 条，含全部行（含人工/无凭据）**；`object_id=batch_id` |
| AC-130-04 导出内容包 | `CONTENT_PACK_EXPORTED` | `ExportPackService.build_zip` | 构建成功后写；`copy_payload` 不写审计（口径同 1.0.0） |

### MOD-057 Worker 入口与 systemd 单元

**IFC-189 `manage.py run_content_worker`**
```
python manage.py run_content_worker [--poll-interval 2] [--once] [--max-jobs N]
```
**1.1.0（ADR-063 第 5、6 条）**：**移除 `--concurrency`**（worker 固定单线程串行；传入该参数应报 "unrecognized arguments"，systemd 单元模板本就没有传）；`JobRun(job_name="content_worker")` 心跳**至多每 60 秒写一次**（常量 `HEARTBEAT_INTERVAL_SECONDS = 60`，用单调时钟判断；另在启动时与停止时各写一次），**不得**每个轮询周期写；监控的"心跳过期"阈值为 180 秒。以下 1.0.0 条目中与之冲突的"`--concurrency` 取 1~2"与"每轮更新 `JobRun`"作废：
- 启动时 `register_all_handlers()`（`B/handlers.py`，注册 `TextJobHandler`、`ImageJobHandler`、`VideoJobHandler`、`DraftPushHandler`）；
- 主循环：`claim_next` → `run_one`；无任务时睡眠 `poll-interval` 秒（1~30）；`--concurrency` 取 1~2（线程数，缺省 1）；`--once` 处理完当前可领取的任务后退出（供测试与运维）；
- housekeeping（启动后及每 10 分钟）：`requeue_expired`、`MediaService.housekeeping`、`JobService.purge`；
- 每轮更新 `JobRun(job_name="content_worker")` 心跳（`core/models.py:71-75`，沿用 `run_due_jobs` 的做法）；
- 信号：SIGTERM/SIGINT → 完成当前步骤后退出，退出码 0；未捕获异常 → 非 0，由 systemd `Restart=on-failure` 拉起；
- 鉴权：无（本地命令，仅在服务器上由 systemd 运行）；输入校验：参数范围越界 → `CommandError`。

`deploy/systemd/ocap-content-worker.service`（新建，模板，实际安装由 E1/E2 完成）要点：`After=network-online.target ocap-backend.service`；`Type=simple`；`User=yangyang`；`WorkingDirectory=/home/yangyang/ocap/backend`；`EnvironmentFile=/home/yangyang/ocap/backend/.env`；`ExecStart=/home/yangyang/ocap/backend/venv/bin/python manage.py run_content_worker`；`Restart=on-failure`、`RestartSec=5`；`Nice=10`；`MemoryMax=400M`（`[ESTIMATE]`，E1 实测后调整）；`TimeoutStopSec=150`；`WantedBy=multi-user.target`。单元名前缀 `ocap-`，不触碰 `freeark-*`。

### MOD-058 前端契约文件

**IFC-235 `frontend/src/shared/api.js`**（修改现有；管理端调用放入 `admin` 对象并用 `adminHttp`，用户端放入新增 `infoApi` 并用 `http`）。解析器要求：每个调用写成 `adminHttp.get('/…')` 字面量，路径可含 `${id}`，**不含 `?`**；查询参数传 `{ params }`；Blob 下载传 `{ responseType: 'blob' }`。方法清单（名称 → 方法 路径）：

| 名称 | 方法 路径 | 对应 IFC |
|---|---|---|
| `contentPosts(params)` / `createContentPost(data)` / `contentPost(id)` / `updateContentPost(id,data)` / `publishContentPost(id)` / `offlineContentPost(id)` / `deleteContentPost(id)` / `confirmContentText(id)` / `previewContent(data)` | GET/POST/GET/PATCH/POST/POST/DELETE/POST/POST `/admin/content/posts…`、`/admin/content/preview` | IFC-190~198 |
| `styleTemplates()` / `createStyleTemplate(d)` / `updateStyleTemplate(id,d)` / `deleteStyleTemplate(id)` | `/admin/content/style-templates…` | IFC-199~202 |
| `mediaList(params)` / `uploadMedia(file,title)` / `renameMedia(id,title)` / `deleteMedia(id)` / `saveMedia(id)` | `/admin/content/media…` | IFC-203~207 |
| `contentServices()` / `saveContentService(type,d)` / `testContentService(type)` / `llmOptions()` | `/admin/content/services…`、`/admin/content/llm/options` | IFC-208~211 |
| `promptTemplates()` / `createPromptTemplate(d)` / `updatePromptTemplate(id,d)` / `deletePromptTemplate(id)` | `/admin/content/prompt-templates…` | IFC-212~215 |
| `aiText(d)` / `aiImage(d)` / `aiVideo(d)` / `contentJob(id)` / `contentJobs(params)` | `/admin/content/ai/*`、`/admin/content/jobs…` | IFC-216~220 |
| `platformAccounts()` / `createPlatformAccount(d)` / `updatePlatformAccount(id,d)` / `deletePlatformAccount(id)` | `/admin/content/platform-accounts…` | IFC-221~224 |
| `pushDrafts(postId,accountIds)` / `retryDraft(pushId)` / `draftHistory(postId,params)` / `exportPack(postId,platform)` / `copyPack(postId,platform)` | `/admin/content/posts/${id}/drafts` 等 | IFC-225~229 |
| `contentSettings()` / `updateContentSettings(values)` | `/admin/content/settings` | IFC-230/231 |
| `infoApi.list(params)` / `infoApi.detail(id, fmt)` | `http.get('/info/posts')`、`http.get(\`/info/posts/${id}\`, { fmt })` | IFC-232/233 |

**IFC-236 `miniprogram/utils/api.js`**（修改现有）：`infoPosts(params)` → `http.get('/info/posts', params)`；`infoPost(id)` → `http.get(\`/info/posts/${id}\`, { fmt: 'blocks' })`。媒体 `src` 由组件把 `blocks[].src`（API 相对路径）拼上 `utils/http.js` 的 API 基址（`miniprogram/utils/http.js:1` 的 `BASE`，需把 `BASE` 导出或新增 `mediaUrl(path)` 工具，属 MOD-061）。

### MOD-059 Web 管理端页面

页面与职责（均挂在 `/admin` 子路由，`meta.admin` 继承）：

| 路由 | 组件 | 内容 |
|---|---|---|
| `/admin/content/posts` | `AdminContentPosts.vue` | 列表、按状态筛选、新建、发布/下线/删除（二次确认） |
| `/admin/content/posts/:id` | `AdminContentEditor.vue` | 标题、`RichEditor`、样式模板选择与预览、"确认文案"、AI 生成面板（文案/配图/视频及任务轮询，2 s 间隔、上限 10 min 后提示刷新）、一键保存对话框（平台勾选、逐平台结果、重试、历史、导出/复制） |
| `/admin/content/media` | `AdminMedia.vue` | 筛选（类型/来源）、上传、重命名、删除（被引用时展示拒绝提示与引用内容标题）、AI 候选"保存到素材库" |
| `/admin/content/services` | `AdminAiServices.vue` | 4 类服务配置（凭据输入框为"已保存/覆盖"形态，永不回填）、测试连通、提示词模板管理 |
| `/admin/content/platforms` | `AdminPlatforms.vue` | 三平台账户、认证信息、失效标记。**1.1.0**：公众号表单按 `credential_fields` 渲染 AppID、AppSecret 两个"已保存/覆盖"输入框（永不回填）；页面固定提示"需在公众号后台把本服务器的出口 IP 加入 IP 白名单，否则无法获取令牌"；失败原因展示 `IP_NOT_WHITELISTED`/`TOKEN_BUSY`/`NO_CREDENTIALS` 等的中文文案（状态码不以英文原样显示，F07 末项）；没有"检测有效性"按钮（AC-127-05） |
| `/admin/content/settings` | `AdminContentSettings.vue` | 参数表（"待确认"标签） |

**IFC-237 `RichEditor.vue`**
```ts
// props
interface RichEditorProps { modelValue: DocNode; mediaUrls: Record<string, string>; disabled?: boolean }
// emits
type Emits = { 'update:modelValue': [DocNode]; 'pick-media': [kind: 'image' | 'video'] ; 'request-link': [] }
// 暴露方法
interface RichEditorExposed { insertMedia(kind: 'image' | 'video', mediaId: string, url: string): void; insertPageBreak(): void; clearFormat(): void }
```
编辑器扩展配置：StarterKit（`code: false, codeBlock: false`）+ TextAlign + TextStyle(color/background-color/font-size/line-height) + Image(仅 `mediaId`、`src` 仅用于显示) + 自建 `Video`、`PageBreak`；不装表格/公式/表情/卡片。链接添加前做 `^(https?:\/\/|mailto:|tel:)` 校验，失败提示"网址无效"（AC-109-03）。依赖：`@tiptap/*`（新增 npm，见 tech_stack）。

**1.1.0 修订（ADR-062；F02、F04）**：
- StarterKit 配置追加 `heading: { levels: [1, 2, 3, 4] }`；工具栏标题下拉只给"正文/1~4 级"（`Toolbar.vue:9,79-83` 现有下拉按此收敛）。
- 工具栏文字色、背景色由文本框（`Toolbar.vue:24`）改为 Element Plus 取色器 `el-color-picker`（已有依赖，`color-format="hex"`、`:show-alpha="false"`、含预设色板），另有"清除颜色"项（`unsetColor`/`unsetBackgroundColor`）；取色器输出 `#rrggbb`。
- `Color`、`BackgroundColor` 扩展的 `parseHTML` 以 `toHexColor()`（IFC-241）归一化，返回 `null` 则不设置该属性。
- 粘贴：`editorProps.transformPastedHTML = guardPastedHtml`（IFC-242）；被丢弃的外链图片数量通过 emit `'paste-dropped': [{ images: number }]` 交给页面提示。
- 保存响应的 `warnings`（IFC-191/193）由 `AdminContentEditor.vue` 汇总提示："已自动处理/忽略 N 处不支持的格式：第 3 个块颜色…"（最多列前 3 条位置 + 总数）；`reason`→中文：`COLOR`"颜色格式不支持"、`SIZE`"字号或行距超出范围"、`LINK`"链接地址无效"、`TYPE`"不支持的内容类型"、`MEDIA_ID`"外链图片请通过素材库插入"、`LEVEL`"标题级别已调整为 4 级"；位置文案"第 {block_index+1} 个块（{块类型中文}）"。
- 保存返回 400 `CONTENT_INVALID_DOC` 时，用 `details.block_index/block_type/reason` 生成同样的位置提示。**`publish()`/`confirmText()` 必须在 `await saveDraft()` 成功（未抛错、未 400）之后才继续；保存失败即中止并提示（F02 为实现缺陷，此条是验收口径）。**

**IFC-241 `frontend/src/admin/editor/colors.js`（新建）**
```ts
export function toHexColor(input: unknown): string | null
// 规则与服务端 normalize_color 完全一致（IFC-169 的规则与"共享测试向量"）；非字符串、不匹配 → null
// 测试：frontend/tests/rich_colors.spec.js，使用与后端相同的向量表
```
**IFC-242 `frontend/src/admin/editor/pasteGuard.js`（新建）**
```ts
export interface PasteGuardResult { html: string; droppedImages: number }
export function guardPastedHtml(html: string): PasteGuardResult
// 在 DOMParser 解析出的文档上处理（不用正则改 HTML）：
//   1. 移除所有没有编辑器自身 Image 节点输出的 mediaId 属性的 <img>（外链、data:、blob:），计数；
//   2. 移除 <script>/<style>/<iframe>/<object>/<embed>/<video>/<audio>（视频只能经素材库）；
//   3. 把内联 style 中 color/background-color 的 rgb()/rgba() 归一化为 #hex（toHexColor），无法归一化的删除该声明；
//   4. <h5>/<h6> 不处理（编辑器 levels=[1..4] 使其降为段落）；
//   不做网络请求、不转存图片（ADR-062）
// 剪贴板中的图片文件（截图）不处理：由页面提示"请通过素材库或上传插入图片"
```

### MOD-060 Web 门户页面

`/info`（`InfoList.vue`：列表，调用 `infoApi.list`）、`/info/:id`（`InfoDetail.vue`：调用 `infoApi.detail(id,'html')`，逐页展示，页码与"上一页/下一页"，`v-html` 渲染服务端生成并转义的 HTML；`page_count=1` 时不显示翻页控件，AC-113-04）。路由为 `PortalLayout` 子路由，沿用登录守卫（`router/index.js:48-55`）。入口：`Home.vue` 卡片区新增"信息公开"卡片（修改现有）。

### MOD-061 小程序页面

`pages/info/index.vue`（列表）、`pages/info/detail.vue`（`fmt=blocks`，逐页渲染，上一页/下一页）、`components/RichBlocks.vue`。

**IFC-238 `RichBlocks.vue`**
```ts
interface RichBlocksProps { blocks: Block[]; theme: StyleTokens; apiBase: string }   // Block/Inline 类型同 IFC-170
// 渲染: paragraph/heading → <view><text/></view>（行内样式取自 Inline 白名单属性）；image → <image mode="widthFix" @tap=预览>；
//       video → <video controls :src>；link → 文本带下划线色，@tap 调 uni.setClipboardData 并 uni.showToast("链接已复制，请在浏览器中打开")（A-3）
```
**1.1.0 修订（ADR-063 第 7 条）**：`paragraph`/`heading` 块应用 `Block.lh` 为 `line-height`；`quote.children` 与 `bullet_list/ordered_list.items[][]` 中的 `image`/`video` 块与顶层一样渲染（`<image :src>`、`<video :src>`，`src` 由 `apiBase` 拼接）——不得把它们当作文字或丢弃；`Inline` 同时有 `underline` 与 `strike` 时合并为单个 `text-decoration: underline line-through`；`revokeObjectURL` 等 Web 端细节属实现缺陷，不在本设计范围。
`pages.json` 增加 2 个页面条目；`pages/index/index.vue` 增"信息公开"入口卡片。小程序依赖不变。

### MOD-062 公众号令牌服务（1.1.0 新建）

职责：用已保存的 AppID/AppSecret 换取公众号访问令牌，加密缓存在 `PlatformAccount`，单飞刷新，失效重取，错误分类。文件 `B/wechat_token.py`。依赖 MOD-039、040、041、063。无 HTTP 入口（内部服务）。

**IFC-240 `WechatTokenService`**
```python
class WechatTokenError(Exception):
    code: Literal["NO_CREDENTIALS", "AUTH_REJECTED", "IP_NOT_WHITELISTED", "UPSTREAM", "NETWORK", "TOKEN_BUSY"]
    errcode: int | None
    message: str                         # 已脱敏，≤200 字符

class WechatTokenService:
    @staticmethod
    def get_token(account_id: int, credentials: Mapping[str, str], *, force: bool = False,
                  stale_token: str | None = None, now: datetime | None = None) -> str: ...
    @staticmethod
    def invalidate(account_id: int) -> None: ...      # 清空 token_blob / token_expires_at / token_refreshed_at / token_lock_until
    @staticmethod
    def classify(errcode: int | None) -> Literal["AUTH_REJECTED", "IP_NOT_WHITELISTED", "UPSTREAM"]: ...
        # errcode ∈ content.wechat_mp.ip_errcodes → IP_NOT_WHITELISTED（优先）；∈ auth_errcodes → AUTH_REJECTED；其余（含 None）→ UPSTREAM
```
`get_token` 的行为契约（步骤即验收点）：
1. 账户须存在且 `platform=="wechat_mp"`（否则 `ValueError`，调用方保证）；`credentials` 缺 `appid`/`appsecret` 或为空 → `WechatTokenError("NO_CREDENTIALS")`，不访问网络。
2. **命中缓存**：`force=False` 且 `token_expires_at - token_margin_seconds > now` 且 `token_blob` 可解密 → 返回缓存令牌（解密失败按未命中处理，不抛错）。
3. **强制刷新（`force=True`）**：若缓存仍有效且缓存令牌 `!= stale_token`（他人已刷新）→ 直接返回缓存令牌；若 `token_refreshed_at` 距 `now` 小于 `refresh_cooldown_seconds` 且缓存令牌 `== stale_token` → 不访问网络，抛 `TOKEN_BUSY`（消息"令牌刷新冷却中，请稍后重试"）。
4. **抢锁**：条件 `UPDATE content_platformaccount SET token_lock_until = <锁值> WHERE id=? AND (token_lock_until IS NULL OR token_lock_until < now)`；锁值 = `now + timeout_seconds + 15 秒`；影响行数 1 表示抢到。未抢到：每 0.5 秒重读缓存，至多 10 秒，出现有效令牌则返回，否则抛 `TOKEN_BUSY`。
5. **取令牌**（持锁）：`WechatMpApi.fetch_token(appid, secret, timeout_seconds=content.wechat_mp.timeout_seconds)`（IFC-239）。成功后写缓存：`token_blob = CredentialVault.encrypt({"access_token": t}, context="content_platformaccount_token|<pk>")`，`token_expires_at = now + expires_in 秒`（`expires_in` 缺失/非正数用 7200，[CODE: wechat.py:103]），`token_refreshed_at = now`，同时释放锁；写入使用 `UPDATE ... WHERE id=? AND token_lock_until = <锁值>`，**条件不成立（凭据在取令牌期间被覆盖并执行了 `invalidate`）时丢弃结果**，令牌只供本次调用使用，不入库。
6. **失败映射**：`WechatMpApiError(kind="ERRCODE")` → `classify(errcode)`；`kind="NETWORK"` → `NETWORK`；`kind="BAD_RESPONSE"`/`"HTTP"` → `UPSTREAM`；所有消息经 `SecretRedactor([appsecret, access_token])`；任何路径都在 `finally` 释放锁（`token_lock_until=NULL`，条件同上）。
7. 令牌明文**不得**写入日志、审计、`ContentJob.state/result`、`DraftPush` 任何列、异常消息。
外部依赖：`WechatMpApi`（MOD-063）、`CredentialVault`/`SecretRedactor`（MOD-040）、`ContentSettings`（MOD-041）；标准库 `time`。

### MOD-063 公众号接口客户端（1.1.0 新建）

职责：公众号相关 HTTP 调用的最薄封装，便于以替身测试。文件 `backend/apps/integrations/wechat_mp.py`。依赖 MOD-040（脱敏）。无 HTTP 入口（出站调用）；鉴权：以 AppID/AppSecret 换取的令牌，调用方传入；输入校验：`appid`/`secret` 非空且 ≤4096 字符，`access_token` 非空；超时取 `content.wechat_mp.timeout_seconds`（5~120）。

**IFC-239 `WechatMpApi`**
```python
@dataclass(frozen=True)
class TokenResponse:
    access_token: str                    # 非空
    expires_in: int                      # 秒；响应缺失时由调用方按 7200 处理（[CODE: wechat.py:103]）

class WechatMpApiError(Exception):
    kind: Literal["NETWORK", "HTTP", "BAD_RESPONSE", "ERRCODE"]
    errcode: int | None                  # kind=="ERRCODE" 时有值
    http_status: int | None              # kind=="HTTP" 时有值
    errmsg: str                          # 已脱敏、≤200 字符；响应里"错误描述"字段名无出处 [UNSOURCED]（Q-B1 第 4 项），实现可读取名为 errmsg 的键（现有 draft.py 的做法），读不到则为空串，仅展示 errcode

@dataclass(frozen=True)
class DraftArticle:
    title: str; content: str; author: str = ""
    thumb_media_id: str | None = None    # [UNSOURCED] 字段名与是否必填（Q-B1 第 1 项）；None 时请求体不含该键；仅 upload_cover 开启时才会有值

class WechatMpApi(Protocol):
    def fetch_token(self, *, appid: str, secret: str, timeout_seconds: int) -> TokenResponse: ...
        # GET https://api.weixin.qq.com/cgi-bin/token，查询参数 grant_type=client_credential、appid、secret；
        # 响应 JSON：access_token、expires_in、errcode。出处 [CODE: backend/apps/integrations/wechat.py:97-103]
        # errcode 非零 → ERRCODE；无 access_token → BAD_RESPONSE；网络/超时 → NETWORK
    def add_draft(self, *, access_token: str, article: DraftArticle, timeout_seconds: int) -> str: ...
        # POST https://api.weixin.qq.com/cgi-bin/draft/add，查询参数 access_token，JSON {"articles":[{"title","content","author"}]}；
        # 出处 [P11: publisher/publishers.py:76-79]；响应含非空 media_id → 返回它 [P11: publishers.py:83-87]；
        # HTTP 4xx/5xx → HTTP（参考实现对 HTTP 错误状态视为失败，publishers.py:81）；有 errcode 无 media_id → ERRCODE；其余无 media_id → BAD_RESPONSE
    def upload_cover(self, *, access_token: str, file_path: str, content_type: str, timeout_seconds: int) -> str: ...
        # [UNSOURCED]（Q-B1 第 1 项）：端点、请求与响应字段、格式/大小限制均无出处。仅签名占位；
        # HttpWechatMpApi 中抛 NotImplementedError("UNSOURCED: Q-B1")；返回封面素材编号
    def upload_content_image(self, *, access_token: str, file_path: str, content_type: str, timeout_seconds: int) -> str: ...
        # [UNSOURCED]（Q-B1 第 2 项）：同上；返回微信侧图片地址

def get_wechat_mp_api() -> WechatMpApi: ...
def set_wechat_mp_api(api: WechatMpApi | None) -> None: ...        # 同 wechat.py:143-153 的注入模式
```
泄露面：取令牌的 `secret` 与草稿接口的 `access_token` 都在查询串中（出处同上），`requests` 异常文本会带完整 URL；`HttpWechatMpApi` 捕获 `requests.RequestException` 后只用 `SecretRedactor([secret, access_token]).redact(...)` 与 `redact_url(url)` 构造 `WechatMpApiError`，日志只记 `redact_url(url)`、状态码、耗时。测试只经 `FakeWechatMpApi`（IFC-181），不得走 `HttpWechatMpApi`。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-099 | US-105、US-106 | MOD-045、039、054、056、059 |
| REQ-FUNC-100 | US-107、US-108 | MOD-045、042、044、055、060、061 |
| REQ-FUNC-101 | US-109 | MOD-042、059（RichEditor） |
| REQ-FUNC-102 | US-110 | MOD-042、059（1.1.0：IFC-169 宽容归一化、IFC-241/242 颜色与粘贴） |
| REQ-FUNC-103 | US-111、US-119 | MOD-044、042、059（1.1.0：外链图片丢弃，IFC-242） |
| REQ-FUNC-104 | US-112、US-113 | MOD-043、042、045、059、060、061 |
| REQ-FUNC-105 | US-114 | MOD-051、052、047、054、059 |
| REQ-FUNC-106 | US-116 | MOD-052、047、044、051 |
| REQ-FUNC-107 | US-123、US-124 | MOD-044、052、048 |
| REQ-FUNC-108 | US-115 | MOD-045（confirm_text、草稿状态）、052、059 |
| REQ-FUNC-109 | US-117 | MOD-051、047、054、059 |
| REQ-FUNC-110 | US-118 | MOD-051、047 |
| REQ-FUNC-111 | US-119 | MOD-044、054 |
| REQ-FUNC-112 | US-120 | MOD-044、052 |
| REQ-FUNC-113 | US-121 | MOD-044、045（引用同步）、059（MediaPicker） |
| REQ-FUNC-114 | US-122 | MOD-044、054、059 |
| REQ-FUNC-115 | US-126 | MOD-053、049、054、059 |
| REQ-FUNC-116 | US-127 | MOD-053、040、049、**062、063、039、041**（1.1.0：令牌自动获取与失效口径） |
| REQ-FUNC-117 | US-128 | MOD-053、049、046、057、042、**062、063**（1.1.0；封面/正文图片上传阻塞于 Q-B1） |
| REQ-FUNC-118 | US-129 | MOD-053、057 |
| REQ-FUNC-119 | US-131 | MOD-054（IsAdmin）、055（IsMember）、059、060、061（无入口） |
| REQ-FUNC-120 | US-124 | MOD-052、048、046、057 |
| REQ-FUNC-121 | US-125 | MOD-051、040、048 |
| REQ-FUNC-122 | US-130 | MOD-053（ExportPackService）、049 |
| REQ-NFUNC-016（辅助） | US-117/125/127 | MOD-040、051、053、047~049（脱敏） |
| REQ-NFUNC-017（辅助） | 多个 | MOD-056、045、044、051、052、053（1.1.0：落点表见 IFC-188） |
| REQ-NFUNC-018（辅助） | US-107/108 | MOD-042 |

24 条 REQ-FUNC 全部被至少一个 MOD 覆盖。

## 依赖关系

```
MOD-039 → (无)                 MOD-040 → (无)                 MOD-041 → core
MOD-042 → (无)                 MOD-056 → (无)
MOD-043 → MOD-039
MOD-044 → MOD-039, MOD-041
MOD-045 → MOD-039, 041, 042, 043, 044 (IFC-169~174), MOD-056 (IFC-188)
MOD-046 → MOD-039, MOD-041
MOD-047 → MOD-040 (IFC-167)    MOD-048 → MOD-040              MOD-049 → MOD-040, MOD-062 (IFC-240), MOD-063 (IFC-239)   [1.1.0]
MOD-062 → MOD-039, MOD-040 (IFC-166/167), MOD-041, MOD-063 (IFC-239)   [1.1.0 新增]
MOD-063 → MOD-040 (IFC-167)    [1.1.0 新增]
MOD-050 → MOD-044 (RemoteFetcher), MOD-047, 048, 049, 063 (IFC-239，FakeWechatMpApi)
MOD-051 → MOD-039, 040, 041, 047 (IFC-177)
MOD-052 → MOD-041, 042, 044, 045, 046, 048, 051 (IFC-173/175/176/179/182)
MOD-053 → MOD-039, 040, 041, 042, 043, 044, 045, 046, 049 (IFC-166/171/172/174/175/176/180)
MOD-054 → MOD-041, 043, 044, 045, 046, 051, 052, 053
MOD-055 → MOD-044, 045
MOD-057 → MOD-044, 046, 052, 053
MOD-058 ← 契约对应 MOD-054/055 的 HTTP IFC（无代码依赖）
MOD-059, 060, 061 → MOD-058（经 IFC-235/236 调用 IFC-190~233）
```
已检查：无循环依赖（1.1.0 复核：MOD-062 只向下依赖 039/040/041/063，**不**依赖 MOD-049/053；MOD-049 → MOD-062 单向；`PlatformAccountService.update` 调用 MOD-062 的 `invalidate`，MOD-053 → MOD-062 单向；MOD-044 → MOD-056 仅为审计写入，MOD-056 不依赖任何 content 模块）。注：`backend/apps/integrations/draft.py` 现有对 `apps.content.conf/vault` 的导入（`draft.py:7-8`）是 1.0.0 已有的包级反向引用，模块级无环，1.1.0 沿用并新增对 `apps.content.wechat_token` 的同类导入，`wechat_token` 不导入 `draft`。关键方向——处理器（MOD-052/053）依赖任务核心（MOD-046），任务核心不依赖处理器（经 `register_handler` 注册，由 MOD-057 装配）；素材库（MOD-044）不依赖内容服务（MOD-045），"是否被已发布内容引用"直接查 `ContentPostMedia`/`ContentPost` 模型；富文本引擎（MOD-042）为纯函数，样式令牌与媒体解析器均由调用方传入。

## 数据迁移

- **新增表**（均为新建，无既有表改动）：`content_post`、`content_post_media`、`content_media`、`content_style_template`、`content_prompt_template`、`content_service_config`、`content_platform_account`、`content_job`、`content_draft_push`（字段、唯一约束、索引见 IFC-165）。
- **迁移方式**（画像 P6）：`backend/apps/content/migrations/0001_initial.py` **手写**，单 app 范围，文件头不得含 "Generated by Django"；在 Django 5.2.x 下校验，**不得用 6.x**（画像 P4、CR-023）；提交前 `python manage.py makemigrations --check --dry-run --settings=config.test_settings` 应无漂移；测试不跑迁移（`config/test_settings.py:17` 的 `MIGRATION_MODULES` 置空）。
- **是否可逆**：可逆——反向迁移为 `DROP TABLE` 九张表。数据风险：回滚后已录入的内容、素材记录、加密凭据全部丢失；`var/attachments/content/` 下的文件不会被迁移回滚清理，需人工删除。回滚步骤须标 `[MANUAL_ROLLBACK_REQUIRED: 回滚前必须 mysqldump 九张 content_* 表并备份 var/attachments/content/]`。
- **数据风险**：MySQL DDL 非事务，迁移中途失败需手动清理；`ServiceConfig.service_type`、`PlatformAccount.platform`、`StyleTemplate.name`、`PromptTemplate.name` 的唯一索引（utf8mb4 下 Char(64)≤256 字节）在 MySQL 默认索引长度内；`BinaryField` 在 MySQL 为 `LONGBLOB`。
- **种子数据**：无（内置样式模板是代码常量，ADR-057；不需要 RunPython 数据迁移）。

### 1.1.0 增量：`content` 0002（ADR-060）

- **文件**：`backend/apps/content/migrations/0002_platformaccount_token_cache.py`，**手写**（画像 P6），`dependencies=[("content", "0001_initial")]`，文件头不得含 "Generated by Django"，**不得用 `makemigrations` 生成后提交**（画像 P8），不得在目标机上生成迁移；校验在 Django 5.2.x 下进行（画像 P4、CR-023）。
- **schema 操作**（均为 `AddField`，对 `platformaccount`）：`token_blob = BinaryField(null=True, blank=True)`、`token_expires_at = DateTimeField(null=True, blank=True)`、`token_refreshed_at = DateTimeField(null=True, blank=True)`、`token_lock_until = DateTimeField(null=True, blank=True)`。4 列均可空、无缺省值，对既有行无需回填；字段定义须与 `models.py` 完全一致，否则 `makemigrations --check --dry-run --settings=config.test_settings` 报漂移。
- **数据步骤（可选，Q-B2）**：`RunPython(forward, noop)`：`platform="wechat_mp"` 且 `secret_keys` 不同时包含 `appid` 与 `appsecret` 的行，`auth_status` 置 `"UNSET"`（只读 `secret_keys` 列表，**不解密**）。反向为 no-op。
- **是否可逆**：可逆。反向 = `RemoveField` ×4（MySQL `ALTER TABLE ... DROP COLUMN`）。数据风险：回滚丢失的只是令牌缓存（可由 AppID/AppSecret 重新换取），**不涉及凭据密文**；因此 0002 不需要 `[MANUAL_ROLLBACK_REQUIRED]`（0001 的回滚要求不变）。回滚到 0001 后须同时回退到 1.0.0 代码（其适配器要求 `access_token` 凭据），否则公众号推送会因缺字段失败。
- **执行与锁**：MySQL 上给小表加可空列，毫秒级；随部署的 `manage.py migrate content` 执行。测试环境不跑迁移（`config/test_settings.py` 的 `MIGRATION_MODULES` 置空）。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 说明 |
|---|---|---|
| systemd `ocap-backend`（gunicorn `127.0.0.1:9000`，测试环境） | **重启** | 新代码、新依赖、新路由；`.env` 新增 `CONTENT_CRED_ENC_KEY`（必填，缺失时仅内容中心的凭据保存返回 503，其余功能不受影响）、`CONTENT_CRED_ENC_KEY_PREV`（可选）、`CONTENT_MEDIA_PATH_PREFIX`（测试环境为 `/ocap/api/v1`，须与外部访问路径一致，否则 `<img src>` 404）、`CONTENT_PUBLIC_BASE_URL`（推送/导出用的绝对地址，如外网入口；留空时推送给平台的媒体 URL 无效，见 Q-B1） |
| systemd `ocap-content-worker`（**新增**） | **新增、enable、start** | `deploy/systemd/ocap-content-worker.service`；常驻内存约 60~100 MB `[ESTIMATE]`；部署后必须验证 `is-active`、`JobRun(content_worker)` 心跳；回滚=stop+disable+删除单元文件。**需用户批准（D-1）** |
| `ocap-run-due-jobs.timer` | 不变 | 内容中心清理由 worker housekeeping 承担 |
| MySQL 库 `ocap` | **执行迁移** `content` 0001 | 见"数据迁移" |
| Python 依赖 | `pip install -r requirements.txt` | `backend/requirements.txt` 新增 `cryptography`（见 tech_stack）；需 aarch64 预编译轮子可用，DEPLOY 预检 `pip install --dry-run`（SKILL §4 第 8 项）须通过 |
| 媒体文件目录 | `/home/yangyang/ocap/backend/var/attachments/content/`（`MEDIA_ROOT` 子目录，运行时自动创建） | 部署 tar 已排除 `var`（SKILL DEPLOY-002）；**但 DEPLOY-001 的回滚快照 `tar czf backend-<TS>.tar.gz -C /home/yangyang/ocap backend` 会包含 `var/`**，随素材增长快照变大、磁盘紧张：E1 须在 deployment_plan 中改为排除 `backend/var` 或监控；目标机磁盘总量与剩余未知（预检要求 `/home` 可用 ≥ 2 GB） |
| nginx 站点 `ocap`（8090，`/etc/nginx/sites-available/ocap`） | **需只读核实，可能修改** | `client_max_body_size` 须不小于 `max(image_max, video_max) + 2 MB`（缺省 10 MiB → 至少 12m）；`proxy_read_timeout`/`proxy_send_timeout` 对上传、zip 导出应≥60 s；配置文件不在仓库内，由 PM 只读 ssh 或 E2 预检核实；若需修改：改前备份，`nginx -t` 后 `reload`；**只改 ocap 8090 站点，不改 Freeark 的 nginx 段（`^~ /ocap/` 之外），不碰 Freeark 的服务、端口、目录、库**。外网入口（VPS + frp + Freeark nginx）的体积/超时限制不在本批范围，列为已知限制 |
| gunicorn（`ocap-backend.service` 的 `ExecStart`） | 只读核实 | `--timeout`、`--workers`：同步测试连通 ≤10 s、上传 ≤12 MB、zip 导出，均应小于 `--timeout`（缺省 30 s）；建议不低于 60 s |
| Web 前端 | **重新构建并发布** | `npm install`（新增 `@tiptap/*`）；`npm run build -- --base=/ocap/` 产物替换 `web/ocap`；`VITE_API_BASE=/ocap/api/v1` |
| 微信小程序（RU-4） | **重新构建并发布** | `npm run build:mp-weixin`；发布由用户在微信侧完成；无新增依赖 |
| **1.1.0 增量**：`ocap-backend` 与 `ocap-content-worker` | **均需重启** | 新代码（令牌服务、适配器、宽容校验、审计落点）；worker 命令行参数变化（无 `--concurrency`，单元模板未使用，无需改单元文件）；首次部署后核对 `JobRun(content_worker)` 心跳间隔约 60 秒而非 2 秒 |
| **1.1.0 增量**：数据库迁移 | `migrate content` 追加 0002 | 见"1.1.0 增量：`content` 0002"；回滚快照照旧（DEPLOY-001），回滚到 0001 需配套回退代码 |
| **1.1.0 增量**：`backend/.env` | **无新增键** | 令牌缓存复用 `CONTENT_CRED_ENC_KEY`；AppID/AppSecret 在后台"平台账户"页录入，不进 `.env` |
| **1.1.0 增量**：公众号出口 IP 白名单 | **用户在微信侧配置，不在仓库内** | 树莓派出口 IP 未知且可能变化（家宽/frp）；E2 前用户确认；未配置时取令牌返回 `IP_NOT_WHITELISTED` 类错误（[CODE: wechat.py:13]）；E1 deployment_plan 增"出口 IP 只读核对"项（由 PM 只读 ssh 或用户提供，子代理不 ssh，P9） |
| **1.1.0 增量**：Web 前端 | **重新构建并发布** | 取色器、粘贴守卫、平台表单；**无新增 npm 依赖**（`el-color-picker` 属已有的 Element Plus）；`package-lock.json` 不变 |
| **1.1.0 增量**：小程序 | 重新构建并发布（RU-4） | `RichBlocks.vue` 行距/深层媒体/装饰线；无新增依赖 |
| **1.1.0 增量**：测试机 `/tmp` | 一次性清理 | 旧版 `build_zip` 留下的 `tmp*.zip`（若已部署过 1.0.0 并导出过）由运维只读核对后手工清理；新版不再产生 |
| Freeark 相关一切 | **不变** | 画像 P7/P8 |

## 已知问题（指向开发，1.1.0）

以下为 GR-C-002 中的**实现缺陷**，不需要设计变更，开发直接修复并补测：
- **F01**（CRITICAL）：`backend/apps/content/media.py:179` 类体内 `list` 静态方法遮蔽内建 `list`，`:212` 的注解 `list[tuple[int, str]]` 在 Python 3.12/3.13 类体求值时 `TypeError`（本设计已把方法改名 `list_items`，见 IFC-173）；修复后须在 Python 3.12 与 3.13 各跑一遍后端全量测试（CI 为 3.13）。
- **F02**（MAJOR）：`AdminContentEditor.vue` 的 `publish()`/`confirmText()` 调用 `saveDraft()` 而后者吞掉异常，保存失败仍发布/确认旧版本；验收口径见 IFC-237 "1.1.0 修订"末条。
- F07 其余项（`revokeObjectURL` 立即调用、推送结果表英文状态码、列表内图片在小程序无 `src`）按 IFC-237/238/MOD-059 的 1.1.0 口径实现；"新建内容"默认标题的服务端口径见 IFC-191/193 前的 `UNTITLED_PLACEHOLDER` 说明。

测试文件规划追加（画像 P3）：后端 `backend/tests/unit/test_content_wechat_token.py`（令牌缓存/单飞/冷却/分类，只经 `FakeWechatMpApi`）、`test_content_richtext_lenient.py`（宽容模式与共享向量）、`test_content_export_tempfile.py`；`backend/tests/integration/test_content_audit_points.py`（IFC-188 落点表逐条断言，含素材删除、全人工批次、无凭据批次）；前端 `frontend/tests/rich_colors.spec.js`、`rich_paste_guard.spec.js`；小程序 `miniprogram/tests/rich_blocks.spec.js` 追加行距/深层媒体/装饰线用例。

## 领域与外部依赖出处

画像 P11 不为"无"。参考实现路径前缀见文首。"事实"列只列设计依赖的外部接口事实；未列入者不依赖。

| IFC / MOD | 事实（端点、字段、状态码…） | 出处 |
|---|---|---|
| IFC-180 / MOD-049 `WechatMpDraftAdapter` | 草稿接口 `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=<token>`，JSON `{"articles":[{"title","content","author":""}]}` | [P11: publisher/publishers.py:76-79] |
| 同上 | 成功判定：响应 JSON 含 `media_id`；缺失即失败 | [P11: publisher/publishers.py:83-87] |
| 同上 | 草稿接口的查询参数名 `access_token`（令牌值现由 MOD-062 取得；**1.1.0：凭据字段不再是 `access_token`，改为 appid/appsecret**） | [P11: publisher/publishers.py:71,76] |
| 同上 | 请求超时 30 s | [P11: publisher/publishers.py:72] |
| 同上 | **排除**：`freepublish/submit` 属于正式发布，不调用 | [P11: publisher/publishers.py:88-92]（REQ-FUNC-117 仅草稿） |
| IFC-239 / MOD-063 `fetch_token`（**1.1.0 新增**） | 端点 `GET https://api.weixin.qq.com/cgi-bin/token`；参数 `grant_type=client_credential`、`appid`、`secret`（`secret` 在查询串中） | [CODE: backend/apps/integrations/wechat.py:97-98]（用户/PM 指令 2026-11-11 确认可作公众号取令牌出处；现有调用用的是小程序 AppID） |
| 同上 | 响应字段 `access_token`、`expires_in`（缺省 7200）、`errcode` | [CODE: wechat.py:99-103] |
| IFC-240 / MOD-062 | 令牌提前 300 秒视为过期（缺省 `token_margin_seconds`） | [CODE: wechat.py:94] |
| 同上 / `content.wechat_mp.ip_errcodes` | `errcode` 40164 归类为"IP 不在白名单" | [CODE: wechat.py:13] |
| IFC-240 `classify` / `auth_errcodes`、`token_errcodes` | 取令牌时"AppSecret 错误/被重置"的 `errcode`；草稿接口"令牌无效/过期"的 `errcode` 与 `errmsg` 字段含义 | **[UNSOURCED]**（Q-B1 第 4 项；`errcode` 字段本身的存在有出处 [CODE: wechat.py:59-62]，`errmsg` 字段名与具体取值均无）；默认空，**不得凭记忆填入** |
| IFC-239 `add_draft` | HTTP 错误状态视为失败（参考实现 `raise_for_status`） | [P11: publisher/publishers.py:81] |
| IFC-239 `upload_cover`；`DraftArticle.thumb_media_id` | 封面上传端点、请求/响应字段、格式大小限制；草稿接口封面字段名与是否必填 | **[UNSOURCED]**（Q-B1 第 1 项，`CLARIFICATION_NEEDED` CRITICAL）；仅签名占位，开关 `upload_cover` 缺省关闭，开发不得实现 HTTP 细节 |
| IFC-239 `upload_content_image`；`DraftPayload.html_for` | 正文图片是否必须先上传微信侧、上传端点、响应中的图片地址字段、限制 | **[UNSOURCED]**（Q-B1 第 2 项，同上） |
| 同上 | 草稿正文中视频的嵌入方式 | [UNSOURCED]（Q-B1 第 3 项；A-5 假设"不随正文发送"，仍作为不能保留的样式提示） |
| 同上 | 是否有删除草稿接口 | [UNSOURCED]（Q-B1 第 5 项；设计不依赖它，ADR-054 的"至多一次"策略不变） |
| 参考：线上成功证据 | GenPlatform 仅发 `title/content/author` 的 `draft/add` 调用线上成功过 | [USER P4=是]（画像 P11-3）——**说明"封面必填"尚未被证实**，不能当作已知事实，也不能当作"不需要封面"的保证 |
| IFC-180 / MOD-049 `ManualExportAdapter(xiaohongshu)` | 参考实现的小红书端点为 placeholder，不可作为草稿接口 | [P11: publisher/publishers.py:54]；画像 P11-3 第 139 行（P2=A 人工粘贴） |
| IFC-180 / MOD-049 `ManualExportAdapter(toutiao)` | 参考实现的头条接口为正式发布，不是草稿 | [P11: publisher/publishers.py:121]；画像 P11-3 第 140 行 |
| 同上（两平台） | 认证信息形式 | [UNSOURCED]（A-1；仅预留一个加密保存的可选字段，不使用） |
| IFC-177 / MOD-047 `LlmClient` | DeepSeek base `https://api.deepseek.com/v1`；方舟 base `https://ark.cn-beijing.volces.com/api/v3` | [P11: llm_gateway/providers.py:10-11] |
| 同上 | `POST {base}/chat/completions`，`Authorization: Bearer`，JSON `{model,messages,max_tokens,temperature,stream:true}` | [P11: llm_gateway/providers.py:132-140]（DeepSeek）、[:221-229]（方舟） |
| 同上 | 流式解析：行以 `data:` 开头，`[DONE]` 结束，增量取 `choices[0].delta.content` | [P11: llm_gateway/providers.py:141-154]、[:230-243] |
| 同上 | 超时 120 s | [P11: llm_gateway/providers.py:129,218] |
| 同上 | 连通测试：`GET {base}/models` + Bearer；10 s 超时；200 成功、401 无效、429 配额、其余不可达 | [P11: llm_gateway/providers.py:106-107,191-192]；[P11: settings_vault/ark_validator.py:20-21,44,70-98] |
| 同上 | DeepSeek 对 401/429 的语义与方舟相同 | [ASSUMPTION]（HTTP 通用语义，P11 未单独登记） |
| IFC-182 / MOD-051 `ServiceSpec` | 模型提示清单与默认模型：`deepseek-chat`、`doubao-pro-4k` 等；默认温度 DeepSeek 1.0、方舟 0.7；max_tokens 缺省 4096/2048 | [P11: llm_gateway/providers.py:18-27,83-85,165-167] |
| IFC-178 / MOD-047 `ImageGenClient` | `POST https://ark.cn-beijing.volces.com/api/v3/images/generations`，Bearer，JSON `{model,prompt,n,size,response_format:"url"}` | [P11: image_generator/doubao_image_client.py:30,146-170,187-200] |
| 同上 | 响应 `data[].url`；空列表视为失败 | [P11: image_generator/doubao_image_client.py:249-262] |
| 同上 | 错误映射：401 认证失败、429 配额、400 且 error.code/message 含 `content_filter`/`sensitive`/`审核`/`违规` 为内容审核拒绝 | [P11: image_generator/doubao_image_client.py:207-247] |
| 同上 | 超时 120 s；网络错误重试 1 次（间隔 5 s） | [P11: image_generator/doubao_image_client.py:33,181-205] |
| 同上 | 模型清单 `doubao-seedream-5-0-260128`、`-4-5-251128`、`-4-0-250828`；提示词 1~500 字符、张数 1~4、`size` 缺省 `2048x2048` | [P11: image_generator/doubao_image_client.py:37-44,97,106-108] |
| 同上 | 返回图片格式（是否限于 jpg/png）、结果 URL 有效期 | [UNSOURCED]（设计：下载后按魔数校验，非 jpg/png 判失败 `BAD_FORMAT`；下载立即执行） |
| IFC-179 / MOD-048 `VideoGenClient` | Base `https://visual.volcengineapi.com`、service `visual`、region `cn-north-1`、version `2024-05-01` | [P11: video_generator/jimeng_client.py:14-17] |
| 同上 | 请求签名：HMAC-SHA256，规范请求/待签名串/派生密钥/`Authorization: HMAC-SHA256 Credential=…, SignedHeaders=content-type;host;x-date, Signature=…` | [P11: video_generator/jimeng_client.py:39-85] |
| 同上 | 提交：`Action=CVSubmitTask`，body `{"req_key":"i2v_multi_scene","scenes":[{"prompt","narration","duration","transition"}]}`，响应 `data.task_id` 或顶层 `task_id` | [P11: video_generator/jimeng_client.py:102-131] |
| 同上 | 查询：`Action=CVQueryTask`，body `{"task_id"}`，响应 `data.status`（`queue/processing/succeed/failed`）、`data.video_urls`、`data.progress`、`data.error_message` | [P11: video_generator/jimeng_client.py:133-165] |
| 同上 | 账号信息字段：`access_key`、`secret_key` | [P11: video_generator/jimeng_client.py:35] |
| 同上 | `duration`、`transition` 的合法取值，单次提示长度上限，费用与限流，视频文件格式与 URL 有效期 | [UNSOURCED]（A-6；以可配置参数承载，下载后按魔数校验 mp4，非 mp4 判失败） |
| IFC-173 / MOD-044 | 素材类型/来源的命名参考（image/video、ai_generated/uploaded） | [P11: media_library/models.py:17-33]（仅命名参考，非外部接口） |
| 现有系统事实（INCREMENTAL 基线） | `IsAdmin/IsMember`、`AuditService.record` 白名单与脱敏、附件魔数/分块、`wechat.py` 的 Protocol+注入点、`fakes.py` 的替身风格、契约测试解析规则、`JobRun` 心跳、`RateLimiter.hit`、`page_response` | [CODE: backend/apps/core/permissions.py:19-34]、[CODE: backend/apps/core/audit.py:10-59]、[CODE: backend/apps/core/attachments.py:16-90]、[CODE: backend/apps/integrations/wechat.py:43-48,143-153]、[CODE: backend/apps/integrations/fakes.py:46]、[CODE: backend/tests/integration/test_frontend_contract.py:30-97]、[CODE: backend/apps/core/models.py:71-75]、[CODE: backend/apps/core/ratelimit.py:25-40]、[CODE: backend/apps/core/serializers.py:4-12] |

**1.1.0 结论（取代 1.0.0 此处"无 `[UNSOURCED]` 影响接口签名"的结论）**：上表中 IFC-239 的 `upload_cover`、`upload_content_image`、`DraftArticle.thumb_media_id`，以及 `auth_errcodes`/`token_errcodes` 的取值，**影响接口契约且无出处**，依协议 §N-2 已返回 `CLARIFICATION_NEEDED(CRITICAL)`（architecture_design"开放问题"Q-B1）。这些接口在本文中只有签名占位并标 `[UNSOURCED]`，开关缺省关闭，开发不得实现其 HTTP 细节；取令牌（[CODE: wechat.py:97-103]）与 `draft/add` 的 title/content/author（[P11: publishers.py:76-87]）有出处，可直接实现。其余 `[UNSOURCED]` 行（A-1、A-5、A-6 等）仍为不改变签名的行为细节。小红书、头条的草稿接口**不存在于任何出处**，设计上也未假设其存在（人工粘贴）。
即梦、方舟文生图、LLM 各行出处沿用 1.0.0，本次未改动也未重读这些参考文件；本次只重读了 `publisher/publishers.py:60-99`（公众号部分）与仓库内 `wechat.py`。
