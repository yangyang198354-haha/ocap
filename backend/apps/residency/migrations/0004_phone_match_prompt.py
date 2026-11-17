# 手写迁移（画像 P6）：新增 PhoneMatchPrompt（手机号匹配清册的待确认状态，ADR-128）；可逆（DeleteModel）。
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residency", "0003_appeal_owner_name"),
        ("accounts", "0003_adminaccount_theme_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhoneMatchPrompt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(
                    choices=[("PENDING", "待确认"), ("DISMISSED", "已选不是"), ("DONE", "已确认"),
                             ("EXPIRED", "已失效")],
                    default="PENDING", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, related_name="phone_match_prompt",
                    to="accounts.user")),
            ],
        ),
    ]
