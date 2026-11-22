"""房屋关系（MOD-005）。"""
from django.db import models

from apps.registry.models import RegistryUnit


class Membership(models.Model):
    ROLES = [("HEAD", "户主"), ("OWNER", "产权业主"), ("RESIDENT", "同住人")]
    SOURCES = [("REGISTRY", "清册认证"), ("APPEAL", "申诉"), ("APPLICATION", "同住人申请")]
    END_REASONS = [("REVOKED", "撤销"), ("CANCELLED", "注销"), ("REMOVED", "移除"),
                   ("LEFT", "退出"), ("MERGED", "合并"), ("UPGRADED", "升级")]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="memberships")
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=8, choices=ROLES)
    source = models.CharField(max_length=12, choices=SOURCES)
    certified_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=12, choices=END_REASONS, null=True, blank=True)
    active_slot = models.SmallIntegerField(null=True, blank=True, default=1)
    head_slot = models.SmallIntegerField(null=True, blank=True)
    # MOD-141 / IFC-347b：认证时通过核对的清册业主；不参与任何唯一约束
    registry_owner = models.ForeignKey("registry.RegistryOwner", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="verified_memberships")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "unit", "active_slot"], name="uniq_membership_active"),
            models.UniqueConstraint(fields=["unit", "head_slot"], name="uniq_unit_head"),
        ]
        ordering = ["certified_at", "id"]


class Appeal(models.Model):
    STATUSES = [("PENDING", "待审"), ("APPROVED", "通过"), ("REJECTED", "拒绝"),
                ("CLOSED", "已关闭"), ("WITHDRAWN", "已撤回")]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="appeals")
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="appeals")
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by_admin_id = models.IntegerField(null=True, blank=True)
    reject_reason = models.CharField(max_length=500, null=True, blank=True)
    # IFC-384：管理员处理备注（通过与驳回均可填，选填）
    decision_note = models.CharField(max_length=500, null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    # IFC-382：撤回后重新提交的来源记录（D-02）
    previous_appeal = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name="resubmitted_appeals")
    pending_slot = models.SmallIntegerField(null=True, blank=True, default=1)
    owner_name = models.CharField(max_length=64, blank=True, default="")  # ADR-111：申诉的产权人名字，空串=未提供

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "unit", "pending_slot"], name="uniq_appeal_pending")]


class ResidentApplication(models.Model):
    STATUSES = [("PENDING", "待审"), ("APPROVED", "通过"), ("REJECTED", "拒绝"),
                ("CLOSED", "已关闭"), ("WITHDRAWN", "已撤回")]

    applicant = models.ForeignKey("accounts.User", on_delete=models.CASCADE,
                                  related_name="resident_applications")
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="resident_applications")
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    decided_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="decided_resident_applications")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # IFC-385：提交时的本人实名快照（C-361：不参与认证/清册匹配）
    applicant_name = models.CharField(max_length=64, blank=True, default="")
    # IFC-388：产权业主处理备注与驳回原因（均选填）
    reject_reason = models.CharField(max_length=500, null=True, blank=True)
    decision_note = models.CharField(max_length=500, null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    # IFC-385：撤回后重新提交的来源记录（D-02）
    previous_application = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                             related_name="resubmitted_applications")
    pending_slot = models.SmallIntegerField(null=True, blank=True, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["applicant", "unit", "pending_slot"],
                                    name="uniq_resident_application_pending")
        ]


class PhoneMatchPrompt(models.Model):
    """MOD-132 / ADR-128：手机号匹配清册后的"待确认"状态；不存手机号、清册信息或单元快照。"""
    STATUSES = [("PENDING", "待确认"), ("DISMISSED", "已选不是"), ("DONE", "已确认"), ("EXPIRED", "已失效")]

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="phone_match_prompt")
    status = models.CharField(max_length=12, choices=STATUSES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
