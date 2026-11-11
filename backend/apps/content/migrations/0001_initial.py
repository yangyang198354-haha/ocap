"""MOD-039：内容中心九张新表（手写迁移，画像 P6；仅新建表，可逆）。"""
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContentPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("title", models.CharField(blank=True, default="", max_length=200)),
                ("doc", models.JSONField(blank=True, default=dict)),
                ("style_key", models.CharField(default="builtin:classic", max_length=64)),
                ("status", models.CharField(choices=[("DRAFT", "草稿"), ("PUBLISHED", "已发布"), ("OFFLINE", "已下线")], default="DRAFT", max_length=10)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("text_confirmed_hash", models.CharField(blank=True, default="", max_length=64)),
                ("text_confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_by_label", models.CharField(blank=True, default="", max_length=64)),
                ("updated_by_admin_id", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-updated_at", "-id"]},
        ),
        migrations.CreateModel(
            name="PromptTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("prompt", models.TextField()),
                ("params", models.JSONField(blank=True, default=dict)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ServiceConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("service_type", models.CharField(choices=[("LLM_DEEPSEEK", "DeepSeek"), ("LLM_VOLCANO", "火山方舟"), ("IMAGE_ARK", "火山方舟图像生成"), ("VIDEO_JIMENG", "即梦视频生成")], max_length=16, unique=True)),
                ("params", models.JSONField(blank=True, default=dict)),
                ("secret_blob", models.BinaryField(blank=True, null=True)),
                ("secret_keys", models.JSONField(blank=True, default=list)),
                ("is_default", models.BooleanField(default=False)),
                ("last_test_ok", models.BooleanField(blank=True, null=True)),
                ("last_tested_at", models.DateTimeField(blank=True, null=True)),
                ("last_test_error", models.CharField(blank=True, default="", max_length=32)),
                ("updated_by_admin_id", models.IntegerField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="StyleTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("tokens", models.JSONField(default=dict)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="PlatformAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("platform", models.CharField(choices=[("wechat_mp", "微信公众号"), ("xiaohongshu", "小红书"), ("toutiao", "今日头条")], max_length=16, unique=True)),
                ("display_name", models.CharField(max_length=64)),
                ("secret_blob", models.BinaryField(blank=True, null=True)),
                ("secret_keys", models.JSONField(blank=True, default=list)),
                ("auth_status", models.CharField(choices=[("UNSET", "未设置"), ("NORMAL", "正常"), ("EXPIRED", "失效")], default="UNSET", max_length=8)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ContentJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("LLM_TEXT", "文案生成"), ("IMAGE_GEN", "配图生成"), ("VIDEO_GEN", "视频生成"), ("DRAFT_PUSH", "保存草稿")], max_length=16)),
                ("status", models.CharField(choices=[("QUEUED", "排队"), ("RUNNING", "执行中"), ("WAITING_REMOTE", "等待远端"), ("SUCCEEDED", "成功"), ("FAILED", "失败")], default="QUEUED", max_length=16)),
                ("payload", models.JSONField(default=dict)),
                ("state", models.JSONField(blank=True, default=dict)),
                ("result", models.JSONField(blank=True, null=True)),
                ("error_code", models.CharField(blank=True, default="", max_length=32)),
                ("error_message", models.CharField(blank=True, default="", max_length=500)),
                ("attempts", models.SmallIntegerField(default=0)),
                ("max_attempts", models.SmallIntegerField(default=2)),
                ("lease_token", models.CharField(blank=True, default="", max_length=32)),
                ("lease_until", models.DateTimeField(blank=True, null=True)),
                ("next_run_at", models.DateTimeField()),
                ("subject_type", models.CharField(blank=True, default="", max_length=24)),
                ("subject_id", models.CharField(blank=True, default="", max_length=64)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_by_label", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="MediaItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("media_type", models.CharField(choices=[("IMAGE", "图片"), ("VIDEO", "视频")], max_length=8)),
                ("source", models.CharField(choices=[("UPLOAD", "上传"), ("AI_GENERATED", "AI 生成")], max_length=16)),
                ("state", models.CharField(choices=[("SAVED", "已保存"), ("CANDIDATE", "候选")], default="SAVED", max_length=12)),
                ("title", models.CharField(blank=True, default="", max_length=255)),
                ("original_name", models.CharField(blank=True, default="", max_length=255)),
                ("content_type", models.CharField(blank=True, default="", max_length=100)),
                ("size", models.BigIntegerField(default=0)),
                ("sha256", models.CharField(blank=True, default="", max_length=64)),
                ("storage_path", models.CharField(max_length=255)),
                ("ai_job", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="content.contentjob")),
                ("created_by_admin_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="ContentPostMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("media", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="post_links", to="content.mediaitem")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media_links", to="content.contentpost")),
            ],
        ),
        migrations.CreateModel(
            name="DraftPush",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("platform", models.CharField(max_length=16)),
                ("batch_id", models.UUIDField(default=uuid.uuid4)),
                ("mode", models.CharField(choices=[("AUTO", "自动"), ("MANUAL", "人工")], max_length=6)),
                ("status", models.CharField(choices=[("PENDING", "待发送"), ("SENDING", "发送中"), ("SAVED", "已保存"), ("FAILED", "失败"), ("UNKNOWN", "结果未知"), ("MANUAL_REQUIRED", "需人工粘贴")], default="PENDING", max_length=16)),
                ("error_code", models.CharField(blank=True, default="", max_length=32)),
                ("error_message", models.CharField(blank=True, default="", max_length=500)),
                ("remote_ref", models.CharField(blank=True, default="", max_length=128)),
                ("unsupported", models.JSONField(blank=True, default=list)),
                ("created_by_admin_id", models.IntegerField()),
                ("created_by_label", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="content.platformaccount")),
                ("job", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="content.contentjob")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="draft_pushes", to="content.contentpost")),
                ("retry_of", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="content.draftpush")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="contentpostmedia",
            constraint=models.UniqueConstraint(fields=("post", "media"), name="uniq_content_post_media"),
        ),
        migrations.AddIndex(
            model_name="contentpost",
            index=models.Index(fields=["status", "published_at"], name="content_con_status_5c3f6e_idx"),
        ),
        migrations.AddIndex(
            model_name="mediaitem",
            index=models.Index(fields=["state", "media_type", "source", "created_at"], name="content_med_state_e3a0b1_idx"),
        ),
        migrations.AddIndex(
            model_name="contentjob",
            index=models.Index(fields=["status", "next_run_at"], name="content_con_status_9a1c2d_idx"),
        ),
        migrations.AddIndex(
            model_name="contentjob",
            index=models.Index(fields=["kind", "created_at"], name="content_con_kind_4b7e8f_idx"),
        ),
        migrations.AddIndex(
            model_name="draftpush",
            index=models.Index(fields=["post", "created_at"], name="content_dra_post_id_2d6f7a_idx"),
        ),
        migrations.AddIndex(
            model_name="draftpush",
            index=models.Index(fields=["batch_id"], name="content_dra_batch_i_8c4b9e_idx"),
        ),
    ]
