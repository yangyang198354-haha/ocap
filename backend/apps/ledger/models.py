"""台账（MOD-012 / IFC-110~114；MOD-192~194 账户与报表链式口径）。"""
from django.db import models


class LedgerAccount(models.Model):
    """资金账户（MOD-192 / REQ-FUNC-336）。停用不删除，账户号空值存 NULL（ADR-183）。"""
    STATUSES = [("ENABLED", "启用"), ("DISABLED", "停用")]

    name = models.CharField(max_length=64)
    account_no = models.CharField(max_length=32, null=True, blank=True, unique=True)
    status = models.CharField(max_length=8, choices=STATUSES, default="ENABLED")
    is_default = models.BooleanField(default=False)
    created_by_admin_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "id"]
        indexes = [models.Index(fields=["status"], name="ledger_account_status_idx")]

    def __str__(self) -> str:
        return self.name


class LedgerEntry(models.Model):
    DIRECTIONS = [("INCOME", "收入"), ("EXPENSE", "支出")]
    STATUSES = [("ACTIVE", "有效"), ("VOIDED", "已作废")]

    account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="entries")
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
            models.Index(fields=["account", "status", "occurred_on"],
                         name="ledger_entry_acct_status_idx"),
        ]

    def save(self, *args, **kwargs):
        # 未显式指定账户的写入（存量脚本/直接 create）归入默认账户，保证非空列可写。
        if self.account_id is None:
            from .services import AccountService

            self.account = AccountService.default_account()
        super().save(*args, **kwargs)


class LedgerReport(models.Model):
    PERIOD_TYPES = [("QUARTER", "季度"), ("YEAR", "年度")]
    GEN_TYPES = [("SYSTEM", "系统"), ("MEMBER", "业委会成员")]

    period_type = models.CharField(max_length=8, choices=PERIOD_TYPES)
    year = models.SmallIntegerField()
    quarter = models.SmallIntegerField(null=True, blank=True)
    total_income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    closing_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    legacy = models.BooleanField(default=False)
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


class HistoricalExpenseBatch(models.Model):
    """历史支出导入批次（MOD-192）：只用于上线前历史数据补录。"""
    STATUSES = [("IMPORTED", "已导入"), ("VOIDED", "已作废")]

    file_name = models.CharField(max_length=255)
    imported_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT,
                                    related_name="historical_expense_batches")
    status = models.CharField(max_length=10, choices=STATUSES, default="IMPORTED")
    total_rows = models.PositiveIntegerField(default=0)
    imported_rows = models.PositiveIntegerField(default=0)
    skipped_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    voided_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+")
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["status", "created_at"], name="ledger_hist_status_created_idx")]


class HistoricalExpenseRow(models.Model):
    """历史支出导入行（MOD-193）：保留原始行与处理结果，成功行关联台账。"""
    STATUSES = [("IMPORTED", "成功"), ("DUPLICATE", "重复"), ("ERROR", "错误")]

    batch = models.ForeignKey(HistoricalExpenseBatch, on_delete=models.CASCADE, related_name="rows")
    line_no = models.PositiveSmallIntegerField()
    occurred_on = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=32, blank=True, default="")
    purpose = models.CharField(max_length=200, blank=True, default="")
    remark = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUSES, default="ERROR")
    error_message = models.CharField(max_length=200, blank=True, default="")
    ledger_entry = models.OneToOneField(LedgerEntry, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name="historical_expense_row")

    class Meta:
        ordering = ["line_no", "id"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "line_no"], name="uniq_hist_expense_line"),
        ]
        indexes = [models.Index(fields=["batch", "status"], name="ledger_hist_batch_status_idx")]
