"""为收入表增加可空的软删除时间。"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("income", "0006_income_sheet_account")]

    operations = [
        migrations.AddField(
            model_name="incomesheet",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
