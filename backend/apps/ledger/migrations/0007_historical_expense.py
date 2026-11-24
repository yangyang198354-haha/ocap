"""历史支出批量导入（MOD-192/193，手写迁移；因台账账户迁移占用 0004，本迁移编号为 0007）。"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("ledger", "0006_ledger_entry_account_not_null"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalExpenseBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("IMPORTED", "已导入"), ("VOIDED", "已作废")],
                                            default="IMPORTED", max_length=10)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("imported_rows", models.PositiveIntegerField(default=0)),
                ("skipped_rows", models.PositiveIntegerField(default=0)),
                ("failed_rows", models.PositiveIntegerField(default=0)),
                ("total_amount", models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("voided_at", models.DateTimeField(blank=True, null=True)),
                ("void_reason", models.CharField(blank=True, default="", max_length=200)),
                ("imported_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                                  related_name="historical_expense_batches",
                                                  to="accounts.user")),
                ("voided_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                related_name="+", to="accounts.user")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="historicalexpensebatch",
            index=models.Index(fields=["status", "created_at"], name="ledger_hist_status_created_idx"),
        ),
        migrations.CreateModel(
            name="HistoricalExpenseRow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_no", models.PositiveSmallIntegerField()),
                ("occurred_on", models.DateField(blank=True, null=True)),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("category", models.CharField(blank=True, default="", max_length=32)),
                ("purpose", models.CharField(blank=True, default="", max_length=200)),
                ("remark", models.CharField(blank=True, default="", max_length=200)),
                ("status", models.CharField(choices=[("IMPORTED", "成功"), ("DUPLICATE", "重复"), ("ERROR", "错误")],
                                            default="ERROR", max_length=10)),
                ("error_message", models.CharField(blank=True, default="", max_length=200)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                            related_name="rows", to="ledger.historicalexpensebatch")),
                ("ledger_entry", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                      related_name="historical_expense_row",
                                                      to="ledger.ledgerentry")),
            ],
            options={"ordering": ["line_no", "id"]},
        ),
        migrations.AddConstraint(
            model_name="historicalexpenserow",
            constraint=models.UniqueConstraint(fields=("batch", "line_no"), name="uniq_hist_expense_line"),
        ),
        migrations.AddIndex(
            model_name="historicalexpenserow",
            index=models.Index(fields=["batch", "status"], name="ledger_hist_batch_status_idx"),
        ),
    ]
