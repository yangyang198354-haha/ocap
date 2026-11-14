"""TC-INT-501~507：/me 身份口径与认证房屋明细（US-145~147 / REQ-FUNC-136~140）。"""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.registry.models import RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class IdentityDisplayTests(ApiTestBase):
    def make_display_unit(self, *, building="1栋", unit_no="1单元", floor="9", room="902",
                          unit_type="RESIDENCE", area="89.50"):
        return RegistryUnit.objects.create(
            building=building, unit_no=unit_no, floor=floor, room=room,
            unit_type=unit_type, area=Decimal(area) if area is not None else None,
        )

    def test_tc_int_501_guest_has_guest_label_and_empty_units(self):
        """US-145 AC-145-01；US-146 AC-146-06。"""
        _, token = self.make_user()
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        identities = me.data["identities"]
        self.assertEqual(identities["labels"], ["游客"])
        self.assertTrue(identities["is_guest"])
        self.assertEqual(identities["units"], [])

    def test_tc_int_502_registry_owner_shows_owner_and_unit_detail(self):
        """US-145 AC-145-02；US-146 AC-146-01/04/05；REQ-NFUNC-025。"""
        unit = self.make_display_unit()
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        identities = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(identities["labels"], ["产权业主"])
        self.assertFalse(identities["is_guest"])
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

    def test_tc_int_503_appeal_owner_shows_owner(self):
        """US-145 AC-145-03。"""
        unit = self.make_display_unit()
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="OWNER", source="APPEAL", active_slot=1)
        identities = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(identities["labels"], ["产权业主"])
        self.assertEqual(identities["units"][0]["role_label"], "产权业主")

    def test_tc_int_504_resident_shows_resident_and_owner_wins(self):
        """US-145 AC-145-04/05；US-146 AC-146-08。"""
        unit_a = self.make_display_unit(building="1栋", unit_no="1单元", floor="9", room="902")
        unit_b = self.make_display_unit(building="2栋", unit_no="1单元", floor="3", room="301",
                                        unit_type="APARTMENT", area=None)
        resident, resident_token = self.make_user()
        Membership.objects.create(user=resident, unit=unit_b, role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        labels = self.api("get", "/me", token=resident_token).data["identities"]["labels"]
        self.assertEqual(labels, ["同住人"])
        owner, owner_token = self.make_user()
        Membership.objects.create(user=owner, unit=unit_a, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        Membership.objects.create(user=owner, unit=unit_b, role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        identities = self.api("get", "/me", token=owner_token).data["identities"]
        self.assertEqual(identities["labels"], ["产权业主"])
        self.assertEqual([row["role_label"] for row in identities["units"]],
                         ["产权业主", "同住人"])

    def test_tc_int_505_committee_position_wins_and_expired_falls_back(self):
        """US-145 AC-145-07/08/09。"""
        unit = self.make_display_unit()
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        self.make_seat(user, "CHAIR")
        self.assertEqual(self.api("get", "/me", token=token).data["identities"]["labels"], ["主任"])

        user2, token2 = self.make_user()
        unit2 = self.make_display_unit(building="3栋", unit_no="", floor="", room="D001",
                                       unit_type="PARKING", area="12.00")
        Membership.objects.create(user=user2, unit=unit2, role="OWNER", source="REGISTRY",
                                  active_slot=1)
        self.make_seat(user2, "REPRESENTATIVE")
        self.assertEqual(self.api("get", "/me", token=token2).data["identities"]["labels"],
                         ["业主代表"])
        parking = self.api("get", "/me", token=token2).data["identities"]["units"][0]
        self.assertEqual(parking["unit_type_label"], "车位")
        self.assertEqual(parking["area_display"], "12.00 ㎡")
        self.assertNotIn("None", parking["specific_part"])

        user3, token3 = self.make_user()
        unit3 = self.make_display_unit(building="4栋", unit_no="1单元", floor="2", room="201")
        Membership.objects.create(user=user3, unit=unit3, role="OWNER", source="REGISTRY",
                                  active_slot=1)
        today = timezone.localdate()
        self.make_seat(user3, "MEMBER").__class__.objects.filter(user=user3).update(
            term_end=today - timedelta(days=1))
        self.assertEqual(self.api("get", "/me", token=token3).data["identities"]["labels"],
                         ["产权业主"])

    def test_tc_int_506_units_sorted_and_missing_display_values(self):
        """US-146 AC-146-02/03/04/05/09。"""
        unit_b = self.make_display_unit(building="2栋", unit_no="1单元", floor="1", room="101",
                                        unit_type=None, area=None)
        unit_a = self.make_display_unit(building="1栋", unit_no="1单元", floor="1", room="101",
                                        unit_type="SHOP", area="45.6")
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit_b, role="OWNER", source="REGISTRY",
                                  active_slot=1)
        Membership.objects.create(user=user, unit=unit_a, role="OWNER", source="REGISTRY",
                                  active_slot=1)
        Membership.objects.create(user=user, unit=unit_a, role="RESIDENT", source="APPLICATION",
                                  active_slot=2)
        units = self.api("get", "/me", token=token).data["identities"]["units"]
        self.assertEqual([row["unit_id"] for row in units], [unit_a.id, unit_b.id])
        self.assertEqual(units[0]["role_label"], "产权业主")
        self.assertEqual(units[0]["unit_type_label"], "商铺")
        self.assertEqual(units[0]["area_display"], "45.60 ㎡")
        self.assertEqual(units[1]["unit_type_label"], "未登记")
        self.assertEqual(units[1]["area_display"], "未登记")
        self.assertIsNone(units[1]["area"])

    def test_tc_int_507_ended_membership_is_excluded(self):
        """US-147 AC-147-03；REQ-NFUNC-026。"""
        unit = self.make_display_unit()
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY",
                                  active_slot=None, head_slot=None,
                                  ended_at=timezone.now(), end_reason="REVOKED")
        identities = self.api("get", "/me", token=token).data["identities"]
        self.assertEqual(identities["labels"], ["游客"])
        self.assertEqual(identities["units"], [])
        self.assertTrue(identities["is_guest"])
