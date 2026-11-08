"""报销、借款与结算（MOD-010 / IFC-100~104）。"""
from django.core.validators import MinValueValidator
from django.db import models


class Claim(models.Model):
    TYPES = [("REIMBURSEMENT", "报销"), ("ADVANCE", "借款"), ("SETTLEMENT", "结算")]
    STATUSES = [("PENDING", "审批中"), ("APPROVED", "通过"), ("REJECTED", "拒绝"),
                ("WITHDRAWN", "已撤回")]

    type = models.CharField(max_length=16, choices=TYPES)
    submitter = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="claims")
    applicant_labels = models.CharField(max_length=128, blank=True, default="")
    amount = models.DecimalField(max_digits=14, decimal_places=2,
                                 validators=[MinValueValidator(0.01)])
    reason = models.CharField(max_length=500)
    occurred_on = models.DateField(null=True, blank=True)
    expected_usage = models.CharField(max_length=200, blank=True, default="")
    expected_settle_on = models.DateField(null=True, blank=True)
    advance_id = models.BigIntegerField(null=True, blank=True)
    settlement_id = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    revision = models.IntegerField(default=1)
    settle_slot = models.IntegerField(null=True, blank=True)
    ledger_posted = models.BooleanField(default=False)
    approval_instance_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "type"]),
            models.Index(fields=["submitter", "status"]),
        ]
