"""历史支出导入接入审批（MOD-207，手写迁移）：新增账户/审批字段与状态机取值。"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0007_historical_expense"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalexpensebatch",
            name="account",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="historical_expense_batches", to="ledger.ledgeraccount"),
        ),
        migrations.AddField(
            model_name="historicalexpensebatch",
            name="approval_instance_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalexpensebatch",
            name="decided_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalexpensebatch",
            name="status",
            field=models.CharField(choices=[("PENDING", "审批中"), ("IMPORTED", "已入账"), ("REJECTED", "已驳回"),
                                            ("WITHDRAWN", "已撤回"), ("VOIDED", "已作废")],
                                   default="PENDING", max_length=10),
        ),
        migrations.AlterField(
            model_name="historicalexpenserow",
            name="status",
            field=models.CharField(choices=[("PENDING", "待入账"), ("IMPORTED", "成功"),
                                            ("DUPLICATE", "重复"), ("ERROR", "错误")],
                                   default="ERROR", max_length=10),
        ),
    ]
