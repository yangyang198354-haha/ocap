<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-11T00:29:19+08:00</timestamp>
  <project_name>ocap_content_publish</project_name>
  <version>1.0.0</version>
  <input_files><file>requirements/requirements_spec.md</file><file>requirements/user_stories.md</file><file>architecture/architecture_design.md</file><file>architecture/module_design.md</file><file>architecture/tech_stack.md</file></input_files>
  <phase>PHASE_05</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：信息公开与多平台内容中心（GROUP_C）

## 范围

按已批准设计实现 MOD-039~061：9 张新表、凭据保险库、富文本引擎、样式模板、素材库、内容状态机、任务队列、LLM/文生图/视频/草稿适配器、管理端与用户端 API、常驻 worker、Web 管理端与门户、小程序页面。

## 架构落地对照

| MOD | 文件 | 状态 |
|---|---|---|
| MOD-039 数据模型与迁移 | `backend/apps/content/{models.py,migrations/0001_initial.py}`、`config/settings.py` | DONE |
| MOD-040 凭据保险库 | `backend/apps/content/vault.py` | DONE |
| MOD-041 内容参数 | `backend/apps/content/conf.py` | DONE |
| MOD-042 富文本引擎 | `backend/apps/content/richtext/*` | DONE |
| MOD-043 样式模板 | `backend/apps/content/styles.py` | DONE |
| MOD-044 素材库 | `backend/apps/content/media.py` | DONE |
| MOD-045 内容服务 | `backend/apps/content/posts.py` | DONE |
| MOD-046 任务核心 | `backend/apps/content/jobs.py` | DONE |
| MOD-047 LLM/文生图客户端 | `backend/apps/integrations/{llm,imagegen}.py` | DONE |
| MOD-048 视频客户端 | `backend/apps/integrations/videogen.py` | DONE |
| MOD-049 草稿适配器 | `backend/apps/integrations/draft.py` | DONE |
| MOD-050 测试替身 | `backend/apps/integrations/fakes.py` | DONE |
| MOD-051 服务配置/提示词 | `backend/apps/content/{services_config,prompts}.py` | DONE |
| MOD-052 AI 任务 | `backend/apps/content/ai_jobs.py` | DONE |
| MOD-053 平台账户/草稿/导出 | `backend/apps/content/{platforms,drafts,export_pack}.py` | DONE |
| MOD-054 管理端 API | `backend/apps/content/{views_admin,serializers,urls}.py`、`config/urls.py` | DONE |
| MOD-055 用户端 API | `backend/apps/content/views_member.py` | DONE |
| MOD-056 审计动作 | `backend/apps/core/audit.py` | DONE |
| MOD-057 Worker | `backend/apps/content/{handlers.py,management/commands/run_content_worker.py}`、`deploy/systemd/ocap-content-worker.service` | DONE |
| MOD-058 前端契约 | `frontend/src/shared/api.js`、`miniprogram/utils/api.js` | DONE |
| MOD-059 Web 管理端 | `frontend/src/admin/{AdminContentPosts,AdminContentEditor,AdminMedia,AdminAiServices,AdminPlatforms,AdminContentSettings}.vue`、`admin/editor/*`、`router/index.js`、`AdminLayout.vue` | DONE |
| MOD-060 Web 门户 | `frontend/src/portal/{InfoList,InfoDetail}.vue`、`Home.vue`、`router/index.js` | DONE |
| MOD-061 小程序 | `miniprogram/pages/info/*`、`components/RichBlocks.vue`、`pages.json`、`pages/index/index.vue` | DONE |

## 需求追溯

| US | AC | 实现位置 | 状态 |
|---|---|---|---|
| US-105 | AC-105-01 | backend/apps/content/{posts,views_admin,serializers,urls}.py；frontend/src/admin/{AdminContentPosts,AdminContentEditor}.vue | DONE |
| US-105 | AC-105-02 | backend/apps/content/{posts,views_admin,serializers,urls}.py；frontend/src/admin/{AdminContentPosts,AdminContentEditor}.vue | DONE |
| US-105 | AC-105-03 | backend/apps/content/{posts,views_admin,serializers,urls}.py；frontend/src/admin/{AdminContentPosts,AdminContentEditor}.vue | DONE |
| US-106 | AC-106-01 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentPosts.vue | DONE |
| US-106 | AC-106-02 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentPosts.vue | DONE |
| US-106 | AC-106-03 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentPosts.vue | DONE |
| US-106 | AC-106-04 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentPosts.vue | DONE |
| US-107 | AC-107-01 | backend/apps/content/{richtext/render,posts,views_member}.py；frontend/src/portal/{InfoList,InfoDetail}.vue | DONE |
| US-107 | AC-107-02 | backend/apps/content/{richtext/render,posts,views_member}.py；frontend/src/portal/{InfoList,InfoDetail}.vue | DONE |
| US-107 | AC-107-03 | backend/apps/content/{richtext/render,posts,views_member}.py；frontend/src/portal/{InfoList,InfoDetail}.vue | DONE |
| US-107 | AC-107-04 | backend/apps/content/{richtext/render,posts,views_member}.py；frontend/src/portal/{InfoList,InfoDetail}.vue | DONE |
| US-108 | AC-108-01 | backend/apps/content/{richtext/render,posts,views_member}.py；miniprogram/pages/info/*、components/RichBlocks.vue | DONE |
| US-108 | AC-108-02 | backend/apps/content/{richtext/render,posts,views_member}.py；miniprogram/pages/info/*、components/RichBlocks.vue | DONE |
| US-108 | AC-108-03 | backend/apps/content/{richtext/render,posts,views_member}.py；miniprogram/pages/info/*、components/RichBlocks.vue | DONE |
| US-108 | AC-108-04 | backend/apps/content/{richtext/render,posts,views_member}.py；miniprogram/pages/info/*、components/RichBlocks.vue | DONE |
| US-109 | AC-109-01 | backend/apps/content/richtext/{schema,render}.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-109 | AC-109-02 | backend/apps/content/richtext/{schema,render}.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-109 | AC-109-03 | backend/apps/content/richtext/{schema,render}.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-109 | AC-109-04 | backend/apps/content/richtext/{schema,render}.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-110 | AC-110-01 | backend/apps/content/richtext/schema.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-110 | AC-110-02 | backend/apps/content/richtext/schema.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-110 | AC-110-03 | backend/apps/content/richtext/schema.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-110 | AC-110-04 | backend/apps/content/richtext/schema.py；frontend/src/admin/editor/{RichEditor,Toolbar}.vue | DONE |
| US-111 | AC-111-01 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-111 | AC-111-02 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-111 | AC-111-03 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-112 | AC-112-01 | backend/apps/content/{styles,posts,richtext/render}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-112 | AC-112-02 | backend/apps/content/{styles,posts,richtext/render}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-112 | AC-112-03 | backend/apps/content/{styles,posts,richtext/render}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-112 | AC-112-04 | backend/apps/content/{styles,posts,richtext/render}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-113 | AC-113-01 | backend/apps/content/richtext/{paginate,convert}.py；frontend/src/portal/InfoDetail.vue；miniprogram/pages/info/detail.vue | DONE |
| US-113 | AC-113-02 | backend/apps/content/richtext/{paginate,convert}.py；frontend/src/portal/InfoDetail.vue；miniprogram/pages/info/detail.vue | DONE |
| US-113 | AC-113-03 | backend/apps/content/richtext/{paginate,convert}.py；frontend/src/portal/InfoDetail.vue；miniprogram/pages/info/detail.vue | DONE |
| US-113 | AC-113-04 | backend/apps/content/richtext/{paginate,convert}.py；frontend/src/portal/InfoDetail.vue；miniprogram/pages/info/detail.vue | DONE |
| US-114 | AC-114-01 | backend/apps/content/{ai_jobs,services_config,prompts}.py、apps/integrations/llm.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-114 | AC-114-02 | backend/apps/content/{ai_jobs,services_config,prompts}.py、apps/integrations/llm.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-114 | AC-114-03 | backend/apps/content/{ai_jobs,services_config,prompts}.py、apps/integrations/llm.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-114 | AC-114-04 | backend/apps/content/{ai_jobs,services_config,prompts}.py、apps/integrations/llm.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-114 | AC-114-05 | backend/apps/content/{ai_jobs,services_config,prompts}.py、apps/integrations/llm.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-115 | AC-115-01 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-115 | AC-115-02 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-115 | AC-115-03 | backend/apps/content/{posts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-116 | AC-116-01 | backend/apps/content/ai_jobs.py、apps/integrations/imagegen.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-116 | AC-116-02 | backend/apps/content/ai_jobs.py、apps/integrations/imagegen.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-116 | AC-116-03 | backend/apps/content/ai_jobs.py、apps/integrations/imagegen.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-116 | AC-116-04 | backend/apps/content/ai_jobs.py、apps/integrations/imagegen.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-117 | AC-117-01 | backend/apps/content/{services_config,models,views_admin}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-117 | AC-117-02 | backend/apps/content/{services_config,models,views_admin}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-117 | AC-117-03 | backend/apps/content/{services_config,models,views_admin}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-117 | AC-117-04 | backend/apps/content/{services_config,models,views_admin}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-117 | AC-117-05 | backend/apps/content/{services_config,models,views_admin}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-118 | AC-118-01 | backend/apps/content/services_config.py、apps/integrations/llm.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-118 | AC-118-02 | backend/apps/content/services_config.py、apps/integrations/llm.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-118 | AC-118-03 | backend/apps/content/services_config.py、apps/integrations/llm.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-118 | AC-118-04 | backend/apps/content/services_config.py、apps/integrations/llm.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-119 | AC-119-01 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/{AdminMedia,editor/MediaPicker}.vue | DONE |
| US-119 | AC-119-02 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/{AdminMedia,editor/MediaPicker}.vue | DONE |
| US-119 | AC-119-03 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/{AdminMedia,editor/MediaPicker}.vue | DONE |
| US-119 | AC-119-04 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/{AdminMedia,editor/MediaPicker}.vue | DONE |
| US-120 | AC-120-01 | backend/apps/content/{ai_jobs,media}.py；frontend/src/admin/{AdminMedia,AdminContentEditor}.vue | DONE |
| US-120 | AC-120-02 | backend/apps/content/{ai_jobs,media}.py；frontend/src/admin/{AdminMedia,AdminContentEditor}.vue | DONE |
| US-120 | AC-120-03 | backend/apps/content/{ai_jobs,media}.py；frontend/src/admin/{AdminMedia,AdminContentEditor}.vue | DONE |
| US-121 | AC-121-01 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/MediaPicker.vue | DONE |
| US-121 | AC-121-02 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/MediaPicker.vue | DONE |
| US-121 | AC-121-03 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/MediaPicker.vue | DONE |
| US-122 | AC-122-01 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/AdminMedia.vue | DONE |
| US-122 | AC-122-02 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/AdminMedia.vue | DONE |
| US-122 | AC-122-03 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/AdminMedia.vue | DONE |
| US-122 | AC-122-04 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/AdminMedia.vue | DONE |
| US-122 | AC-122-05 | backend/apps/content/{media,views_admin}.py；frontend/src/admin/AdminMedia.vue | DONE |
| US-123 | AC-123-01 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-123 | AC-123-02 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-123 | AC-123-03 | backend/apps/content/{media,posts}.py；frontend/src/admin/editor/{RichEditor,MediaPicker}.vue | DONE |
| US-124 | AC-124-01 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-02 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-03 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-04 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-05 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-06 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-124 | AC-124-07 | backend/apps/content/{ai_jobs,jobs,handlers}.py、apps/integrations/videogen.py、management/commands/run_content_worker.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-125 | AC-125-01 | backend/apps/content/{services_config,vault}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-125 | AC-125-02 | backend/apps/content/{services_config,vault}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-125 | AC-125-03 | backend/apps/content/{services_config,vault}.py；frontend/src/admin/AdminAiServices.vue | DONE |
| US-126 | AC-126-01 | backend/apps/content/{platforms,views_admin}.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-126 | AC-126-02 | backend/apps/content/{platforms,views_admin}.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-126 | AC-126-03 | backend/apps/content/{platforms,views_admin}.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-126 | AC-126-04 | backend/apps/content/{platforms,views_admin}.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-127 | AC-127-01 | backend/apps/content/{platforms,vault,drafts}.py、apps/integrations/draft.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-127 | AC-127-02 | backend/apps/content/{platforms,vault,drafts}.py、apps/integrations/draft.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-127 | AC-127-03 | backend/apps/content/{platforms,vault,drafts}.py、apps/integrations/draft.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-127 | AC-127-04 | backend/apps/content/{platforms,vault,drafts}.py、apps/integrations/draft.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-127 | AC-127-05 | backend/apps/content/{platforms,vault,drafts}.py、apps/integrations/draft.py；frontend/src/admin/AdminPlatforms.vue | DONE |
| US-128 | AC-128-01 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-02 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-03 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-04 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-05 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-06 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-128 | AC-128-07 | backend/apps/content/{drafts,jobs,handlers}.py、apps/integrations/draft.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-129 | AC-129-01 | backend/apps/content/{drafts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-129 | AC-129-02 | backend/apps/content/{drafts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-129 | AC-129-03 | backend/apps/content/{drafts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-129 | AC-129-04 | backend/apps/content/{drafts,views_admin}.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-130 | AC-130-01 | backend/apps/content/export_pack.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-130 | AC-130-02 | backend/apps/content/export_pack.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-130 | AC-130-03 | backend/apps/content/export_pack.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-130 | AC-130-04 | backend/apps/content/export_pack.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-130 | AC-130-05 | backend/apps/content/export_pack.py；frontend/src/admin/AdminContentEditor.vue | DONE |
| US-131 | AC-131-01 | backend/apps/core/permissions.py（IsAdmin/IsMember）、backend/apps/content/{views_admin,views_member,urls}.py | DONE |
| US-131 | AC-131-02 | backend/apps/core/permissions.py（IsAdmin/IsMember）、backend/apps/content/{views_admin,views_member,urls}.py | DONE |
| US-131 | AC-131-03 | backend/apps/core/permissions.py（IsAdmin/IsMember）、backend/apps/content/{views_admin,views_member,urls}.py | DONE |
| US-131 | AC-131-04 | backend/apps/core/permissions.py（IsAdmin/IsMember）、backend/apps/content/{views_admin,views_member,urls}.py | DONE |

共 112 条 AC，均映射到实现位置；GROUP_D 负责逐条测试映射。

## 数据迁移

- `backend/apps/content/migrations/0001_initial.py` 手写，仅新建 9 张表；文件头无 "Generated by Django"。
- `makemigrations --check --dry-run --settings=config.test_settings` → `No changes detected`。
- 反向迁移为 DROP TABLE；数据风险与 mysqldump 要求见 module_design「数据迁移」，E1 部署计划须标注 `[MANUAL_ROLLBACK_REQUIRED]`。

## 自验证记录（2026-11-11）

| 命令 | 结果 |
|---|---|
| `python manage.py check --settings=config.test_settings` | System check identified no issues (0 silenced) |
| `python manage.py makemigrations --check --dry-run --settings=config.test_settings` | No changes detected |
| `python manage.py test --settings=config.test_settings` | Ran 327 tests / OK（含既有契约测试） |
| `npm run build -- --base=/ocap/`（frontend） | ✓ built in 9.74s（新增 Tiptap 依赖后 48 packages） |
| `npx vitest run`（frontend） | 124 passed / 2 failed（theme_build、theme.spec 既有环境失败） |
| `npx vitest run`（miniprogram） | 69 passed（页面数断言已更新为 13 页） |
| 临时 API 冒烟（test client + migrate run_syncdb） | 创建 201、预览 200、发布 200、会员详情 200（2 页）、非法链接 400 `CONTENT_INVALID_DOC`、服务/平台/参数 200 |

## 与设计的偏差与说明

1. 管理端页面为可用实现（列表/表单/对话框），未做像素级视觉打磨；编辑器依赖已按 tech_stack 安装 7 个 `@tiptap/*` 包（3.33.1）。
2. `blocks` 渲染的媒体 `src` 在会员接口中去除 `CONTENT_MEDIA_PATH_PREFIX` 前缀，由小程序拼接 API 基址（IFC-233 口径）。
3. 素材配额预检使用「已用 + 本次文件上限」保守估算；实际大小仍逐块校验。
4. 平台账户首次创建时先以临时 context 加密再以真实 id 重加密（保证 AAD 绑定 id）。
5. 小程序新增 2 页后，既有主题守护测试的页数断言由 11 更新为 13；前端路由数量断言同步更新。
