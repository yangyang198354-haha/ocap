"""业委会决议（MOD-009）。"""
from django.db import models


class Resolution(models.Model):
    STATUSES = [("PENDING", "审批中"), ("APPROVED", "通过"), ("REJECTED", "未通过"), ("WITHDRAWN", "已撤回")]
    MODES = [("DESIGNATED", "指定负责人"), ("HALF_MAJORITY", "半数同意")]

    title = models.CharField(max_length=200)
    content = models.TextField()
    initiator = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="resolutions")
    initiator_labels = models.JSONField(default=list)
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    approval_mode = models.CharField(max_length=16, choices=MODES, default="DESIGNATED")
    vote_deadline = models.DateTimeField(null=True, blank=True)
    revision = models.IntegerField(default=1)
    decided_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class Vote(models.Model):
    CHOICES = [("AGREE", "同意"), ("DISAGREE", "反对"), ("ABSTAIN", "弃权")]

    resolution = models.ForeignKey(Resolution, on_delete=models.CASCADE, related_name="votes")
    revision = models.IntegerField(default=1)
    voter = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="resolution_votes")
    choice = models.CharField(max_length=8, choices=CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["resolution", "revision", "voter"], name="uniq_resolution_vote")
        ]
