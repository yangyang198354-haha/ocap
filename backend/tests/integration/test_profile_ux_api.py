"""ocap_profile_ux GROUP_D：资料页 / 公开 profile / 头像上限 / 席位 / 房屋关系 / 审批流程。

分层：integration（真实 ORM + DRF 视图，仅短信等外部依赖使用 fakes）。
溯源：US-260～US-272（REQ-FUNC-255～263、REQ-NFUNC-051/052）。
"""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.committee.models import Seat
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from tests.batch1118_support import SeatHolderBase
from tests.support import ApiTestBase, next_phone


def png(size: int) -> SimpleUploadedFile:
    return SimpleUploadedFile("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * size,
                              content_type="image/png")


class ProfileFieldsTests(ApiTestBase):
    def test_signature_and_switch_default_and_boundary(self):
        user, token = self.make_user()
        body = self.api("get", "/me/profile", token=token).json()
        self.assertEqual((body["signature"], body["real_name_visible"], body["real_name"]),
                         ("", False, None))
        resp = self.api("patch", "/me/profile", {"signature": "字" * 100}, token=token)
        self.assert_ok(resp)
        self.assertEqual(len(resp.json()["signature"]), 100)
        self.assert_error(self.api("patch", "/me/profile", {"signature": "字" * 101}, token=token),
                          400, "INVALID_VALUE")

    def test_real_name_requires_verified_owner(self):
        _, token = self.make_user()
        self.assert_error(self.api("patch", "/me/profile", {"real_name_visible": True}, token=token),
                          403, "FORBIDDEN")

    def test_committee_member_owner_can_show_real_name(self):
        """AC-271-03：最高身份为业委会职务时，有效产权业主仍可开启实名展示。"""
        unit = RegistryUnit.objects.create(building="3栋", unit_no="1单元", floor="2", room="201")
        owner = RegistryOwner.objects.create(unit=unit, name="王五")
        user, token = self.make_user(nickname="委员甲")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1, registry_owner=owner)
        self.make_seat(user)
        body = self.assert_ok(self.api("get", "/me/profile", token=token)).json()
        self.assertTrue(body["can_show_real_name"])
        self.assert_ok(self.api("patch", "/me/profile", {"real_name_visible": True}, token=token))

    def test_phone_matched_owner_without_link_can_show_real_name(self):
        """AC-271-03：历史记录未写 registry_owner，但手机号命中清册业主时同样可开启实名。"""
        unit = RegistryUnit.objects.create(building="4栋", unit_no="2单元", floor="5", room="501")
        owner = RegistryOwner.objects.create(unit=unit, name="赵六")
        phone = next_phone()
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        user, token = self.make_user(phone=phone, nickname="历史用户")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1)
        _, viewer_token = self.make_user()

        body = self.assert_ok(self.api("get", "/me/profile", token=token)).json()
        self.assertTrue(body["can_show_real_name"])
        self.assertEqual(body["real_name"], "赵六")
        self.assert_ok(self.api("patch", "/me/profile", {"real_name_visible": True}, token=token))
        pub = self.assert_ok(self.api("get", f"/users/{user.id}/profile", token=viewer_token)).json()
        self.assertEqual(pub["real_name"], "赵六")

    def test_owner_real_name_visibility_and_public_profile_whitelist(self):
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="902")
        owner = RegistryOwner.objects.create(unit=unit, name="张三")
        phone = next_phone()
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        user, token = self.make_user(phone=phone, nickname="昵称甲")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1, registry_owner=owner)
        viewer, viewer_token = self.make_user()

        self.assert_ok(self.api("patch", "/me/profile", {"real_name_visible": True}, token=token))
        resp = self.assert_ok(self.api("get", f"/users/{user.id}/profile", token=viewer_token))
        body = resp.json()
        self.assertEqual(set(body), {"id", "nickname", "avatar_url", "identity", "labels",
                                     "real_name", "signature", "is_self"})
        self.assertEqual(body["real_name"], "张三")
        text = resp.content.decode()
        for forbidden in ("phone", "email", "birthday", "account_no", "138", "139"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(self.api("get", f"/users/{user.id}/profile", token=token).json()["is_self"], True)
        self.assert_ok(self.api("patch", "/me/profile", {"real_name_visible": False}, token=token))
        self.assertIsNone(self.api("get", f"/users/{user.id}/profile", token=viewer_token).json()["real_name"])

        self.assert_ok(self.api("get", f"/users/{viewer.id}/profile", token=token))
        self.assert_error(self.api("get", "/users/999999/profile", token=token), 404, "NOT_FOUND")
        self.enterprise_401 = self.api("get", f"/users/{user.id}/profile")
        self.assertEqual(self.enterprise_401.status_code, 401)


class AvatarLimitTests(ApiTestBase):
    def test_avatar_5mb_boundary_and_type(self):
        _, token = self.make_user()
        self.assert_ok(self.upload("/me/avatar", {"file": png(int(4.9 * 1024 * 1024))}, token=token), 201)
        resp = self.upload("/me/avatar", {"file": png(5 * 1024 * 1024 + 1)}, token=token)
        self.assert_error(resp, 413, "FILE_TOO_LARGE")
        gif = SimpleUploadedFile("a.gif", b"GIF89a", content_type="image/gif")
        self.assert_error(self.upload("/me/avatar", {"file": gif}, token=token), 400)


class SeatListProfileUxTests(SeatHolderBase):
    def test_bucket_holder_detail_filters_and_permission(self):
        unit, owner, phones, _ = self.reg_unit(name="业主乙")
        pending = self.pending_seat(owner)
        user, token, _ = self.make_owner()
        bound = self.make_seat(user)
        ended = Seat.objects.create(user=user, position="MEMBER", term_start=timezone.localdate(),
                                    term_end=timezone.localdate(), status="REVOKED", active_slot=None)
        resp = self.assert_ok(self.api("get", "/admin/committee/seats", token=self.admin_token))
        body = resp.json()
        ids = {r["id"] for r in body["results"]}
        self.assertIn(bound.id, ids)
        self.assertIn(pending.id, ids)
        self.assertNotIn(ended.id, ids)
        self.assertEqual(body["ended_count"], 1)  # AC-265-01：折叠区标题条数
        row = next(r for r in body["results"] if r["id"] == pending.id)
        self.assertEqual(set(row["holder_detail"]), {"nickname", "name", "phone_masked", "unit_text",
                                                     "unit_type", "building", "unit_no", "floor",
                                                     "room", "area"})
        self.assertEqual(row["holder_detail"]["name"], "业主乙")
        self.assertNotIn(phones[0], resp.content.decode())

        ended_resp = self.assert_ok(self.api(
            "get", "/admin/committee/seats?bucket=ended", token=self.admin_token))
        self.assertEqual({r["id"] for r in ended_resp.json()["results"]}, {ended.id})
        self.assertIn("end_reason", ended_resp.json()["results"][0])

        filtered = self.assert_ok(self.api(
            "get", "/admin/committee/seats?building=1栋&unit_no=1单元", token=self.admin_token))
        self.assertEqual({r["id"] for r in filtered.json()["results"]}, {pending.id})
        self.assert_error(self.api("get", "/admin/committee/seats?bucket=oops", token=self.admin_token),
                          400, "INVALID_QUERY")
        self.assert_error(self.api("get", "/admin/committee/seats", token=token), 403)

    def test_bound_user_seat_shows_phone_matched_real_name(self):
        """按用户授予（无清册快照）的已绑定席位：姓名取认证房屋的清册实名（手机号命中，兼容未回填 registry_owner）。"""
        phone = next_phone()
        unit, _, _, _ = self.reg_unit(name="业主丙", phones=[phone])
        user, _ = self.make_user(phone=phone, nickname="丙哥")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1)
        seat = self.make_seat(user)
        body = self.assert_ok(self.api("get", "/admin/committee/seats", token=self.admin_token)).json()
        row = next(r for r in body["results"] if r["id"] == seat.id)
        self.assertEqual(row["bind_state"], "BOUND")
        self.assertEqual(row["holder_detail"]["name"], "业主丙")
        hit = self.assert_ok(self.api(
            "get", "/admin/committee/seats?name=业主丙", token=self.admin_token)).json()
        self.assertIn(seat.id, {r["id"] for r in hit["results"]})
        miss = self.assert_ok(self.api(
            "get", "/admin/committee/seats?name=查无此人", token=self.admin_token)).json()
        self.assertNotIn(seat.id, {r["id"] for r in miss["results"]})

    def test_bound_user_seat_shows_linked_registry_owner_name(self):
        """已绑定用户认证时记录了清册业主（registry_owner）→ 席位姓名取该业主姓名。"""
        unit, owner, _, _ = self.reg_unit(name="业主丁")
        user, _ = self.make_user(nickname="丁哥")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1, registry_owner=owner)
        seat = self.make_seat(user)
        body = self.assert_ok(self.api("get", "/admin/committee/seats", token=self.admin_token)).json()
        row = next(r for r in body["results"] if r["id"] == seat.id)
        self.assertEqual(row["holder_detail"]["name"], "业主丁")


class MembershipFilterTests(ApiTestBase):
    def test_filters_and_search(self):
        _, admin_token = self.make_admin()
        unit = RegistryUnit.objects.create(building="2栋", unit_no="3单元", floor="10", room="1001")
        owner = RegistryOwner.objects.create(unit=unit, name="李四")
        phone = next_phone()
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        user, _ = self.make_user(phone=phone, nickname="四哥")
        Membership.objects.create(user=user, unit=unit, role="HEAD", source="CERTIFIED",
                                  active_slot=1, head_slot=1, registry_owner=owner)
        resident, _ = self.make_user(nickname="同住丙")
        Membership.objects.create(user=resident, unit=unit, role="RESIDENT", source="APPLICATION",
                                  active_slot=1)

        def count(query):
            resp = self.assert_ok(self.api("get", f"/admin/memberships{query}", token=admin_token))
            return resp.json()["count"]

        self.assertEqual(count("?building=2栋&unit_no=3单元&floor=10"), 2)
        self.assertEqual(count("?building=9栋"), 0)
        self.assertEqual(count("?name=李四"), 2)  # AC-269-01：含同住人
        self.assertEqual(count(f"?phone={phone[-4:]}"), 1)
        self.assertEqual(count("?unit_keyword=1001"), 2)  # REQ-FUNC-284：专有部分标识/户号独立过滤
        self.assert_error(self.api("get", "/admin/memberships?phone=12ab", token=admin_token),
                          400, "INVALID_QUERY")


class FlowDetailTests(ApiTestBase):
    def test_flow_approver_identity_and_edit(self):
        _, admin_token = self.make_admin()
        approver, _ = self.make_user(nickname="审批甲")
        self.make_seat(approver)
        flow = self.make_flow(approvers=[approver], name="原名称")
        resp = self.assert_ok(self.api("get", "/admin/approval/flows", token=admin_token))
        row = next(r for r in resp.json()["results"] if r["id"] == flow.id)
        self.assertEqual(set(row["approvers"][0]), {"id", "nickname", "identity_label"})

        other, _ = self.make_user(nickname="审批乙")
        self.make_seat(other)
        resp = self.assert_ok(self.api("put", f"/admin/approval/flows/{flow.id}",
                                       {"name": "新名称", "approver_ids": [other.id]}, token=admin_token))
        self.assertEqual(resp.json()["name"], "新名称")
        self.assertEqual([a["id"] for a in resp.json()["approvers"]], [other.id])
