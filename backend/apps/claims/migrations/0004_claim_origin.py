"""报销/备用金增加 origin 自关联：失败后新建申请时留痕（REQ-FUNC-273）。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("claims", "0003_rename_claims_clai_status_a1b2c3_idx_claims_clai_status_2fd679_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="claim",
            name="origin",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT,
                                    related_name="reissued", to="claims.claim"),
        ),
    ]
