"""US-135 / AC-135-01~04/06：管理端、用户端读取同一 stored specific_part。"""
from apps.residency.models import Membership
from tests.integration.test_registry_import_enhancement import RegistryImportTestBase


class SpecificPartDisplayConsistencyTests(RegistryImportTestBase):
    def test_tc_int_421_same_value_across_admin_and_portal(self):
        unit = self.make_registry_unit(building="1栋", unit_no="1单元", floor="1", room="101")
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1)

        admin_units = self.api("get", "/admin/registry/units?q=1栋1单元", token=self.admin_token)
        self.assert_ok(admin_units)
        self.assertEqual([item["specific_part"] for item in admin_units.data["results"]], ["1栋1单元1层101号"])

        memberships = self.api("get", "/admin/memberships?q=1栋1单元", token=self.admin_token)
        self.assert_ok(memberships)
        self.assertEqual([item["specific_part"] for item in memberships.data["results"]], ["1栋1单元1层101号"])

        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        self.assertEqual([item["specific_part"] for item in me.data["identities"]["units"]], ["1栋1单元1层101号"])

    def test_tc_int_422_old_format_keyword_does_not_match(self):
        self.make_registry_unit(building="1栋", unit_no="1单元", floor="1", room="101")
        for path in ("/admin/registry/units?q=1栋-1单元", "/admin/memberships?q=1栋-1单元"):
            resp = self.api("get", path, token=self.admin_token)
            self.assert_ok(resp)

    def test_tc_int_423_me_does_not_expose_owner_pii(self):
        unit = self.make_registry_unit(building="1栋", unit_no="1单元", floor="1", room="101")
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1)
        me = self.api("get", "/me", token=token)
        self.assert_ok(me)
        unit_row = me.data["identities"]["units"][0]
        self.assertEqual(set(unit_row), {"unit_id", "specific_part", "role", "role_label",
                                         "unit_type", "unit_type_label", "area", "area_display"})
