"""决议增加 origin 自关联：失败后新建决议时留痕（REQ-FUNC-273）。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resolutions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="resolution",
            name="origin",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT,
                                    related_name="reissued", to="resolutions.resolution"),
        ),
    ]
