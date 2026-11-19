"""ocap_profile_ux GROUP_D E2E：资料 → 实名 → 他人查看 → 头像 → 管理端席位之旅。

分层：e2e（多步完整 API 旅程，真实 ORM/视图/令牌；短信走 fakes）。
溯源：US-263、US-270、US-271、US-272、US-264。
"""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.committee.models import CommitteeConfig
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class ProfileUxJourneyTests(ApiTestBase):
    def test_profile_real_name_avatar_and_seat_admin_journey(self):
        # 1 产权业主完成清册认证（含清册姓名），同住人/访客为另一注册用户
        phone = next_phone()
        unit = RegistryUnit.objects.create(building="1栋", unit_no="2单元", floor="9", room="902")
        owner_row = RegistryOwner.objects.create(unit=unit, name="张三")
        RegistryPhone.objects.create(unit=unit, owner=owner_row, phone=phone)
        user, token, _ = self.register(phone=phone)
        Membership.objects.create(user_id=user["id"], unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1, registry_owner=owner_row)
        viewer, viewer_token, _ = self.register()

        # 2 编辑签名与实名开关（默认关闭 → 开启 → 他人可见）
        self.assert_ok(self.api("patch", "/me/profile",
                                {"signature": "业主委员会志愿者", "real_name_visible": False}, token=token))
        self.assertIsNone(self.api("get", f"/users/{user['id']}/profile",
                                  token=viewer_token).json()["real_name"])
        self.assert_ok(self.api("patch", "/me/profile", {"real_name_visible": True}, token=token))
        public = self.assert_ok(self.api("get", f"/users/{user['id']}/profile", token=viewer_token)).json()
        self.assertEqual((public["real_name"], public["signature"]), ("张三", "业主委员会志愿者"))
        self.assertNotIn("phone", public)

        # 3 头像 4.9MB 上传成功（5.1MB 在集成层覆盖）
        big = SimpleUploadedFile("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * int(4.9 * 1024 * 1024),
                                 content_type="image/png")
        uploaded = self.assert_ok(self.upload("/me/avatar", {"file": big}, token=token), 201).json()
        self.assert_ok(self.api("patch", "/me/profile", {"avatar_attachment_id": uploaded["id"]}, token=token))
        self.assertIsNotNone(self.api("get", f"/users/{user['id']}/profile",
                                      token=viewer_token).json()["avatar_url"])

        # 4 管理员赋予席位 → 列表默认 active 且分列持有人信息
        _, admin_token = self.make_admin()
        cfg = CommitteeConfig.load()
        cfg.cap_member = 5
        cfg.term_months_member = 12
        cfg.save()
        resp = self.assert_ok(self.api("post", "/admin/committee/seats",
                                       {"registry_owner_id": owner_row.id, "position": "MEMBER"},
                                       token=admin_token), 201)
        self.assert_ok(self.api("get", "/admin/committee/seats?bucket=active&building=1栋",
                                token=admin_token))
        seat = resp.json()
        self.assertEqual(seat["holder_detail"]["name"], "张三")
        self.assertTrue(seat["holder_detail"]["unit_text"])
        self.assertLessEqual(seat["term_end"], str(timezone.localdate().replace(year=timezone.localdate().year + 1)))
