"""income 排序选项、索引名与 line_no 字段选项对齐模型（手写，CR-023；迁移名与已上线版本相同）。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("income", "0002_income_fields"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="incomerecord",
            options={"ordering": ["line_no", "id"]},
        ),
        migrations.RenameIndex(
            model_name="incomesheet",
            new_name="income_inco_status_405779_idx",
            old_name="income_inco_status__idx",
        ),
        migrations.AlterField(
            model_name="incomerecord",
            name="line_no",
            field=models.SmallIntegerField(),
        ),
    ]
