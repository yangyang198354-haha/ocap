# 手写迁移（画像 P6）：Appeal / ResidentApplication 的 status choices 追加 CLOSED，仅元数据变更，无 SQL。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residency", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appeal",
            name="status",
            field=models.CharField(
                choices=[("PENDING", "待审"), ("APPROVED", "通过"), ("REJECTED", "拒绝"), ("CLOSED", "已关闭")],
                default="PENDING", max_length=8),
        ),
        migrations.AlterField(
            model_name="residentapplication",
            name="status",
            field=models.CharField(
                choices=[("PENDING", "待审"), ("APPROVED", "通过"), ("REJECTED", "拒绝"), ("CLOSED", "已关闭")],
                default="PENDING", max_length=8),
        ),
    ]
