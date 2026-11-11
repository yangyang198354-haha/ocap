# MOD-068：手写迁移，为 accounts_adminaccount 增加可空列 theme_key（管理端风格偏好）。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_theme_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="adminaccount",
            name="theme_key",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
