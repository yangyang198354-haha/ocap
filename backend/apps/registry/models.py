"""业主清册（MOD-004 / MOD-030）。

MOD-030 增补：专有部分类型与面积、业主实体（RegistryOwner）、手机号归属业主。
MOD-064：专有部分标识改为“楼栋单元楼层户号”直接连接并按段补后缀（ADR-064）。
"""
import re

from django.db import models

UNIT_TYPE_CHOICES = [
    ("RESIDENCE", "住宅"),
    ("APARTMENT", "公寓"),
    ("SHOP", "商铺"),
    ("PARKING", "车位"),
    ("OTHER", "其他"),
]

# 各段后缀：楼栋、单元、楼层、户号（IFC-243）
_SUFFIXES: tuple[str, str, str, str] = ("栋", "单元", "层", "号")
_PURE_NUMBER = re.compile(r"(?:负)?[0-9]+")


def _segment(value: str, suffix: str) -> str:
    """按 ADR-064 规则处理单段：空段跳过、已带后缀原样、纯数字补后缀、其他原样。"""
    text = (value or "").strip()
    if not text:
        return ""
    if text.endswith(suffix):
        return text
    if _PURE_NUMBER.fullmatch(text):
        return text + suffix
    return text


def _floor_is_implied_by_room(floor: str, room: str) -> bool:
    """规则（5）：户号以“楼层值+层”开头时，楼层段不再单独输出。"""
    floor_text = (floor or "").strip()
    room_text = (room or "").strip()
    if not floor_text or not room_text:
        return False
    stem = floor_text[:-1] if floor_text.endswith("层") else floor_text
    if not stem:
        return False
    return room_text.startswith(stem + "层")


def build_specific_part(building: str, unit_no: str, floor: str, room: str) -> str:
    """按楼栋、单元、楼层、户号的顺序直接连接并补后缀（REQ-FUNC-123/124）。"""
    floor_text = (floor or "").strip()
    room_text = (room or "").strip()
    parts = [
        _segment(building, _SUFFIXES[0]),
        _segment(unit_no, _SUFFIXES[1]),
        "" if _floor_is_implied_by_room(floor_text, room_text) else _segment(floor_text, _SUFFIXES[2]),
        _segment(room_text, _SUFFIXES[3]),
    ]
    return "".join(part for part in parts if part)


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
