"""账户实体与报表期初/期末/旧口径字段（MOD-197 / ADR-178~183）。手写 scoped 迁移。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0003_rename_ledger_lede_occurre_c39b98_idx_ledger_ledg_occurre_17517a_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="LedgerAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("name", models.CharField(max_length=64)),
                ("account_no", models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ("status", models.CharField(choices=[("ENABLED", "启用"), ("DISABLED", "停用")],
                                            default="ENABLED", max_length=8)),
                ("is_default", models.BooleanField(default=False)),
                ("created_by_admin_id", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-is_default", "id"],
                "indexes": [models.Index(fields=["status"], name="ledger_account_status_idx")],
            },
        ),
        migrations.AddField(
            model_name="ledgerentry",
            name="account",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT,
                                    related_name="entries", to="ledger.ledgeraccount"),
        ),
        migrations.AddIndex(
            model_name="ledgerentry",
            index=models.Index(fields=["account", "status", "occurred_on"],
                               name="ledger_entry_acct_status_idx"),
        ),
        migrations.AddField(
            model_name="ledgerreport",
            name="opening_balance",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="ledgerreport",
            name="closing_balance",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="ledgerreport",
            name="legacy",
            field=models.BooleanField(default=False),
        ),
    ]
