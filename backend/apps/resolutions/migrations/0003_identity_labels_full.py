"""REQ-FUNC-277 / D-05：历史决议发起人身份快照改为业务全称（只改身份文案，重复执行无变化）。"""
from django.db import migrations

SHORT_TO_FULL = {"主任": "业委会主任", "副主任": "业委会副主任", "委员": "业委会委员"}


def forwards(apps, schema_editor):
    Resolution = apps.get_model("resolutions", "Resolution")
    for row in Resolution.objects.exclude(initiator_labels=[]).iterator():
        labels = row.initiator_labels
        if not isinstance(labels, list):
            continue
        new_labels = [SHORT_TO_FULL.get(label, label) for label in labels]
        if new_labels != labels:
            row.initiator_labels = new_labels
            row.save(update_fields=["initiator_labels"])


class Migration(migrations.Migration):
    dependencies = [("resolutions", "0002_resolution_origin")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
