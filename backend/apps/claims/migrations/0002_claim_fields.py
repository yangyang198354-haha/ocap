# G-003/G-010：报销字段补齐（applicant_labels、occurred_on、expected_usage、expected_settle_on、advance_id、settlement_id、settle_slot、ledger_posted、approval_instance_id、updated_at）。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("claims", "0001_initial"),
    ]

    operations = [
        migrations.AddField(model_name="claim", name="applicant_labels",
                            field=models.CharField(blank=True, default="", max_length=128)),
        migrations.AddField(model_name="claim", name="occurred_on",
                            field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="expected_usage",
                            field=models.CharField(blank=True, default="", max_length=200)),
        migrations.AddField(model_name="claim", name="expected_settle_on",
                            field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="advance_id",
                            field=models.BigIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="settlement_id",
                            field=models.BigIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="settle_slot",
                            field=models.IntegerField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="ledger_posted",
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="claim", name="approval_instance_id",
                            field=models.BigIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="claim", name="updated_at",
                            field=models.DateTimeField(auto_now=True)),
        migrations.AddIndex(model_name="claim",
                             index=models.Index(fields=["status", "type"], name="claims_clai_status_a1b2c3_idx")),
        migrations.AddIndex(model_name="claim",
                             index=models.Index(fields=["submitter", "status"],
                                                name="claims_clai_submitt_d4e5f6_idx")),
    ]
