"""收入表增加 origin 自关联：失败后新建收入表时留痕（REQ-FUNC-273）。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("income", "0003_alter_incomerecord_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="incomesheet",
            name="origin",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT,
                                    related_name="reissued", to="income.incomesheet"),
        ),
    ]
