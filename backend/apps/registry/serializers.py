"""清册序列化器（MOD-030 / IFC-153、IFC-156）。"""
from rest_framework import serializers

from .models import RegistryUnit


class RegistryOwnerSerializer(serializers.Serializer):
    """管理员视图：含姓名与完整手机号（REQ-FUNC-095、US-019 AC-019-06）。"""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True, allow_null=True)
    phones = serializers.SerializerMethodField()

    def get_phones(self, obj):
        return [p.phone for p in obj.phones.all()]


class RegistryUnitAdminSerializer(serializers.ModelSerializer):
    unit_type_label = serializers.SerializerMethodField()
    owners = RegistryOwnerSerializer(many=True, read_only=True)

    def get_unit_type_label(self, obj):
        return obj.get_unit_type_display() if obj.unit_type else None

    class Meta:
        model = RegistryUnit
        fields = [
            "id", "specific_part", "building", "unit_no", "floor", "room",
            "unit_type", "unit_type_label", "area", "owners",
        ]
