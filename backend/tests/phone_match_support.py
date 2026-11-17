"""ocap_identity_property 测试支撑：清册匹配引导（IFC-332~336）的合成数据与辅助调用。

清册业主姓名、手机号全部为合成值（C-73）；手机号经 tests.support.next_phone 生成。
"""
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership, PhoneMatchPrompt
from tests.support import ApiTestBase, next_phone

OWNER_NAME = "测试清册业主甲"  # 合成姓名，用于断言响应不泄露


class PhoneMatchBase(ApiTestBase):
    def reg_unit(self, phones=(), *, building="1栋", unit_no="1单元", floor="3", room="301",
                 unit_type="RESIDENCE", area=None, name=OWNER_NAME):
        unit = RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor, room=room,
                                           unit_type=unit_type, area=area)
        if phones:
            owner = RegistryOwner.objects.create(unit=unit, name=name)
            for phone in phones:
                RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def add_phone(self, unit, phone, name="测试清册业主乙"):
        owner = RegistryOwner.objects.filter(unit=unit).first() or RegistryOwner.objects.create(unit=unit, name=name)
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)

    def register_raw(self, phone):
        code = self.request_code(phone, "REGISTER")
        return self.api("post", "/auth/register", {"phone": phone, "code": code})

    def matches(self, token):
        return self.api("get", "/me/registry-matches", token=token)

    def confirm(self, token, unit_ids):
        return self.api("post", "/me/registry-matches/confirm", {"unit_ids": unit_ids}, token=token)

    def dismiss(self, token):
        return self.api("post", "/me/registry-matches/dismiss", {}, token=token)

    def prompt_status(self, user_or_id):
        uid = getattr(user_or_id, "id", user_or_id)
        row = PhoneMatchPrompt.objects.filter(user_id=uid).first()
        return row.status if row else None

    def active_units(self, user_id):
        return set(Membership.objects.filter(user_id=user_id, ended_at__isnull=True)
                   .values_list("unit_id", flat=True))
