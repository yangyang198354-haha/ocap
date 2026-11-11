"""GROUP_D：管理员登录后台并查看注册用户目录（TC-E2E-305 / US-132 ~ 136）。"""
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone

from apps.committee.models import Seat
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class AdminDirectoryJourneyTests(ApiTestBase):
    def test_tc_e2e_305_admin_login_and_view_directory(self):
        """TC-E2E-305 / US-132 ~ 136：管理员登录后按实名搜索并看到身份/认证/实名/上次登录。"""
        self.make_admin(username="dir_admin", password="Admin12345")

        phone = next_phone()
        user, _ = self.make_user(phone=phone, nickname="业主甲")
        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])

        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="1",
                                           room=uuid4().hex[:8], unit_type="RESIDENCE")
        owner = RegistryOwner.objects.create(unit=unit, name="张三")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        today = timezone.localdate()
        Seat.objects.create(user=user, position="MEMBER",
                            term_start=today - timedelta(days=30),
                            term_end=today + timedelta(days=30),
                            status="ACTIVE", active_slot=1)

        login = self.api("post", "/admin/auth/login",
                         {"username": "dir_admin", "password": "Admin12345"})
        self.assert_ok(login)
        token = login.data["token"]

        resp = self.api("get", "/admin/users", {"q": "张三"}, token=token)
        self.assert_ok(resp)
        row = next(item for item in resp.data["results"] if item["id"] == user.id)
        self.assertEqual(row["identity_label"], "委员")
        self.assertEqual(row["certified_units"], 1)
        self.assertEqual(row["real_names"], ["张三"])
        self.assertIsNotNone(row["last_login_at"])
        self.assertTrue(row["phone"].endswith(phone[-4:]))
        self.assertNotIn(phone, row["phone"])
