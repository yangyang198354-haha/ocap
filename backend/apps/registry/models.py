"""业主清册（MOD-004）。"""
from django.db import models


class RegistryUnit(models.Model):
    building = models.CharField(max_length=32)
    unit_no = models.CharField(max_length=32)
    floor = models.CharField(max_length=16)
    room = models.CharField(max_length=16)
    specific_part = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["building", "unit_no", "floor", "room"], name="uniq_registry_unit")
        ]
        ordering = ["building", "unit_no", "floor", "room"]

    def save(self, *args, **kwargs):
        self.specific_part = f"{self.building}-{self.unit_no}-{self.floor}-{self.room}"
        super().save(*args, **kwargs)


class RegistryPhone(models.Model):
    unit = models.ForeignKey(RegistryUnit, on_delete=models.CASCADE, related_name="phones")
    phone = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["unit", "phone"], name="uniq_registry_phone")]
        indexes = [models.Index(fields=["phone"])]
