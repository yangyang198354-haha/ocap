"""MOD-030：为既有手机号回填一位姓名为 NULL 的业主（ADR-037）。

手写迁移（画像 P6）。不删除任何既有行；逻辑放在可被测试直接导入调用的函数里
（测试环境 MIGRATION_MODULES 置空，不会自动跑迁移）。
"""
from django.db import migrations


def backfill_legacy_owners(apps, schema_editor):
    RegistryOwner = apps.get_model("registry", "RegistryOwner")
    RegistryPhone = apps.get_model("registry", "RegistryPhone")

    for phone in RegistryPhone.objects.filter(owner__isnull=True).iterator(chunk_size=1000):
        owner = RegistryOwner.objects.create(unit_id=phone.unit_id)
        RegistryPhone.objects.filter(pk=phone.pk).update(owner_id=owner.pk)


def remove_backfilled_owners(apps, schema_editor):
    RegistryOwner = apps.get_model("registry", "RegistryOwner")
    RegistryPhone = apps.get_model("registry", "RegistryPhone")

    legacy_ids = list(RegistryOwner.objects.filter(name__isnull=True).values_list("id", flat=True))
    if not legacy_ids:
        return
    RegistryPhone.objects.filter(owner_id__in=legacy_ids).update(owner_id=None)
    RegistryOwner.objects.filter(id__in=legacy_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0002_owner_type_area"),
    ]

    operations = [
        migrations.RunPython(backfill_legacy_owners, remove_backfilled_owners),
    ]
