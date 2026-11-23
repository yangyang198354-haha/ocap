from rest_framework import serializers

from .directory import certified_units, identity_view, real_names
from .models import AdminAccount, User


class AdminAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAccount
        fields = ["id", "username", "is_active", "created_at"]


class AdminUserSerializer(serializers.ModelSerializer):
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
        data["avatar_url"] = instance.avatar_url
        # 审批等场景展示实名（无实名时回退账号），不回退昵称（昵称可重复）
        data["display_name"] = (data["real_names"][0] if data["real_names"]
                                else f"用户{instance.account_no}")
        return data
