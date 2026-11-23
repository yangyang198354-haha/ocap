"""收入表增加账户归属（MOD-197 / REQ-FUNC-339）。"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("income", "0005_identity_labels_full"),
        ("ledger", "0004_ledger_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="incomesheet",
            name="account",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name="income_sheets", to="ledger.ledgeraccount"),
        ),
    ]
