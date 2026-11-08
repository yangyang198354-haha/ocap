import uuid

from django.db import models


class AuditLog(models.Model):
    ACTOR_TYPES = [("MEMBER", "成员"), ("ADMIN", "管理员"), ("SYSTEM", "系统")]
    RESULTS = [("SUCCESS", "成功"), ("FAILURE", "失败"), ("DENIED", "拒绝")]

    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor_type = models.CharField(max_length=8, choices=ACTOR_TYPES)
    actor_id = models.IntegerField(null=True, blank=True)
    actor_label = models.CharField(max_length=64, blank=True, default="")
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=48)
    object_id = models.CharField(max_length=64)
    result = models.CharField(max_length=8, choices=RESULTS)
    detail = models.JSONField(default=dict, blank=True)
    ip = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["action", "occurred_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]
        ordering = ["-occurred_at", "-id"]


class Attachment(models.Model):
    OWNER_TYPES = [("MEMBER", "成员"), ("ADMIN", "管理员")]
    STATUSES = [("TEMP", "临时"), ("LINKED", "已关联")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_type = models.CharField(max_length=8, choices=OWNER_TYPES)
    owner_id = models.IntegerField()
    purpose = models.CharField(max_length=32)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    sha256 = models.CharField(max_length=64)
    storage_path = models.CharField(max_length=255)
    status = models.CharField(max_length=8, choices=STATUSES, default="TEMP")
    linked_type = models.CharField(max_length=48, null=True, blank=True)
    linked_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SystemConfig(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_admin_id = models.IntegerField(null=True, blank=True)


class RateLimit(models.Model):
    key = models.CharField(max_length=128)
    window_start = models.DateTimeField()
    count = models.IntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["key", "window_start"], name="uniq_rate_window")]


class Lockout(models.Model):
    key = models.CharField(max_length=128, primary_key=True)
    fail_count = models.SmallIntegerField(default=0)
    window_start = models.DateTimeField()
    locked_until = models.DateTimeField(null=True, blank=True)


class JobRun(models.Model):
    job_name = models.CharField(max_length=64, primary_key=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=16, blank=True, default="")
    last_error = models.TextField(blank=True, default="")
