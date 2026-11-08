"""claims 索引改名，使索引名与模型 Meta.indexes 自动命名一致（手写，CR-023；迁移名与已上线版本相同）。"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("claims", "0002_claim_fields"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="claim",
            new_name="claims_clai_status_2fd679_idx",
            old_name="claims_clai_status_a1b2c3_idx",
        ),
        migrations.RenameIndex(
            model_name="claim",
            new_name="claims_clai_submitt_0cdf15_idx",
            old_name="claims_clai_submitt_d4e5f6_idx",
        ),
    ]
