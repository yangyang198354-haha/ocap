"""台账（MOD-012 / IFC-110~114）。"""
from django.db import models


class LedgerEntry(models.Model):
    DIRECTIONS = [("INCOME", "收入"), ("EXPENSE", "支出")]
    STATUSES = [("ACTIVE", "有效"), ("VOIDED", "已作废")]

    direction = models.CharField(max_length=8, choices=DIRECTIONS)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    occurred_on = models.DateField(db_index=True)
    entry_type = models.CharField(max_length=32)
    summary = models.CharField(max_length=200, null=True, blank=True)
    source_type = models.CharField(max_length=32)
    source_id = models.BigIntegerField()
    seq = models.SmallIntegerField(default=0)
    status = models.CharField(max_length=8, choices=STATUSES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    voided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source_type", "source_id", "seq"],
                                    name="uniq_ledger_source_seq"),
        ]
        indexes = [
            models.Index(fields=["occurred_on"]),
            models.Index(fields=["status", "occurred_on"]),
        ]


class LedgerReport(models.Model):
    PERIOD_TYPES = [("QUARTER", "季度"), ("YEAR", "年度")]
    GEN_TYPES = [("SYSTEM", "系统"), ("MEMBER", "业委会成员")]

    period_type = models.CharField(max_length=8, choices=PERIOD_TYPES)
    year = models.SmallIntegerField()
    quarter = models.SmallIntegerField(null=True, blank=True)
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    detail = models.JSONField(default=list)
    stale = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by_type = models.CharField(max_length=8, choices=GEN_TYPES, default="MEMBER")
    generated_by_id = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["period_type", "year", "quarter"],
                                    name="uniq_ledger_period"),
        ]
        ordering = ["-year", "-period_type", "-quarter"]
