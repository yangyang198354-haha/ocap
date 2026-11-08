from rest_framework import serializers

from apps.core.masking import PlainPhoneField

from .models import RegistryPhone, RegistryUnit


class PlainPhoneListField(serializers.ListField):
    child = PlainPhoneField()


class RegistryUnitAdminSerializer(serializers.ModelSerializer):
    phones = serializers.SerializerMethodField()

    def get_phones(self, obj):
        return [p.phone for p in obj.phones.all()]

    class Meta:
        model = RegistryUnit
        fields = ["id", "specific_part", "building", "unit_no", "floor", "room", "phones"]


_ = RegistryPhone
