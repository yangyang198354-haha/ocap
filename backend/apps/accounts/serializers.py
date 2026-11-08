from rest_framework import serializers

from apps.core.masking import MaskedPhoneField

from .models import AdminAccount, User


class AdminAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAccount
        fields = ["id", "username", "is_active", "created_at"]


class AdminUserSerializer(serializers.ModelSerializer):
    phone = MaskedPhoneField()

    class Meta:
        model = User
        fields = ["id", "account_no", "phone", "nickname", "status"]
