# 手写迁移（画像 P6）：Appeal 新增 owner_name（申诉的产权人名字，缺省空串=未提供）；可逆（RemoveField）。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residency", "0002_closed_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="appeal",
            name="owner_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
