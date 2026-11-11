"""GROUP_D：注册用户目录展示（US-132 ~ 136）TC-INT-389 ~ 397。"""
from datetime import datetime, timedelta
from uuid import uuid4

from django.db import connection
from django.utils import timezone

from apps.accounts.models import User
from apps.committee.models import Seat
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_account_no, next_phone


class SqlCounter:
    def __init__(self):
        self.selects = []

    def __call__(self, execute, sql, params, many, context):
        if sql.lstrip().upper().startswith("SELECT"):
            self.selects.append(sql)
        return execute(sql, params, many, context)


class AdminUserDirectoryTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def make_unit(self, room=None):
        return RegistryUnit.objects.create(
            building="1栋", unit_no="1单元", floor="1",
            room=room or uuid4().hex[:8], unit_type="RESIDENCE",
        )

    def add_owner(self, unit, name, phone=None):
        owner = RegistryOwner.objects.create(unit=unit, name=name)
        if phone:
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return owner

    def add_membership(self, user, unit, role="HEAD", ended=False):
        return Membership.objects.create(
            user=user, unit=unit, role=role, source="REGISTRY",
            active_slot=None if ended else 1,
            head_slot=1 if role == "HEAD" and not ended else None,
            ended_at=timezone.now() if ended else None,
        )

    def add_seat(self, user, position, active=True):
        today = timezone.localdate()
        return Seat.objects.create(
            user=user, position=position,
            term_start=today - timedelta(days=30),
            term_end=today + timedelta(days=30) if active else today - timedelta(days=1),
            status="ACTIVE", active_slot=1 if active else None,
        )

    def fetch(self, token=None, **params):
        resp = self.api("get", "/admin/users", params or None, token=token or self.admin_token)
        self.assert_ok(resp)
        return resp

    def rows(self, token=None, **params):
        return {row["id"]: row for row in self.fetch(token=token, **params).data["results"]}

    def test_tc_int_389_identity_priority(self):
        """TC-INT-389 / US-132 AC-132-01 ~ 04：最高身份优先级与过期席位回退。"""
        u1, _ = self.make_user()
        self.add_membership(u1, self.make_unit(), "HEAD")
        self.add_seat(u1, "MEMBER")

        u2, _ = self.make_user()
        self.add_membership(u2, self.make_unit(), "OWNER")
        self.add_seat(u2, "CHAIR")

        u3, _ = self.make_user()
        self.add_membership(u3, self.make_unit(), "HEAD")
        self.add_seat(u3, "REPRESENTATIVE", active=False)

        u4, _ = self.make_user()
        self.add_membership(u4, self.make_unit(), "RESIDENT")

        u5, _ = self.make_user()

        rows = self.rows()
        self.assertEqual(rows[u1.id]["identity_label"], "委员")
        self.assertEqual(rows[u2.id]["identity_label"], "主任")
        self.assertEqual(rows[u3.id]["identity_label"], "户主")
        self.assertEqual(rows[u4.id]["identity_label"], "同住人")
        self.assertEqual(rows[u5.id]["identity_label"], "游客")
        self.assertEqual(rows[u5.id]["certified_units"], 0)

    def test_tc_int_390_certified_units_count_and_revoke(self):
        """TC-INT-390 / US-132 AC-132-05、US-136 AC-136-02：认证套数去重与撤销后减少。"""
        user, _ = self.make_user()
        unit_a, unit_b = self.make_unit(), self.make_unit()
        self.add_membership(user, unit_a, "HEAD")
        membership_b = self.add_membership(user, unit_b, "RESIDENT")

        self.assertEqual(self.rows()[user.id]["certified_units"], 2)

        membership_b.ended_at = timezone.now()
        membership_b.active_slot = None
        membership_b.save(update_fields=["ended_at", "active_slot"])
        row = self.rows()[user.id]
        self.assertEqual(row["certified_units"], 1)
        self.assertEqual(row["identity_label"], "户主")

    def test_tc_int_391_real_names_dedupe_and_join(self):
        """TC-INT-391 / US-133 AC-133-01 ~ 03：多套实名去重保序。"""
        phone = next_phone()
        user, _ = self.make_user(phone=phone)
        unit_a, unit_b, unit_c = self.make_unit(), self.make_unit(), self.make_unit()
        self.add_owner(unit_a, "张三", phone)
        self.add_owner(unit_b, "李四", phone)
        self.add_owner(unit_c, "张三", phone)
        self.add_membership(user, unit_a, "HEAD")
        self.add_membership(user, unit_b, "OWNER")
        self.add_membership(user, unit_c, "OWNER")

        row = self.rows()[user.id]
        self.assertEqual(row["real_names"], ["张三", "李四"])
        self.assertEqual(row["certified_units"], 3)

    def test_tc_int_392_real_names_empty_cases(self):
        """TC-INT-392 / US-133 AC-133-04 ~ 05：无手机号/未匹配/非产权/撤销后不显示实名。"""
        no_phone = User.objects.create(account_no=next_account_no(), phone=None)
        self.add_membership(no_phone, self.make_unit(), "HEAD")

        unmatched, _ = self.make_user()
        self.add_membership(unmatched, self.make_unit(), "HEAD")

        resident_phone = next_phone()
        resident, _ = self.make_user(phone=resident_phone)
        resident_unit = self.make_unit()
        self.add_owner(resident_unit, "王五", resident_phone)
        self.add_membership(resident, resident_unit, "RESIDENT")

        revoked_phone = next_phone()
        revoked, _ = self.make_user(phone=revoked_phone)
        revoked_unit = self.make_unit()
        self.add_owner(revoked_unit, "赵六", revoked_phone)
        self.add_membership(revoked, revoked_unit, "HEAD", ended=True)

        rows = self.rows()
        self.assertEqual(rows[no_phone.id]["real_names"], [])
        self.assertEqual(rows[unmatched.id]["real_names"], [])
        self.assertEqual(rows[resident.id]["real_names"], [])
        self.assertEqual(rows[revoked.id]["real_names"], [])
        self.assertEqual(rows[revoked.id]["identity_label"], "游客")
        self.assertEqual(rows[revoked.id]["certified_units"], 0)

    def test_tc_int_393_last_login(self):
        """TC-INT-393 / US-134 AC-134-01 ~ 04：登录时间 ISO 与从未登录 null。"""
        logged, _ = self.make_user()
        logged.last_login_at = timezone.now()
        logged.save(update_fields=["last_login_at"])
        never, _ = self.make_user()

        rows = self.rows()
        parsed = datetime.fromisoformat(rows[logged.id]["last_login_at"])
        self.assertIsNotNone(parsed.tzinfo)
        self.assertIsNone(rows[never.id]["last_login_at"])

    def test_tc_int_394_search_real_name_and_existing(self):
        """TC-INT-394 / US-135 AC-135-01 ~ 04：实名搜索与原有搜索并存。"""
        phone = next_phone()
        named, _ = self.make_user(phone=phone, nickname="昵称甲")
        unit = self.make_unit()
        self.add_owner(unit, "张三", phone)
        self.add_membership(named, unit, "HEAD")

        other, _ = self.make_user(phone="13900001234", nickname="昵称乙")

        self.assertIn(named.id, self.rows(q="张三"))
        self.assertIn(named.id, self.rows(q="昵称甲"))
        self.assertIn(named.id, self.rows(q=named.account_no))
        self.assertIn(named.id, self.rows(q=phone))
        self.assertIn(other.id, self.rows(q="1234"))
        resp = self.fetch(q="不存在")
        self.assertEqual(resp.data["count"], 0)
        self.assertEqual(resp.data["results"], [])

    def test_tc_int_395_search_same_registry_row_only(self):
        """TC-INT-395 / US-135、GR-B-001-F01：实名搜索不得跨 RegistryPhone 记录误匹配。"""
        phone = next_phone()
        user, _ = self.make_user(phone=phone)
        other_unit = self.make_unit()
        self.add_owner(other_unit, "张三", phone)
        own_unit = self.make_unit()
        self.add_owner(own_unit, "李四", phone)
        self.add_membership(user, own_unit, "OWNER")

        self.assertNotIn(user.id, self.rows(q="张三"))
        self.assertIn(user.id, self.rows(q="李四"))

    def test_tc_int_396_permissions(self):
        """TC-INT-396 / US-132 AC-132-06：未登录 401，普通用户 403。"""
        self.assertEqual(self.api("get", "/admin/users").status_code, 401)
        _, user_token = self.make_user()
        self.assertEqual(self.api("get", "/admin/users", token=user_token).status_code, 403)

    def test_tc_int_397_query_count_bounded(self):
        """TC-INT-397 / US-135、GR-B-001-F02：每页查询数不随行数增长。"""
        for _ in range(20):
            user, _ = self.make_user()
            unit = self.make_unit()
            self.add_owner(unit, "张三", user.phone)
            self.add_membership(user, unit, "HEAD")
            self.add_seat(user, "MEMBER")

        counter_one = SqlCounter()
        with connection.execute_wrapper(counter_one):
            self.fetch(page_size=1)
        counter_twenty = SqlCounter()
        with connection.execute_wrapper(counter_twenty):
            self.fetch(page_size=20)

        self.assertLessEqual(len(counter_twenty.selects), len(counter_one.selects) + 1)
        self.assertLessEqual(len(counter_twenty.selects), 10)
