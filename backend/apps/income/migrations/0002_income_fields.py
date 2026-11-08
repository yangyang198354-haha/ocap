# G-008/G-009：收入表补齐 source/creator_labels/void 字段、状态命名 EFFECTIVE/VOID；明细重命名 occurred_on、加 line_no/source_note/remark。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("income", "0001_initial"),
    ]

    operations = [
        # IncomeSheet 字段补齐
        migrations.AddField(model_name="incomesheet", name="source",
                            field=models.CharField(choices=[("MANUAL", "手工"), ("IMPORT", "导入")],
                                                   default="MANUAL", max_length=8)),
        migrations.AddField(model_name="incomesheet", name="creator_labels",
                            field=models.CharField(blank=True, default="", max_length=128)),
        migrations.AddField(model_name="incomesheet", name="effective_at",
                            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="incomesheet", name="void_reason",
                            field=models.CharField(blank=True, default="", max_length=200)),
        migrations.AddField(model_name="incomesheet", name="voided_by_id",
                            field=models.IntegerField(blank=True, null=True)),
        migrations.AddField(model_name="incomesheet", name="voided_at",
                            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="incomesheet", name="updated_at",
                            field=models.DateTimeField(auto_now=True)),
        migrations.AlterField(model_name="incomesheet", name="status",
                              field=models.CharField(choices=[("DRAFT", "草稿"), ("PENDING", "审批中"),
                                                               ("EFFECTIVE", "已生效"), ("REJECTED", "未通过"),
                                                               ("WITHDRAWN", "已撤回"), ("VOID", "已作废")],
                                                      default="DRAFT", max_length=12)),
        migrations.AddIndex(model_name="incomesheet",
                             index=models.Index(fields=["status", "period_start", "period_end"],
                                                name="income_inco_status__idx")),
        # IncomeRecord 字段对齐
        migrations.RenameField(model_name="incomerecord", old_name="income_date",
                               new_name="occurred_on"),
        migrations.RemoveField(model_name="incomerecord", name="item"),
        migrations.RemoveField(model_name="incomerecord", name="voucher_id"),
        migrations.AddField(model_name="incomerecord", name="line_no",
                            field=models.SmallIntegerField(default=1)),
        migrations.AddField(model_name="incomerecord", name="source_note",
                            field=models.CharField(blank=True, default="", max_length=200)),
        migrations.AddField(model_name="incomerecord", name="remark",
                            field=models.CharField(blank=True, default="", max_length=200)),
        migrations.AddConstraint(model_name="incomerecord",
                                 constraint=models.UniqueConstraint(fields=("sheet", "line_no"),
                                                                     name="uniq_income_record_line")),
    ]
