"""业委会席位与配置（MOD-006）。"""
from django.db import models


class CommitteeConfig(models.Model):
    cap_chair = models.IntegerField(null=True, blank=True)
    cap_vice = models.IntegerField(null=True, blank=True)
    cap_member = models.IntegerField(null=True, blank=True)
    cap_rep = models.IntegerField(null=True, blank=True)
    term_months_chair = models.IntegerField(null=True, blank=True)
    term_months_vice = models.IntegerField(null=True, blank=True)
    term_months_member = models.IntegerField(null=True, blank=True)
    term_months_rep = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_admin_id = models.IntegerField(null=True, blank=True)

    @classmethod
    def load(cls) -> "CommitteeConfig":
        config, _ = cls.objects.get_or_create(
            id=1, defaults={"cap_chair": 1, "cap_vice": 2, "cap_member": 6},
        )
        return config


class Seat(models.Model):
    POSITIONS = [("CHAIR", "主任"), ("VICE_CHAIR", "副主任"), ("MEMBER", "委员"),
                 ("REPRESENTATIVE", "业主代表")]
    STATUSES = [("ACTIVE", "在任"), ("REVOKED", "撤销"), ("EXPIRED", "到期"),
                ("INVALIDATED", "资格失效"), ("REPLACED", "变更"), ("MERGED", "合并")]

    # MOD-140 / IFC-347：user 为空 = 待绑定（持有人为清册业主 holder_owner，尚未注册并认证）
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="seats",
                             null=True, blank=True)
    holder_owner = models.ForeignKey("registry.RegistryOwner", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="seats")
    holder_unit_text = models.CharField(max_length=140, blank=True, default="")  # 授予时 specific_part 快照
    holder_name = models.CharField(max_length=64, blank=True, default="")  # 授予时清册业主姓名（已归一）
    bound_at = models.DateTimeField(null=True, blank=True)
    bind_conflict_at = models.DateTimeField(null=True, blank=True)
    position = models.CharField(max_length=16, choices=POSITIONS)
    term_start = models.DateField()
    term_end = models.DateField()
    status = models.CharField(max_length=12, choices=STATUSES, default="ACTIVE")
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=48, null=True, blank=True)
    granted_by_admin_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active_slot = models.SmallIntegerField(null=True, blank=True, default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "active_slot"], name="uniq_seat_active_per_user"),
            models.UniqueConstraint(fields=["holder_owner", "active_slot"], name="uniq_seat_active_per_owner"),
        ]
