from rest_framework import serializers

from apps.core.masking import MaskedPhoneField

from .directory import certified_units, identity_view, real_names
from .models import AdminAccount, User


class AdminAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAccount
        fields = ["id", "username", "is_active", "created_at"]


class AdminUserSerializer(serializers.ModelSerializer):
    phone = MaskedPhoneField()

    class Meta:
        model = User
        fields = ["id", "account_no", "phone", "nickname", "status", "last_login_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        memberships = list(instance.memberships.all())
        seats = list(instance.seats.all())
        identity = identity_view(memberships=memberships, seats=seats)
        data["identity_code"] = identity["identity_code"]
        data["identity_label"] = identity["identity_label"]
        data["certified_units"] = certified_units(memberships=memberships)
        data["real_names"] = real_names(user=instance, memberships=memberships)
        return data
