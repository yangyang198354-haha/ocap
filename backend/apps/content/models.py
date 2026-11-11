"""MOD-039：内容中心数据模型（IFC-165）。"""
import uuid

from django.db import models


class ContentPost(models.Model):
    STATUSES = [("DRAFT", "草稿"), ("PUBLISHED", "已发布"), ("OFFLINE", "已下线")]

    title = models.CharField(max_length=200, blank=True, default="")
    doc = models.JSONField(default=dict, blank=True)
    style_key = models.CharField(max_length=64, default="builtin:classic")
    status = models.CharField(max_length=10, choices=STATUSES, default="DRAFT")
    published_at = models.DateTimeField(null=True, blank=True)
    text_confirmed_hash = models.CharField(max_length=64, blank=True, default="")
    text_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_by_admin_id = models.IntegerField()
    created_by_label = models.CharField(max_length=64, blank=True, default="")
    updated_by_admin_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["status", "published_at"])]
        ordering = ["-updated_at", "-id"]


class MediaItem(models.Model):
    MEDIA_TYPES = [("IMAGE", "图片"), ("VIDEO", "视频")]
    SOURCES = [("UPLOAD", "上传"), ("AI_GENERATED", "AI 生成")]
    STATES = [("SAVED", "已保存"), ("CANDIDATE", "候选")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_type = models.CharField(max_length=8, choices=MEDIA_TYPES)
    source = models.CharField(max_length=16, choices=SOURCES)
    state = models.CharField(max_length=12, choices=STATES, default="SAVED")
    title = models.CharField(max_length=255, blank=True, default="")
    original_name = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=100, blank=True, default="")
    size = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, default="")
    storage_path = models.CharField(max_length=255)
    ai_job = models.ForeignKey("content.ContentJob", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="+")
    created_by_admin_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["state", "media_type", "source", "created_at"])]
        ordering = ["-created_at", "-id"]


class ContentPostMedia(models.Model):
    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name="media_links")
    media = models.ForeignKey(MediaItem, on_delete=models.CASCADE, related_name="post_links")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["post", "media"], name="uniq_content_post_media")]


class StyleTemplate(models.Model):
    name = models.CharField(max_length=64, unique=True)
    tokens = models.JSONField(default=dict)
    created_by_admin_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PromptTemplate(models.Model):
    name = models.CharField(max_length=64, unique=True)
    prompt = models.TextField()
    params = models.JSONField(default=dict, blank=True)
    created_by_admin_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ServiceConfig(models.Model):
    SERVICE_TYPES = [
        ("LLM_DEEPSEEK", "DeepSeek"), ("LLM_VOLCANO", "火山方舟"),
        ("IMAGE_ARK", "火山方舟图像生成"), ("VIDEO_JIMENG", "即梦视频生成"),
    ]

    service_type = models.CharField(max_length=16, choices=SERVICE_TYPES, unique=True)
    params = models.JSONField(default=dict, blank=True)
    secret_blob = models.BinaryField(null=True, blank=True)
    secret_keys = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)
    last_test_ok = models.BooleanField(null=True, blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_error = models.CharField(max_length=32, blank=True, default="")
    updated_by_admin_id = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class PlatformAccount(models.Model):
    PLATFORMS = [("wechat_mp", "微信公众号"), ("xiaohongshu", "小红书"), ("toutiao", "今日头条")]
    AUTH_STATUSES = [("UNSET", "未设置"), ("NORMAL", "正常"), ("EXPIRED", "失效")]

    platform = models.CharField(max_length=16, choices=PLATFORMS, unique=True)
    display_name = models.CharField(max_length=64)
    secret_blob = models.BinaryField(null=True, blank=True)
    secret_keys = models.JSONField(default=list, blank=True)
    auth_status = models.CharField(max_length=8, choices=AUTH_STATUSES, default="UNSET")
    created_by_admin_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # 1.1.0（ADR-060，0002）：公众号访问令牌缓存，仅 wechat_mp 使用；任何序列化器不得输出
    token_blob = models.BinaryField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    token_refreshed_at = models.DateTimeField(null=True, blank=True)
    token_lock_until = models.DateTimeField(null=True, blank=True)


class ContentJob(models.Model):
    KINDS = [("LLM_TEXT", "文案生成"), ("IMAGE_GEN", "配图生成"),
             ("VIDEO_GEN", "视频生成"), ("DRAFT_PUSH", "保存草稿")]
    STATUSES = [("QUEUED", "排队"), ("RUNNING", "执行中"), ("WAITING_REMOTE", "等待远端"),
                ("SUCCEEDED", "成功"), ("FAILED", "失败")]

    kind = models.CharField(max_length=16, choices=KINDS)
    status = models.CharField(max_length=16, choices=STATUSES, default="QUEUED")
    payload = models.JSONField(default=dict)
    state = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=32, blank=True, default="")
    error_message = models.CharField(max_length=500, blank=True, default="")
    attempts = models.SmallIntegerField(default=0)
    max_attempts = models.SmallIntegerField(default=2)
    lease_token = models.CharField(max_length=32, blank=True, default="")
    lease_until = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField()
    subject_type = models.CharField(max_length=24, blank=True, default="")
    subject_id = models.CharField(max_length=64, blank=True, default="")
    created_by_admin_id = models.IntegerField()
    created_by_label = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "next_run_at"]),
                   models.Index(fields=["kind", "created_at"])]
        ordering = ["-created_at", "-id"]


class DraftPush(models.Model):
    MODES = [("AUTO", "自动"), ("MANUAL", "人工")]
    STATUSES = [("PENDING", "待发送"), ("SENDING", "发送中"), ("SAVED", "已保存"),
                ("FAILED", "失败"), ("UNKNOWN", "结果未知"), ("MANUAL_REQUIRED", "需人工粘贴")]

    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name="draft_pushes")
    account = models.ForeignKey(PlatformAccount, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="+")
    platform = models.CharField(max_length=16)
    batch_id = models.UUIDField(default=uuid.uuid4)
    mode = models.CharField(max_length=6, choices=MODES)
    status = models.CharField(max_length=16, choices=STATUSES, default="PENDING")
    error_code = models.CharField(max_length=32, blank=True, default="")
    error_message = models.CharField(max_length=500, blank=True, default="")
    remote_ref = models.CharField(max_length=128, blank=True, default="")
    unsupported = models.JSONField(default=list, blank=True)
    retry_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    job = models.ForeignKey(ContentJob, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_by_admin_id = models.IntegerField()
    created_by_label = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["post", "created_at"]), models.Index(fields=["batch_id"])]
        ordering = ["-created_at", "-id"]
