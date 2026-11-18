# 手写迁移（画像 P6）：MOD-141 / ADR-138。Membership 新增 registry_owner（认证时通过核对的清册业主，可空）；
# 不回填存量；可逆（RemoveField）。
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residency", "0004_phone_match_prompt"),
        ("registry", "0005_regenerate_specific_part"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="registry_owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="verified_memberships", to="registry.registryowner"),
        ),
    ]
