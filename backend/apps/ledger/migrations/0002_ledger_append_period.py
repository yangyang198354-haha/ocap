# G-001/G-002/G-004：台账改为追加式入账、period_type/year/quarter 周期维度。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="LedgerEntry"),
        migrations.DeleteModel(name="LedgerReport"),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("direction", models.CharField(choices=[("INCOME", "收入"), ("EXPENSE", "支出")],
                                               max_length=8)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("occurred_on", models.DateField(db_index=True)),
                ("entry_type", models.CharField(max_length=32)),
                ("summary", models.CharField(blank=True, max_length=200, null=True)),
                ("source_type", models.CharField(max_length=32)),
                ("source_id", models.BigIntegerField()),
                ("seq", models.SmallIntegerField(default=0)),
                ("status", models.CharField(choices=[("ACTIVE", "有效"), ("VOIDED", "已作废")],
                                            default="ACTIVE", max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"indexes": [models.Index(fields=["occurred_on"], name="ledger_lede_occurre_c39b98_idx"),
                                  models.Index(fields=["status", "occurred_on"],
                                               name="ledger_lede_status_7d3a0b_idx")]},
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.UniqueConstraint(fields=("source_type", "source_id", "seq"),
                                                name="uniq_ledger_source_seq"),
        ),
        migrations.CreateModel(
            name="LedgerReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name="ID")),
                ("period_type", models.CharField(choices=[("QUARTER", "季度"), ("YEAR", "年度")],
                                                 max_length=8)),
                ("year", models.SmallIntegerField()),
                ("quarter", models.SmallIntegerField(blank=True, null=True)),
                ("total_income", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("total_expense", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("detail", models.JSONField(default=list)),
                ("stale", models.BooleanField(default=False)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("generated_by_type", models.CharField(choices=[("SYSTEM", "系统"), ("MEMBER", "业委会成员")],
                                                       default="MEMBER", max_length=8)),
                ("generated_by_id", models.IntegerField(blank=True, null=True)),
            ],
            options={"ordering": ["-year", "-period_type", "-quarter"]},
        ),
        migrations.AddConstraint(
            model_name="ledgerreport",
            constraint=models.UniqueConstraint(fields=("period_type", "year", "quarter"),
                                                name="uniq_ledger_period"),
        ),
    ]
