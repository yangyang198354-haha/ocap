from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_user_profile_fields")]

    operations = [
        migrations.AlterField(
            model_name="authtoken",
            name="session_kind",
            field=models.CharField(
                choices=[("IDLE", "闲置"), ("EXTENDED", "延长"), ("REMEMBER", "记住我")],
                default="IDLE",
                max_length=8,
            ),
        ),
    ]
