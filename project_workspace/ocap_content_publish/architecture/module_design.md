<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-10T23:44:30+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>requirements/user_stories.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计：信息公开发布与多平台内容中心（INCREMENTAL）

> 编号：MOD-039~061、IFC-165~238（接续基线 MOD-038 / IFC-164）。模块 = 本次新增/修改的代码单元，均注明"新建"或"修改现有"。只写签名、字段、契约，不含函数体。路径相对仓库根；`B/` = `backend/apps/content/`。
> 外部接口出处 `[P11: 文件:行]` 中的文件均位于 `/root/myproject/GenPlatform/project_workspace/content_gen_platform/src/backend/apps/` 下（下称"参考实现"，仓库外，画像 P11-3）。
> 通用约定（所有 HTTP 接口）：错误体 `{code, message, details?}`（`backend/apps/core/errors.py:6-31`，`ApiError`）；分页沿用 `page_response`（`core/serializers.py:4-12`，`page`/`page_size≤100`，响应 `{count,page,page_size,results}`）；认证为 `Authorization: Bearer <token>`（`accounts/authentication.py`）；管理接口用 `IsAdmin`（未登录 401 `UNAUTHORIZED`、业主/游客 403 `FORBIDDEN`，`core/permissions.py:19-25`）；用户接口用 `IsMember`（`:28-34`）；时间为 ISO8601 字符串。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-039 | 数据模型与迁移 | **新建** `B/__init__.py`、`B/apps.py`、`B/models.py`、`B/migrations/__init__.py`、`B/migrations/0001_initial.py`；**修改现有** `backend/config/settings.py`（INSTALLED_APPS、4 个 env 读取） | 定义 9 张表、迁移、应用注册 | 全部 | — |
| MOD-040 | 凭据保险库与脱敏 | **新建** `B/vault.py` | AES-256-GCM 加解密、`SecretRedactor` | REQ-NFUNC-016；US-117/125/127 | — |
| MOD-041 | 内容中心参数 | **新建** `B/conf.py` | 参数默认值、范围校验、读写（基于 `SystemConfig`） | OQ-2、OQ-6；C-29 | core |
| MOD-042 | 富文本引擎 | **新建** `B/richtext/{__init__,schema,render,paginate,convert}.py` | 文档白名单校验、HTML/块/纯文本渲染、分页、文本转文档 | REQ-FUNC-100~104、REQ-NFUNC-018 | — |
| MOD-043 | 样式模板 | **新建** `B/styles.py` | 内置模板常量、自定义模板 CRUD、令牌校验 | REQ-FUNC-104；US-112 | MOD-039 |
| MOD-044 | 素材库 | **新建** `B/media.py` | 上传校验与分块落盘、配额、候选、签名 URL、Range 响应、远程下载守卫、删除保护 | REQ-FUNC-103、111~114；US-111/119~123 | MOD-039、041 |
| MOD-045 | 信息公开内容服务 | **新建** `B/posts.py` | 草稿/发布/下线/删除/确认文案、媒体引用同步、用户端渲染、预览 | REQ-FUNC-099、100、108；US-105~108、113、115 | MOD-039、041~044 |
| MOD-046 | 任务核心 | **新建** `B/jobs.py` | 任务入队/领取/租约/回收/查询、处理器注册表 | REQ-FUNC-117、118、120；ADR-049 | MOD-039、041 |
| MOD-047 | LLM 与文生图客户端 | **新建** `backend/apps/integrations/llm.py`、`backend/apps/integrations/imagegen.py` | Protocol + Http 实现 + `get_/set_` | REQ-FUNC-105、106、109、110 | MOD-040 |
| MOD-048 | 视频生成客户端 | **新建** `backend/apps/integrations/videogen.py` | 即梦提交/轮询（签名）Protocol + Http 实现 | REQ-FUNC-120、121 | MOD-040 |
| MOD-049 | 草稿箱适配器 | **新建** `backend/apps/integrations/draft.py` | `DraftAdapter` Protocol、公众号适配器、小红书/头条人工适配器、注册表 | REQ-FUNC-117、122 | MOD-040 |
| MOD-050 | 测试替身 | **修改现有** `backend/apps/integrations/fakes.py` | 新增 `FakeLlmClient`、`FakeImageGenClient`、`FakeVideoGenClient`、`FakeDraftAdapter`、`FakeRemoteFetcher` | 画像 P4/P11-3 | MOD-044、047~049 |
| MOD-051 | 服务配置与提示词模板 | **新建** `B/services_config.py`、`B/prompts.py` | 4 类服务配置（只写凭据）、LLM 连通测试与可选清单、提示词模板 CRUD | REQ-FUNC-105、109、110、121；US-114、117、118、125 | MOD-039~041、047 |
| MOD-052 | AI 生成任务 | **新建** `B/ai_jobs.py` | 文案/配图/视频的提交校验与任务处理器、分镜构造 | REQ-FUNC-105~108、112、120；US-114~116、120、124 | MOD-041~046、048、051 |
| MOD-053 | 平台账户与草稿推送 | **新建** `B/platforms.py`、`B/drafts.py`、`B/export_pack.py` | 账户 CRUD、一键保存批次与重试、历史、内容包与复制 | REQ-FUNC-115~118、122；US-126~130 | MOD-039~046、049 |
| MOD-054 | 管理端 HTTP API | **新建** `B/views_admin.py`、`B/serializers.py`、`B/urls.py`；**修改现有** `backend/config/urls.py` | 全部 `/admin/content/*` 接口 | REQ-FUNC-099~122（管理侧）、119 | MOD-041、043~046、051~053 |
| MOD-055 | 用户端 HTTP API | **新建** `B/views_member.py`（含 `B/urls.py` 中用户路由） | `/info/posts*`、`/content/media/<id>/file` | REQ-FUNC-100；US-107/108/113 | MOD-044、045 |
| MOD-056 | 审计动作登记 | **修改现有** `backend/apps/core/audit.py`（`AUDIT_ACTIONS` 增 12 项） | 登记新审计动作 | REQ-NFUNC-017 | — |
| MOD-057 | Worker 入口与单元 | **新建** `B/handlers.py`、`B/management/{__init__,commands/__init__,commands/run_content_worker}.py`、`deploy/systemd/ocap-content-worker.service` | 常驻 worker 命令、处理器注册、housekeeping、systemd 单元模板 | REQ-FUNC-117、118、120；ADR-049 | MOD-044、046、052、053 |
| MOD-058 | 前端契约文件 | **修改现有** `frontend/src/shared/api.js`、`miniprogram/utils/api.js` | 新增调用；保持契约测试可解析 | 画像 P6 | — |
| MOD-059 | Web 管理端页面 | **新建** `frontend/src/admin/{AdminContentPosts,AdminContentEditor,AdminMedia,AdminAiServices,AdminPlatforms,AdminContentSettings}.vue`、`frontend/src/admin/editor/{RichEditor.vue,extensions/Video.js,extensions/PageBreak.js,Toolbar.vue,MediaPicker.vue}`；**修改现有** `frontend/src/router/index.js`、`frontend/src/admin/AdminLayout.vue`、`frontend/package.json` | 编辑器、素材库、AI 生成、平台账户、一键保存、参数页 | REQ-FUNC-099~122（界面侧） | MOD-058 |
| MOD-060 | Web 门户页面 | **新建** `frontend/src/portal/{InfoList,InfoDetail}.vue`；**修改现有** `frontend/src/router/index.js`、`frontend/src/portal/Home.vue` | 信息公开列表与分页阅读 | REQ-FUNC-100、104；US-107、113 | MOD-058 |
| MOD-061 | 小程序页面 | **新建** `miniprogram/pages/info/{index,detail}.vue`、`miniprogram/components/RichBlocks.vue`；**修改现有** `miniprogram/pages.json`、`miniprogram/pages/index/index.vue` | 信息公开列表、块渲染、分页 | REQ-FUNC-100、104；US-108、113 | MOD-058 |

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
| `PlatformAccount` | `id`；`platform` Char(16) ∈ `wechat_mp/xiaohongshu/toutiao`；`display_name` Char(64)；`secret_blob` Binary null；`secret_keys` JSON；`auth_status` Char(8) ∈ `UNSET/NORMAL/EXPIRED`；`created_by_admin_id`；`created_at`、`updated_at` | 唯一 `platform`（每平台至多 1 个账户，AC-126-02） |
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
| `content.wechat_mp.auth_errcodes` | `[]` | 整数列表 | `[UNSOURCED]`（Q-A3） |

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

def validate_doc(doc: Any, *, max_bytes: int) -> Node: ...
    # 返回规范化后的新文档（深拷贝、剔除未知节点/属性、合并空 text）；非法 → DocValidationError
    # 空文档 {"type":"doc","content":[]} 合法（草稿可为空）
```

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

def render_html(doc: Node, tokens: StyleTokens, *, mode: Literal["web", "inline"],
                resolve: MediaResolver) -> str: ...
    # web: <article class="rt-article" style="--rt-…"> + 带 class 的元素；inline: 所有样式内联、无 class/<style>/<script>
    # 所有文本与属性值经 html.escape；a 标签固定加 rel="noopener noreferrer nofollow" target="_blank"
    # 素材缺失：image/video 渲染为 "[素材已删除]" 文本段，不输出空 src
def render_blocks(doc: Node, resolve: MediaResolver) -> list[Block]: ...
def render_text(doc: Node) -> str: ...        # 纯文本，段落间空行；用于复制、内容包、摘要、文案确认摘要
```

**IFC-171 分页与转换**（`paginate.py`、`convert.py`）
```python
def paginate(doc: Node, page_chars: int) -> list[Node]: ...
    # 先按 pageBreak 切；再按顶层块累计 text 字符数，≥ page_chars 即在该块之后换页；不拆分单个块；空页丢弃；至少返回 1 页
def text_to_doc(text: str) -> Node: ...        # 空行分段→paragraph；以 "#"~"####" 开头的行→heading；其余行内换行→hardBreak
def extract_media_ids(doc: Node) -> list[UUID]: ...
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
    def list(*, media_type: str | None, source: str | None, q: str | None) -> QuerySet[MediaItem]: ...   # 仅 state=SAVED
    @staticmethod
    def rename(media_id: UUID, title: str) -> MediaItem: ...
    @staticmethod
    def save_candidate(media_id: UUID) -> MediaItem: ...       # CANDIDATE→SAVED；已 SAVED 幂等
    @staticmethod
    def published_usage(media_id: UUID) -> list[tuple[int, str]]: ...   # 引用它的 PUBLISHED 内容 (id, title)
    @staticmethod
    def delete(media_id: UUID, *, admin_id: int) -> None: ...  # 有已发布引用 → ApiError("MEDIA_IN_USE", 409, details={"posts": [{"id","title"}...≤10]})；先删行后删文件；删 ContentPostMedia
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
    def heartbeat(self) -> None: ...                               # 延长租约

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

@dataclass(frozen=True)
class DraftOutcome:
    status: Literal["SAVED", "AUTH_EXPIRED", "FAILED"]
    remote_ref: str = ""; error_code: str = ""; message: str = ""     # message 已脱敏

class DraftAdapter(Protocol):
    platform: str; label: str; capability: Capability
    credential_fields: tuple[CredentialField, ...]
    unsupported_features: frozenset[str]          # 见 IFC-171 的特征名
    def save_draft(self, payload: DraftPayload, credentials: Mapping[str, str]) -> DraftOutcome: ...
        # capability=="MANUAL_EXPORT" 的适配器：save_draft 抛 NotImplementedError，服务层从不调用

PLATFORMS: tuple[str, ...] = ("wechat_mp", "xiaohongshu", "toutiao")
def get_draft_adapter(platform: str) -> DraftAdapter: ...              # 未知平台 → KeyError（服务层转 PLATFORM_NOT_SUPPORTED）
def set_draft_adapter(platform: str, adapter: DraftAdapter | None) -> None: ...   # 测试/日后接入自动草稿
```
内置适配器：
- `WechatMpDraftAdapter`：`capability="AUTO_DRAFT"`，`credential_fields=(CredentialField("access_token","访问令牌"),)`；`save_draft` 仅发 `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=<token>`，JSON `{"articles":[{"title": title, "content": html, "author": ""}]}`，超时 `content.wechat_mp.timeout_seconds`；响应 JSON 含非空 `media_id` → `SAVED(remote_ref=media_id)`；HTTP 401/403，或响应 JSON 的 `errcode` ∈ `content.wechat_mp.auth_errcodes` → `AUTH_EXPIRED`；其余 → `FAILED(error_code="UPSTREAM", message=脱敏后的响应摘要≤200 字符)`；网络异常 → `FAILED(error_code="NETWORK")`。**不调用 `freepublish/submit`**。`unsupported_features=frozenset({"page_break","video"})`（A-5，`[ASSUMPTION]`）。
- `ManualExportAdapter(platform, label)`：用于 `xiaohongshu`（"小红书"）、`toutiao`（"今日头条"）；`capability="MANUAL_EXPORT"`；`credential_fields=(CredentialField("credential","认证信息（预留）", required=False),)`（A-1）；`unsupported_features=frozenset()`（内容包的固有限制由服务层固定追加，见 IFC-186）。

### MOD-050 测试替身（`backend/apps/integrations/fakes.py`，修改现有）

**IFC-181 新增替身**（沿用 `FakeWeChatClient` 风格：内存记录调用、可编程失败、`reset()`）：
```python
class FakeLlmClient:        # 实现 LlmClient
    responses: list[str]; fail_code: str | None; test_result: LlmTestResult; calls: list[dict]   # calls 不记录 api_key 值，只记录其是否非空
    def reset(self) -> None: ...
class FakeImageGenClient:   # 实现 ImageGenClient；urls: list[str]；fail_code
class FakeVideoGenClient:   # 实现 VideoGenClient；submit_task_id: str；statuses: list[VideoTaskStatus]（逐次 poll 取下一个）；fail_on: Literal["submit","poll"] | None
class FakeDraftAdapter:     # 实现 DraftAdapter；构造参数 platform/capability/outcomes: list[DraftOutcome]；received: list[DraftPayload]；
                            # 用 set_draft_adapter 注入，可模拟 AUTH_EXPIRED / FAILED
class FakeRemoteFetcher:    # 实现 RemoteFetcher；payloads: dict[str, bytes]；未知 URL → MediaFetchError("HTTP")
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
    def build_scenes(text: str, *, max_scenes: int, scene_seconds: int, transition: str) -> list[VideoScene]: ...
        # 按空行分段；段数>max_scenes 时按字符数均衡合并相邻段；每段 scene_prompt=narration=该段文本；duration_sec=scene_seconds
    @staticmethod
    def compose_messages(prompt: str, params: GenParams) -> list[ChatMessage]: ...   # system 提示由服务端固定模板 + 语气/篇幅提示；user=prompt

class TextJobHandler:   kind="LLM_TEXT";   idempotent=True    # 结果 {"text","doc","service_type","model"}；LlmError→Fail(code 同 LlmError.code)
class ImageJobHandler:  kind="IMAGE_GEN";  idempotent=True    # 结果 {"media_ids":[uuid…]}；每个 URL 经 fetch_remote→store_stream(state=CANDIDATE, source=AI_GENERATED)；格式非 jpg/png → Fail("BAD_FORMAT")
class VideoJobHandler:  kind="VIDEO_GEN";  idempotent=False   # 见 ADR-055 状态机；断点 state={"task_id","phase","submitted_at"}；
                                                              # 成功后每个片段 → store_stream(VIDEO, SAVED, AI_GENERATED, ai_video_max_bytes)；写审计 CONTENT_VIDEO_COMPLETED（actor=任务创建者）
```
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
    @staticmethod
    def delete(account_id: int, admin) -> None: ...             # DraftPush.account 置空保留历史；审计
    @staticmethod
    def credentials_of(account_id: int) -> dict[str, str]: ...  # 仅内部使用
    @staticmethod
    def mark_expired(account_id: int) -> None: ...
```
输入校验：`display_name` 去空白后 1~64 字符；`credentials` 键须属于该平台 `credential_fields`，值 1~4096 字符，否则 `INVALID_VALUE`。

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
        # 存在 PENDING 行则入队一个 DRAFT_PUSH 任务（payload={"push_ids":[…]}）
    @staticmethod
    def retry(push_id: int, admin) -> tuple[int, DraftPushOut]: ...   # 仅 FAILED/UNKNOWN 且 mode=AUTO；新建行(retry_of)+入队；否则 DRAFT_PUSH_STATE_INVALID(409)
    @staticmethod
    def history(post_id: int, *, batch_id: str | None) -> QuerySet[DraftPush]: ...
    @staticmethod
    def build_payload(post: ContentPost, adapter: DraftAdapter) -> DraftPayload: ...   # render_html(mode="inline")，媒体 URL 为 absolute 签名 URL(push_url_ttl_seconds)

class DraftPushHandler:   kind="DRAFT_PUSH"; idempotent=False
    # 逐行处理: 置 SENDING → 解密凭据 → adapter.save_draft → 置 SAVED/FAILED/（AUTH_EXPIRED: FAILED + account.mark_expired）
    # 单行异常不影响其他行；全部结束写一条审计 CONTENT_DRAFT_PUSHED（detail.results=[{platform,status,error_code}]）
    # on_interrupted: 仍为 SENDING 的行置 UNKNOWN（"结果未知，请到平台草稿箱核对后重试"），PENDING 的行置 FAILED(INTERRUPTED)
```
**IFC-187 `ExportPackService`**
```python
class ExportPackService:
    @staticmethod
    def build_zip(post: ContentPost, platform: str, admin) -> tuple[IO[bytes], str]: ...
        # 返回 (临时文件对象, 下载文件名)；内含 content.txt、content.html、media/NN_<name>、README.txt；媒体用 ZIP_STORED
        # 平台须在 PLATFORMS 且 capability=="MANUAL_EXPORT"（AUTO 平台也允许导出，供失败兜底，不限制）
        # PostService.is_confirmed 否则 POST_NOT_CONFIRMED；写审计 CONTENT_PACK_EXPORTED
    @staticmethod
    def copy_payload(post: ContentPost, platform: str) -> dict: ...      # {"text": str, "html": str, "unsupported": list[str]}
```
外部依赖：标准库 `zipfile`、`tempfile`；`requests`（仅 `WechatMpDraftAdapter`）。

### MOD-054 管理端 HTTP API

职责：薄视图，权限 `IsAdmin`，序列化，错误码映射。`B/urls.py` 由 `backend/config/urls.py` 以 `path("api/v1/", include("apps.content.urls"))` 引入（修改现有）。路径中 `<id>` 为整数，`<uuid>` 为 UUID。**所有接口鉴权：`IsAdmin`（沿用现有管理员令牌，`core/permissions.py:19-25`）；未登录 401、非管理员 403。**

以下表格给出请求/响应契约；"校验"列为输入校验，"错误"列为 `code (HTTP)`。

**内容（posts）**

| IFC | 方法 路径 | 请求 | 响应 | 校验 | 错误 |
|---|---|---|---|---|---|
| IFC-190 | GET `/admin/content/posts` | query: `status?`(DRAFT\|PUBLISHED\|OFFLINE)、`q?`(≤100)、`page`、`page_size` | 分页；项 `{id,title,status,style_key,published_at,updated_at,created_by_label,text_confirmed}`（不含 doc） | status 枚举外→400 | `INVALID_QUERY (400)` |
| IFC-191 | POST `/admin/content/posts` | `{title?: str≤200, doc?: object, style_key?: str}` | 201 `PostOut` | `doc` 缺省为空文档；经 validate_doc；style_key 校验 | `CONTENT_INVALID_DOC (400)`、`STYLE_INVALID (400)` |
| IFC-192 | GET `/admin/content/posts/<id>` | — | `PostOut` = `{id,title,status,style_key,doc,published_at,created_at,updated_at,created_by_label,text_confirmed,media_urls:{<mediaId>:<签名URL>}}` | — | `NOT_FOUND (404)` |
| IFC-193 | PATCH `/admin/content/posts/<id>` | `{title?, doc?, style_key?}`（至少一项） | `PostOut` | 同 IFC-191；空体→400 | `CONTENT_INVALID_DOC`、`STYLE_INVALID`、`INVALID_VALUE (400)`、`NOT_FOUND` |
| IFC-194 | POST `/admin/content/posts/<id>/publish` | `{}` | `PostOut` | — | `POST_INCOMPLETE (400, details.missing)`、`POST_MEDIA_MISSING (400)`、`NOT_FOUND` |
| IFC-195 | POST `/admin/content/posts/<id>/offline` | `{}` | `PostOut` | — | `POST_STATE_INVALID (409)` |
| IFC-196 | DELETE `/admin/content/posts/<id>` | — | 204 | — | `NOT_FOUND` |
| IFC-197 | POST `/admin/content/posts/<id>/confirm-text` | `{}` | `PostOut` | 文案纯文本须非空 | `POST_INCOMPLETE (400)` |
| IFC-198 | POST `/admin/content/preview` | `{doc: object, style_key?: str}` | `{page_count, pages:[{index,html}], media_urls}` | 同 IFC-191；不落库 | `CONTENT_INVALID_DOC`、`STYLE_INVALID` |

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

### MOD-057 Worker 入口与 systemd 单元

**IFC-189 `manage.py run_content_worker`**
```
python manage.py run_content_worker [--poll-interval 2] [--concurrency 1] [--once] [--max-jobs N]
```
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
| `/admin/content/platforms` | `AdminPlatforms.vue` | 三平台账户、认证信息、失效标记 |
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
`pages.json` 增加 2 个页面条目；`pages/index/index.vue` 增"信息公开"入口卡片。小程序依赖不变。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-099 | US-105、US-106 | MOD-045、039、054、056、059 |
| REQ-FUNC-100 | US-107、US-108 | MOD-045、042、044、055、060、061 |
| REQ-FUNC-101 | US-109 | MOD-042、059（RichEditor） |
| REQ-FUNC-102 | US-110 | MOD-042、059 |
| REQ-FUNC-103 | US-111、US-119 | MOD-044、042、059 |
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
| REQ-FUNC-116 | US-127 | MOD-053、040、049 |
| REQ-FUNC-117 | US-128 | MOD-053、049、046、057、042 |
| REQ-FUNC-118 | US-129 | MOD-053、057 |
| REQ-FUNC-119 | US-131 | MOD-054（IsAdmin）、055（IsMember）、059、060、061（无入口） |
| REQ-FUNC-120 | US-124 | MOD-052、048、046、057 |
| REQ-FUNC-121 | US-125 | MOD-051、040、048 |
| REQ-FUNC-122 | US-130 | MOD-053（ExportPackService）、049 |
| REQ-NFUNC-016（辅助） | US-117/125/127 | MOD-040、051、053、047~049（脱敏） |
| REQ-NFUNC-017（辅助） | 多个 | MOD-056、045、044、051、052、053 |
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
MOD-047 → MOD-040 (IFC-167)    MOD-048 → MOD-040              MOD-049 → MOD-040
MOD-050 → MOD-044 (RemoteFetcher), MOD-047, 048, 049
MOD-051 → MOD-039, 040, 041, 047 (IFC-177)
MOD-052 → MOD-041, 042, 044, 045, 046, 048, 051 (IFC-173/175/176/179/182)
MOD-053 → MOD-039, 040, 041, 042, 043, 044, 045, 046, 049 (IFC-166/171/172/174/175/176/180)
MOD-054 → MOD-041, 043, 044, 045, 046, 051, 052, 053
MOD-055 → MOD-044, 045
MOD-057 → MOD-044, 046, 052, 053
MOD-058 ← 契约对应 MOD-054/055 的 HTTP IFC（无代码依赖）
MOD-059, 060, 061 → MOD-058（经 IFC-235/236 调用 IFC-190~233）
```
已检查：无循环依赖。关键方向——处理器（MOD-052/053）依赖任务核心（MOD-046），任务核心不依赖处理器（经 `register_handler` 注册，由 MOD-057 装配）；素材库（MOD-044）不依赖内容服务（MOD-045），"是否被已发布内容引用"直接查 `ContentPostMedia`/`ContentPost` 模型；富文本引擎（MOD-042）为纯函数，样式令牌与媒体解析器均由调用方传入。

## 数据迁移

- **新增表**（均为新建，无既有表改动）：`content_post`、`content_post_media`、`content_media`、`content_style_template`、`content_prompt_template`、`content_service_config`、`content_platform_account`、`content_job`、`content_draft_push`（字段、唯一约束、索引见 IFC-165）。
- **迁移方式**（画像 P6）：`backend/apps/content/migrations/0001_initial.py` **手写**，单 app 范围，文件头不得含 "Generated by Django"；在 Django 5.2.x 下校验，**不得用 6.x**（画像 P4、CR-023）；提交前 `python manage.py makemigrations --check --dry-run --settings=config.test_settings` 应无漂移；测试不跑迁移（`config/test_settings.py:17` 的 `MIGRATION_MODULES` 置空）。
- **是否可逆**：可逆——反向迁移为 `DROP TABLE` 九张表。数据风险：回滚后已录入的内容、素材记录、加密凭据全部丢失；`var/attachments/content/` 下的文件不会被迁移回滚清理，需人工删除。回滚步骤须标 `[MANUAL_ROLLBACK_REQUIRED: 回滚前必须 mysqldump 九张 content_* 表并备份 var/attachments/content/]`。
- **数据风险**：MySQL DDL 非事务，迁移中途失败需手动清理；`ServiceConfig.service_type`、`PlatformAccount.platform`、`StyleTemplate.name`、`PromptTemplate.name` 的唯一索引（utf8mb4 下 Char(64)≤256 字节）在 MySQL 默认索引长度内；`BinaryField` 在 MySQL 为 `LONGBLOB`。
- **种子数据**：无（内置样式模板是代码常量，ADR-057；不需要 RunPython 数据迁移）。

## 受影响的运行单元 / 构建

| 运行单元 | 影响 | 说明 |
|---|---|---|
| systemd `ocap-backend`（gunicorn `127.0.0.1:9000`，测试环境） | **重启** | 新代码、新依赖、新路由；`.env` 新增 `CONTENT_CRED_ENC_KEY`（必填，缺失时仅内容中心的凭据保存返回 503，其余功能不受影响）、`CONTENT_CRED_ENC_KEY_PREV`（可选）、`CONTENT_MEDIA_PATH_PREFIX`（测试环境为 `/ocap/api/v1`，须与外部访问路径一致，否则 `<img src>` 404）、`CONTENT_PUBLIC_BASE_URL`（推送/导出用的绝对地址，如外网入口；留空时推送给平台的媒体 URL 无效，Q-A2） |
| systemd `ocap-content-worker`（**新增**） | **新增、enable、start** | `deploy/systemd/ocap-content-worker.service`；常驻内存约 60~100 MB `[ESTIMATE]`；部署后必须验证 `is-active`、`JobRun(content_worker)` 心跳；回滚=stop+disable+删除单元文件。**需用户批准（D-1）** |
| `ocap-run-due-jobs.timer` | 不变 | 内容中心清理由 worker housekeeping 承担 |
| MySQL 库 `ocap` | **执行迁移** `content` 0001 | 见"数据迁移" |
| Python 依赖 | `pip install -r requirements.txt` | `backend/requirements.txt` 新增 `cryptography`（见 tech_stack）；需 aarch64 预编译轮子可用，DEPLOY 预检 `pip install --dry-run`（SKILL §4 第 8 项）须通过 |
| 媒体文件目录 | `/home/yangyang/ocap/backend/var/attachments/content/`（`MEDIA_ROOT` 子目录，运行时自动创建） | 部署 tar 已排除 `var`（SKILL DEPLOY-002）；**但 DEPLOY-001 的回滚快照 `tar czf backend-<TS>.tar.gz -C /home/yangyang/ocap backend` 会包含 `var/`**，随素材增长快照变大、磁盘紧张：E1 须在 deployment_plan 中改为排除 `backend/var` 或监控；目标机磁盘总量与剩余未知（预检要求 `/home` 可用 ≥ 2 GB） |
| nginx 站点 `ocap`（8090，`/etc/nginx/sites-available/ocap`） | **需只读核实，可能修改** | `client_max_body_size` 须不小于 `max(image_max, video_max) + 2 MB`（缺省 10 MiB → 至少 12m）；`proxy_read_timeout`/`proxy_send_timeout` 对上传、zip 导出应≥60 s；配置文件不在仓库内，由 PM 只读 ssh 或 E2 预检核实；若需修改：改前备份，`nginx -t` 后 `reload`；**只改 ocap 8090 站点，不改 Freeark 的 nginx 段（`^~ /ocap/` 之外），不碰 Freeark 的服务、端口、目录、库**。外网入口（VPS + frp + Freeark nginx）的体积/超时限制不在本批范围，列为已知限制 |
| gunicorn（`ocap-backend.service` 的 `ExecStart`） | 只读核实 | `--timeout`、`--workers`：同步测试连通 ≤10 s、上传 ≤12 MB、zip 导出，均应小于 `--timeout`（缺省 30 s）；建议不低于 60 s |
| Web 前端 | **重新构建并发布** | `npm install`（新增 `@tiptap/*`）；`npm run build -- --base=/ocap/` 产物替换 `web/ocap`；`VITE_API_BASE=/ocap/api/v1` |
| 微信小程序（RU-4） | **重新构建并发布** | `npm run build:mp-weixin`；发布由用户在微信侧完成；无新增依赖 |
| Freeark 相关一切 | **不变** | 画像 P7/P8 |

## 领域与外部依赖出处

画像 P11 不为"无"。参考实现路径前缀见文首。"事实"列只列设计依赖的外部接口事实；未列入者不依赖。

| IFC / MOD | 事实（端点、字段、状态码…） | 出处 |
|---|---|---|
| IFC-180 / MOD-049 `WechatMpDraftAdapter` | 草稿接口 `POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=<token>`，JSON `{"articles":[{"title","content","author":""}]}` | [P11: publisher/publishers.py:76-79] |
| 同上 | 成功判定：响应 JSON 含 `media_id`；缺失即失败 | [P11: publisher/publishers.py:83-87] |
| 同上 | 凭据字段名 `access_token`（令牌由调用方提供） | [P11: publisher/publishers.py:71] |
| 同上 | 请求超时 30 s | [P11: publisher/publishers.py:72] |
| 同上 | **排除**：`freepublish/submit` 属于正式发布，不调用 | [P11: publisher/publishers.py:88-92]（REQ-FUNC-117 仅草稿） |
| 同上 | 令牌获取/续期流程、令牌有效期 | [UNSOURCED]（Q-A1；设计为"管理员手工录入/覆盖"，不实现获取流程） |
| 同上 | "认证失效"的错误码/判定；`errcode`/`errmsg` 字段名 | [UNSOURCED]（Q-A3；以 HTTP 401/403 + 可配置 `content.wechat_mp.auth_errcodes` 判定，缺省空） |
| 同上 | 草稿正文中图片是否须托管于平台、视频嵌入方式、封面字段 | [UNSOURCED]（Q-A2、A-5；按参考实现只发 title/content/author，视频不随正文发送） |
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

**无 `[UNSOURCED]` 影响接口签名的项**：上表所有 `[UNSOURCED]` 行均为行为细节（令牌续期、错误码、媒体嵌入、取值范围），已转成可配置参数、兜底路径或开放问题（architecture_design"开放问题"Q-A1~Q-A3、A-1、A-5、A-6），不改变本文任何 IFC 的类型签名；因此不触发 `CLARIFICATION_NEEDED(CRITICAL)`。小红书、头条的草稿接口**不存在于任何出处**，设计上也未假设其存在（人工粘贴）。
