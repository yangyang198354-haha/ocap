"""报销/备用金/结算单增加账户归属（MOD-197 / REQ-FUNC-339）。"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("claims", "0004_claim_origin"),
        ("ledger", "0004_ledger_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="claim",
            name="account",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="claims", to="ledger.ledgeraccount"),
        ),
    ]
