"""MOD-039（1.1.0，ADR-060）：公众号令牌缓存列（手写迁移，画像 P6；4 列均可空，可逆）。

数据步骤（Q-B2）：wechat_mp 账户若 secret_keys 不同时含 appid 与 appsecret（1.0.0 的 access_token 凭据），
auth_status 置 UNSET；只读 secret_keys，不解密。反向为 no-op。
"""
from django.db import migrations, models


def mark_legacy_wechat_accounts_unset(apps, schema_editor):
    PlatformAccount = apps.get_model("content", "PlatformAccount")
    for row in PlatformAccount.objects.filter(platform="wechat_mp"):
        keys = set(row.secret_keys or [])
        if not {"appid", "appsecret"} <= keys and row.auth_status != "UNSET":
            row.auth_status = "UNSET"
            row.save(update_fields=["auth_status"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="platformaccount",
            name="token_blob",
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="platformaccount",
            name="token_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="platformaccount",
            name="token_refreshed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="platformaccount",
            name="token_lock_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(mark_legacy_wechat_accounts_unset, migrations.RunPython.noop),
    ]
