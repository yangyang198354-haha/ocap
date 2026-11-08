"""ledger 索引改名，使索引名与模型 Meta.indexes 自动命名一致（手写，CR-023；迁移名与已上线版本相同）。"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0002_ledger_append_period"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="ledgerentry",
            new_name="ledger_ledg_occurre_17517a_idx",
            old_name="ledger_lede_occurre_c39b98_idx",
        ),
        migrations.RenameIndex(
            model_name="ledgerentry",
            new_name="ledger_ledg_status_c22492_idx",
            old_name="ledger_lede_status_7d3a0b_idx",
        ),
    ]
