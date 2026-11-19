# MOD-153：手写迁移，为 accounts_user 增加签名档与实名展示开关（PHASE_04 数据迁移）。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_adminaccount_theme_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="signature",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="user",
            name="real_name_visible",
            field=models.BooleanField(default=False),
        ),
    ]
