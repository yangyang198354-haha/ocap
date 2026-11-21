"""REQ-FUNC-277 / D-05：历史收入表创建人身份快照改为业务全称（只改身份文案，重复执行无变化）。"""
from django.db import migrations

SHORT_TO_FULL = {"主任": "业委会主任", "副主任": "业委会副主任", "委员": "业委会委员"}


def forwards(apps, schema_editor):
    IncomeSheet = apps.get_model("income", "IncomeSheet")
    for row in IncomeSheet.objects.exclude(creator_labels="").iterator():
        parts = [part.strip() for part in row.creator_labels.split(",")]
        new_labels = ",".join(SHORT_TO_FULL.get(part, part) for part in parts)
        if new_labels != row.creator_labels:
            row.creator_labels = new_labels
            row.save(update_fields=["creator_labels"])


class Migration(migrations.Migration):
    dependencies = [("income", "0004_incomesheet_origin")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
