"""PHASE_08 集成测试：已认证房屋列表排序（MOD-106，IFC-289/290）。

关联 US-192（AC-192-01~04）。认证时间与自然顺序故意相反。
"""
from datetime import timedelta

from django.utils import timezone

from apps.registry.models import RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase


def mk(building, unit_no, floor, room, unit_type="RESIDENCE"):
    return RegistryUnit.objects.create(building=building, unit_no=unit_no, floor=floor, room=room,
                                       unit_type=unit_type, area="50.00")


class MyUnitsOrderTests(ApiTestBase):
    def certify(self, user, unit, role="OWNER", days_ago=0, slot=1, source="REGISTRY"):
        m = Membership.objects.create(user=user, unit=unit, role=role, source=source, active_slot=slot,
                                      head_slot=1 if role == "HEAD" else None)
        Membership.objects.filter(pk=m.pk).update(certified_at=timezone.now() - timedelta(days=days_ago))
        return m

    def orders(self, token):
        me = [u["unit_id"] for u in self.api("get", "/me", token=token).data["identities"]["units"]]
        housing = [u["unit_id"] for u in self.api("get", "/me/housing", token=token).data["units"]]
        return me, housing

    def setUp(self):
        super().setUp()
        self.u2 = mk("2栋", "1单元", "1", "101")
        self.u10 = mk("10栋", "1单元", "1", "101")
        self.park = mk("地下车位", "", "负一", "5", unit_type="PARKING")

    def test_tc_int_564_me_and_housing_same_natural_order(self):
        """AC-192-01：认证时间顺序 地下车位(最早)→10栋→2栋(最晚)，两处都是 2栋、10栋、地下车位车位。"""
        user, token = self.make_user()
        self.certify(user, self.park, days_ago=30)
        self.certify(user, self.u10, days_ago=20)
        self.certify(user, self.u2, days_ago=10)
        me, housing = self.orders(token)
        self.assertEqual(me, [self.u2.id, self.u10.id, self.park.id])
        self.assertEqual(housing, [self.u2.id, self.u10.id, self.park.id])

    def test_tc_int_565_order_stable_over_five_refreshes_and_summary_same(self):
        """AC-192-02：重复刷新 5 次，顺序与汇总身份均不变。"""
        user, token = self.make_user()
        self.certify(user, self.park, days_ago=30)
        self.certify(user, self.u10, days_ago=20)
        self.certify(user, self.u2, days_ago=10)
        first = None
        for _ in range(5):
            me, housing = self.orders(token)
            summary = self.api("get", "/me/housing", token=token).data["summary"]
            snap = (me, housing, summary["code"], summary["label"])
            first = first or snap
            self.assertEqual(snap, first)
        self.assertEqual(first[0], first[1])

    def test_tc_int_566_head_and_resident_rows_kept_summary_unchanged(self):
        """AC-192-03：A 为户主、B 为同住人，A 自然顺序在前但认证更晚 → 两行 A(户主)、B(同住人)，汇总身份为产权业主（C-34）。"""
        user, token = self.make_user()
        self.certify(user, self.u10, role="RESIDENT", days_ago=20, source="APPLICATION")
        self.certify(user, self.u2, role="HEAD", days_ago=1)
        data = self.api("get", "/me/housing", token=token).data
        self.assertEqual([(u["unit_id"], u["role"]) for u in data["units"]],
                         [(self.u2.id, "HEAD"), (self.u10.id, "RESIDENT")])
        self.assertEqual((data["summary"]["code"], data["summary"]["label"]), ("OWNER", "产权业主"))  # C-34：HEAD 与 OWNER 同为产权业主
        me_units = self.api("get", "/me", token=token).data["identities"]["units"]
        self.assertEqual([u["unit_id"] for u in me_units], [self.u2.id, self.u10.id])

    def test_tc_int_567_owner_plus_resident_same_unit_two_rows_in_housing(self):
        """AC-192-03：同一专有部分产权业主+同住人两条有效记录，/me/housing 仍两行（相邻），/me 一行。"""
        user, token = self.make_user()
        self.certify(user, self.u2, role="OWNER", days_ago=5, slot=1)
        self.certify(user, self.u2, role="RESIDENT", days_ago=4, slot=2, source="APPLICATION")
        self.certify(user, self.u10, role="OWNER", days_ago=9)
        me, housing = self.orders(token)
        self.assertEqual(housing, [self.u2.id, self.u2.id, self.u10.id])
        self.assertEqual(me, [self.u2.id, self.u10.id])

    def test_tc_int_568_guest_empty_lists(self):
        """AC-192-04：游客两处均为空列表，无报错。"""
        _, token = self.make_user()
        me, housing = self.orders(token)
        self.assertEqual((me, housing), ([], []))
