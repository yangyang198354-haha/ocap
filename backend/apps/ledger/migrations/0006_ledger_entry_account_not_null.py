"""流水账户列改为非空（MOD-197 / ADR-181）。需 0005 回填完成，部署前做数据库快照。"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0005_ledger_account_backfill"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ledgerentry",
            name="account",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name="entries", to="ledger.ledgeraccount"),
        ),
    ]
