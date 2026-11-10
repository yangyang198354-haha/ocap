"""业主清册（MOD-004 / MOD-030）。

MOD-030 增补：专有部分类型与面积、业主实体（RegistryOwner）、手机号归属业主。
"""
from django.db import models

UNIT_TYPE_CHOICES = [
    ("RESIDENCE", "住宅"),
    ("APARTMENT", "公寓"),
    ("SHOP", "商铺"),
    ("PARKING", "车位"),
    ("OTHER", "其他"),
]


def build_specific_part(building: str, unit_no: str, floor: str, room: str) -> str:
    """只拼非空段，以 "-" 连接；四级都非空时与旧规则结果相同（AC-098-05）。"""
    return "-".join(part for part in (building, unit_no, floor, room) if part)


class RegistryUnit(models.Model):
    building = models.CharField(max_length=32)
    unit_no = models.CharField(max_length=32, blank=True, default="")
    floor = models.CharField(max_length=32, blank=True, default="")
    room = models.CharField(max_length=32)
    specific_part = models.CharField(max_length=140, unique=True)
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPE_CHOICES, null=True, blank=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["building", "unit_no", "floor", "room"], name="uniq_registry_unit")
        ]
        ordering = ["building", "unit_no", "floor", "room"]

    def save(self, *args, **kwargs):
        self.specific_part = build_specific_part(self.building, self.unit_no, self.floor, self.room)
        super().save(*args, **kwargs)


class RegistryOwner(models.Model):
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="owners")
    # NULL 仅用于迁移回填的既有记录（ADR-037）；新增/导入/单条编辑一律非空。
    name = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["unit", "name"], name="uniq_registry_owner_name")
        ]
        ordering = ["id"]


class RegistryPhone(models.Model):
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="phones")
    owner = models.ForeignKey(RegistryOwner, on_delete=models.CASCADE, related_name="phones")
    phone = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["unit", "phone"], name="uniq_registry_phone")]
        indexes = [models.Index(fields=["phone"])]
