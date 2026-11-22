# 手写迁移（画像 P6）：MOD-168/MOD-169 / ADR-160~165。
# 申诉与同住申请：新增“已撤回”状态、处理备注、撤回时间、重新提交关联；同住申请新增本人实名与驳回原因。
# 新增字段全部可空或有默认值，不回填存量；反向迁移把 status 改回 8 字符时，
# 若已存在 WITHDRAWN（9 字符）记录需先清理或改写 [MANUAL_ROLLBACK_REQUIRED]。
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("residency", "0005_membership_registry_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appeal",
            name="status",
            field=models.CharField(choices=[("PENDING", "待审"), ("APPROVED", "通过"),
                                            ("REJECTED", "拒绝"), ("CLOSED", "已关闭"),
                                            ("WITHDRAWN", "已撤回")],
                                   default="PENDING", max_length=12),
        ),
        migrations.AddField(
            model_name="appeal",
            name="decision_note",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="appeal",
            name="withdrawn_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="appeal",
            name="previous_appeal",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="resubmitted_appeals", to="residency.appeal"),
        ),
        migrations.AlterField(
            model_name="residentapplication",
            name="status",
            field=models.CharField(choices=[("PENDING", "待审"), ("APPROVED", "通过"),
                                            ("REJECTED", "拒绝"), ("CLOSED", "已关闭"),
                                            ("WITHDRAWN", "已撤回")],
                                   default="PENDING", max_length=12),
        ),
        migrations.AddField(
            model_name="residentapplication",
            name="applicant_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="residentapplication",
            name="reject_reason",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="residentapplication",
            name="decision_note",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="residentapplication",
            name="withdrawn_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="residentapplication",
            name="previous_application",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="resubmitted_applications",
                                    to="residency.residentapplication"),
        ),
    ]
