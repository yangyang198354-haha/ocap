"""TC-E2E-501~503：身份与认证房屋端到端旅程（US-145/146/148）。"""
from decimal import Decimal

from apps.registry.models import RegistryUnit
from tests.support import ApiTestBase, next_phone


class IdentityDisplayJourneyTests(ApiTestBase):
    def make_display_unit(self, *, phone=None, unit_type="RESIDENCE", area="89.50"):
        unit = RegistryUnit.objects.create(
            building="1栋", unit_no="1单元", floor="9", room="902",
            unit_type=unit_type, area=Decimal(area) if area is not None else None,
        )
        if phone:
            from apps.registry.models import RegistryOwner, RegistryPhone
            owner = RegistryOwner.objects.create(unit=unit, name="杨扬")
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def test_tc_e2e_501_register_then_see_owner_and_unit_detail(self):
        """US-145 AC-145-02；US-146 AC-146-01；US-148 AC-148-01/02。"""
        phone = next_phone()
        unit = self.make_display_unit(phone=phone)
        code = self.request_code(phone, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(reg, 201)
        token = reg.data["token"]
        identities = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(identities["labels"], ["产权业主"])
        self.assertEqual(identities["units"], [{
            "unit_id": unit.id,
            "specific_part": "1栋1单元9层902号",
            "role": "HEAD",
            "role_label": "产权业主",
            "unit_type": "RESIDENCE",
            "unit_type_label": "住宅",
            "area": "89.50",
            "area_display": "89.50 ㎡",
        }])

    def test_tc_e2e_502_resident_apply_approve_then_see_resident(self):
        """US-145 AC-145-04；US-146 AC-146-08。"""
        owner_phone = next_phone()
        unit = self.make_display_unit(phone=owner_phone, unit_type="APARTMENT", area=None)
        _, owner_token = self.make_user(phone=owner_phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id},
                                token=owner_token), 201)
        resident, resident_token = self.make_user()
        application = self.api("post", "/resident-applications", {"unit_id": unit.id},
                               token=resident_token)
        self.assert_ok(application, 201)
        decision = self.api("post", f"/resident-applications/{application.data['id']}/decision",
                            {"decision": "APPROVE"}, token=owner_token)
        self.assert_ok(decision)
        identities = self.api("get", "/me", token=resident_token).data["identities"]
        self.assertEqual(identities["labels"], ["同住人"])
        self.assertEqual(identities["units"][0]["role_label"], "同住人")
        self.assertEqual(identities["units"][0]["unit_type_label"], "公寓")
        self.assertEqual(identities["units"][0]["area_display"], "未登记")

    def test_tc_e2e_503_committee_position_wins_over_owner(self):
        """US-145 AC-145-07。"""
        phone = next_phone()
        unit = self.make_display_unit(phone=phone)
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=token), 201)
        self.make_seat(user, "VICE_CHAIR")
        identities = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(identities["labels"], ["副主任"])
        self.assertEqual(identities["units"][0]["role_label"], "产权业主")
