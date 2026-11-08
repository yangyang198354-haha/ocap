"""收入记账（MOD-011 / IFC-100~106）。"""
from django.db import models


class IncomeSheet(models.Model):
    STATUSES = [("DRAFT", "草稿"), ("PENDING", "审批中"), ("EFFECTIVE", "已生效"),
                ("REJECTED", "未通过"), ("WITHDRAWN", "已撤回"), ("VOID", "已作废")]
    SOURCES = [("MANUAL", "手工"), ("IMPORT", "导入")]

    title = models.CharField(max_length=100, null=True, blank=True)
    source = models.CharField(max_length=8, choices=SOURCES, default="MANUAL")
    creator_labels = models.CharField(max_length=128, blank=True, default="")
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    submitted_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT,
                                     related_name="income_sheets")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUSES, default="DRAFT")
    revision = models.IntegerField(default=1)
    approval_instance_id = models.BigIntegerField(null=True, blank=True)
    effective_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.CharField(max_length=200, blank=True, default="")
    voided_by_id = models.IntegerField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    pending_slot = models.SmallIntegerField(null=True, blank=True, default=1)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "period_start", "period_end"]),
        ]


class IncomeRecord(models.Model):
    sheet = models.ForeignKey(IncomeSheet, on_delete=models.CASCADE, related_name="records")
    line_no = models.SmallIntegerField()
    occurred_on = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=32, blank=True, default="")
    source_note = models.CharField(max_length=200, blank=True, default="")
    remark = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["line_no", "id"]
        constraints = [
            models.UniqueConstraint(fields=["sheet", "line_no"], name="uniq_income_record_line"),
        ]
