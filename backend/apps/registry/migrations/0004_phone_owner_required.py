"""MOD-030：手机号归属业主收紧为非空。

手写迁移（画像 P6）。执行前断言不存在 owner 为空的手机号，否则失败以便先回填。
"""
import django.db.models.deletion
from django.db import migrations, models


def assert_no_orphan_phones(apps, schema_editor):
    RegistryPhone = apps.get_model("registry", "RegistryPhone")
    orphan = RegistryPhone.objects.filter(owner__isnull=True).count()
    if orphan:
        raise RuntimeError(f"仍有 {orphan} 条手机号未归属业主，请先执行 0003 回填")


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0003_backfill_legacy_owners"),
    ]

    operations = [
        migrations.RunPython(assert_no_orphan_phones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="registryphone",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="phones",
                to="registry.registryowner",
            ),
        ),
    ]
