# MOD-023：手写迁移，为 accounts_user 增加可空列 theme_key（界面风格偏好）。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="theme_key",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
