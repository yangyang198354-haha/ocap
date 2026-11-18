"""PHASE_08 集成测试（ocap_batch_1118）：席位授予清册业主、三入口自动绑定、冲突、清册变化失效、占名额（US-256~258）。

关联 AC-256-01~07、AC-257-01~09、AC-258-01~04、REQ-NFUNC-049。分层：integration。TC-INT-1020 起。
姓名/手机号均为合成值（C-79）；手机号经 tests.support.next_phone 生成，断言响应不含完整手机号。
"""
from datetime import timedelta

from django.core import mail
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.committee.models import CommitteeConfig, Seat
from apps.committee.services import CommitteeCommands, add_months
from apps.core.models import AuditLog
from apps.integrations.fakes import FakeSmsGateway
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal, Membership
from tests.batch1118_support import SeatHolderBase
from tests.support import next_phone


def today():
    return timezone.localdate()


class GrantToRegistryOwnerTests(SeatHolderBase):
    def test_tc_int_1020_grant_to_unregistered_owner_creates_pending_seat_and_audit(self):
        """TC-INT-1020 / AC-256-01、AC-258-04：授予未注册清册业主 → 201，席位 user=None、bind_state=PENDING_BIND、holder 含专有部分与姓名，
        结束日=开始日+12 个月；审计 SEAT_GRANTED 含 holder 且审计与响应均不含手机号。"""
        unit, owner, phones, _ = self.reg_unit()
        resp = self.grant_owner(owner, "MEMBER")
        self.assert_ok(resp, 201)
        body = resp.json()
        self.assertIsNone(body["user"])
        self.assertEqual(body["bind_state"], "PENDING_BIND")
        self.assertEqual(body["holder"], {"kind": "REGISTRY_OWNER", "unit_text": unit.specific_part, "owner_name": "业主甲"})
        self.assertEqual(body["term_end"], str(add_months(today(), 12)))
        self.assertEqual(body["status"], "ACTIVE")
        log = self.actions("SEAT_GRANTED").latest("id")
        self.assertEqual(log.detail["holder"], {"owner_id": owner.id, "unit": unit.specific_part, "owner_name": "业主甲"})
        self.assertNotIn(phones[0], str(log.detail))
        self.assertNotIn(phones[0], resp.content.decode())

    def test_tc_int_1021_candidates_list_both_owners_masked_phone_and_admin_only(self):
        """TC-INT-1021 / AC-256-02、REQ-NFUNC-046(4)：同一专有部分两位业主 → 候选两位姓名，手机号脱敏（无完整号码）；seated/registered 标注；
        非管理员 403、未登录 401；unit_id 非法 400 INVALID_QUERY、不存在 404。"""
        p1, p2 = next_phone(), next_phone()
        unit, owner_a, _, (owner_b,) = self.reg_unit(phones=[p1], extra_owners=[("业主乙", p2)])
        resp = self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=self.admin_token)
        self.assert_ok(resp)
        names = {o["name"]: o for o in resp.json()["owners"]}
        self.assertEqual(set(names), {"业主甲", "业主乙"})
        for phone in (p1, p2):
            self.assertNotIn(phone, resp.content.decode())
        self.assertIn("*", names["业主甲"]["phone_masked"])
        self.assertEqual((names["业主甲"]["seated"], names["业主甲"]["registered"]), (False, False))
        self.pending_seat(owner_a)
        resp = self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=self.admin_token)
        flags = {o["name"]: o["seated"] for o in resp.json()["owners"]}
        self.assertEqual(flags, {"业主甲": True, "业主乙": False})
        _, utoken = self.make_user()
        self.assertEqual(self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=utoken).status_code, 403)
        self.assertEqual(self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}).status_code, 401)
        self.assert_error(self.api("get", "/admin/committee/owner-candidates", {"unit_id": "x"}, token=self.admin_token), 400, "INVALID_QUERY")
        self.assert_error(self.api("get", "/admin/committee/owner-candidates", {"unit_id": 99999999}, token=self.admin_token), 404, "NOT_FOUND")
        # 另一位业主可单独授予，不受影响
        self.assert_ok(self.grant_owner(owner_b), 201)

    def test_tc_int_1022_pending_seat_occupies_cap_and_revoke_releases(self):
        """TC-INT-1022 / AC-256-03、AC-258-02：委员上限 6、已有 6 个有效席位（其中 1 个待绑定）→ 再授予 409 CAP_REACHED、席位数不变；撤销待绑定后再授予成功。"""
        cfg = CommitteeConfig.load()
        cfg.cap_member = 6
        cfg.save()
        for _ in range(5):
            self.make_seat(self.make_owner()[0], "MEMBER")
        unit, owner, _, _ = self.reg_unit()
        pending = self.pending_seat(owner)
        _, owner2, _, _ = self.reg_unit(name="业主丙", room="903")
        count = Seat.objects.count()
        self.assert_error(self.grant_owner(owner2), 409, "CAP_REACHED")
        self.assertEqual(Seat.objects.count(), count)
        self.assertEqual(self.api("delete", f"/admin/committee/seats/{pending.id}", token=self.admin_token).status_code, 204)
        self.assertEqual(Seat.objects.get(id=pending.id).status, "REVOKED")
        self.assert_ok(self.grant_owner(owner2), 201)
        self.assertEqual(Seat.objects.count(), count + 1)

    def test_tc_int_1023_same_owner_cannot_hold_second_seat(self):
        """TC-INT-1023 / AC-256-04：业主甲已有有效席位，再授予另一职位 → 409 ALREADY_SEATED，席位新增数 0。"""
        _, owner, _, _ = self.reg_unit()
        self.pending_seat(owner, "MEMBER")
        count = Seat.objects.count()
        self.assert_error(self.grant_owner(owner, "VICE_CHAIR"), 409, "ALREADY_SEATED")
        self.assertEqual(Seat.objects.count(), count)

    def test_tc_int_1024_registered_and_certified_owner_gets_direct_effect(self):
        """TC-INT-1024 / AC-256-05：被授予的清册业主已注册并认证（手机号回退口径）→ 席位直接对应该用户，不处于待绑定，/me 委员身份显示。"""
        phone = next_phone()
        unit, owner, _, _ = self.reg_unit(phones=[phone])
        user, token, _ = self.make_owner(phone=phone, unit=unit)
        resp = self.grant_owner(owner, "MEMBER")
        self.assert_ok(resp, 201)
        self.assertEqual(resp.json()["user"]["id"], user.id)
        self.assertEqual(resp.json()["bind_state"], "BOUND")
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertEqual(me["committee"]["position"], "MEMBER")
        self.assertIn("委员", me["labels"])

    def test_tc_int_1025_term_errors_unchanged(self):
        """TC-INT-1025 / AC-256-06：任期未配置 → 409 TERM_NOT_CONFIGURED；开始日使结束日不晚于今天 → 400 INVALID_VALUE；均无席位新增。"""
        _, owner, _, _ = self.reg_unit()
        count = Seat.objects.count()
        self.assert_error(self.grant_owner(owner, "MEMBER", start=today() - timedelta(days=400)), 400, "INVALID_VALUE")
        cfg = CommitteeConfig.load()
        cfg.term_months_member = None
        cfg.save()
        self.assert_error(self.grant_owner(owner, "MEMBER"), 409, "TERM_NOT_CONFIGURED")
        self.assertEqual(Seat.objects.count(), count)

    def test_tc_int_1026_non_admin_cannot_grant_and_param_validation(self):
        """TC-INT-1026 / AC-256-07：普通用户 403、未登录 401；user_id 与 registry_owner_id 都给/都不给 → 400；registry_owner_id 非整数(bool/字符串) → 400；不存在 → 404；席位新增 0。"""
        _, owner, _, _ = self.reg_unit()
        _, utoken = self.make_user()
        count = Seat.objects.count()
        self.assertEqual(self.grant_owner(owner, token=utoken).status_code, 403)
        self.assertEqual(self.api("post", "/admin/committee/seats", {"registry_owner_id": owner.id, "position": "MEMBER"}).status_code, 401)
        user, _, _ = self.make_owner()
        for body in ({"position": "MEMBER"}, {"position": "MEMBER", "user_id": user.id, "registry_owner_id": owner.id},
                     {"position": "MEMBER", "registry_owner_id": True}, {"position": "MEMBER", "registry_owner_id": "7"}):
            self.assert_error(self.api("post", "/admin/committee/seats", body, token=self.admin_token), 400, "INVALID_VALUE")
        self.assert_error(self.api("post", "/admin/committee/seats", {"position": "MEMBER", "registry_owner_id": 99999999}, token=self.admin_token), 404, "NOT_FOUND")
        self.assertEqual(Seat.objects.count(), count)
        # user_id 旧路径保持
        self.assert_ok(self.api("post", "/admin/committee/seats", {"position": "MEMBER", "user_id": user.id}, token=self.admin_token), 201)


class BindOnCertificationTests(SeatHolderBase):
    def setUp(self):
        super().setUp()
        self.phone = next_phone()
        self.unit, self.owner, _, _ = self.reg_unit(phones=[self.phone])
        self.seat = self.pending_seat(self.owner, "MEMBER")

    def reload(self):
        return Seat.objects.get(id=self.seat.id)

    def test_tc_int_1030_manual_certification_binds_seat_without_notification(self):
        """TC-INT-1030 / AC-257-01、AC-257-05：待绑定期间业主甲新注册（未认证）无任何委员权限（表决 403）；手动认证（姓名+手机号一致）成功后
        席位 待绑定→在任并绑定该用户，/me 身份委员，审计新增 1 条 SEAT_BOUND（via=MANUAL），不发短信/邮件。"""
        user, token = self.new_registered_user(self.phone)
        res = self.half_resolution()
        self.assert_error(self.api("post", f"/resolutions/{res.id}/votes", {"choice": "AGREE"}, token=token), 403, "FORBIDDEN")
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertIsNone(me["committee"])
        FakeSmsGateway.shared().reset()
        mail.outbox.clear()
        before = self.actions("SEAT_BOUND").count()
        resp = self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主甲"}, token=token)
        self.assert_ok(resp, 201)
        seat = self.reload()
        self.assertEqual((seat.user_id, seat.status), (user.id, "ACTIVE"))
        self.assertIsNotNone(seat.bound_at)
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertEqual(me["committee"]["position"], "MEMBER")
        self.assertEqual(self.actions("SEAT_BOUND").count(), before + 1)
        detail = self.actions("SEAT_BOUND").latest("id").detail
        self.assertEqual((detail["via"], detail["user_id"]), ("MANUAL", user.id))
        self.assertEqual(FakeSmsGateway.shared().sent, [])
        self.assertEqual(len(mail.outbox), 0)

    def test_tc_int_1031_appeal_approval_binds_seat(self):
        """TC-INT-1031 / AC-257-02：业主甲经申诉（owner_name=业主甲，手机号不在清册）被管理员通过 → 同样绑定并生效，via=APPEAL。"""
        user, token = self.make_user()
        appeal = Appeal.objects.create(user=user, unit=self.unit, owner_name="业主甲")
        resp = self.api("post", f"/admin/appeals/{appeal.id}/decision", {"decision": "APPROVE"}, token=self.admin_token)
        self.assert_ok(resp)
        seat = self.reload()
        self.assertEqual(seat.user_id, user.id)
        self.assertEqual(self.actions("SEAT_BOUND").latest("id").detail["via"], "APPEAL")
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertEqual(me["committee"]["position"], "MEMBER")

    def test_tc_int_1032_phone_match_confirm_binds_seat(self):
        """TC-INT-1032 / AC-257-03：手机号匹配引导确认认证成功 → 同样绑定并生效，via=PHONE_MATCH。"""
        user, token = self.new_registered_user(self.phone)
        resp = self.api("post", "/me/registry-matches/confirm", {"unit_ids": [self.unit.id]}, token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.json()["succeeded"], 1)
        seat = self.reload()
        self.assertEqual(seat.user_id, user.id)
        self.assertEqual(self.actions("SEAT_BOUND").latest("id").detail["via"], "PHONE_MATCH")

    def test_tc_int_1033_other_owner_certification_does_not_bind(self):
        """TC-INT-1033 / AC-257-04：同一专有部分另一位业主乙（另一手机号）认证 → 业主甲的待绑定席位不变，业主乙不获得任何席位角色。"""
        pb = next_phone()
        RegistryPhone.objects.create(unit=self.unit, owner=RegistryOwner.objects.create(unit=self.unit, name="业主乙"), phone=pb)
        user_b, token_b = self.new_registered_user(pb)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主乙"}, token=token_b), 201)
        seat = self.reload()
        self.assertIsNone(seat.user_id)
        self.assertEqual(self.api("get", "/admin/committee/seats", token=self.admin_token).json()["results"][0]["bind_state"], "PENDING_BIND")
        self.assertIsNone(self.assert_ok(self.api("get", "/me", token=token_b)).data["identities"]["committee"])
        self.assertFalse(Seat.objects.filter(user=user_b).exists())

    def test_tc_int_1034_existing_seat_causes_conflict_kept_pending_and_audited(self):
        """TC-INT-1034 / AC-257-06：绑定时该用户已持有另一有效席位 → 绑定失败、待绑定席位保持（bind_state=CONFLICT）、审计 SEAT_BIND_CONFLICT，用户既有席位不变；认证本身仍成功。"""
        user, token = self.new_registered_user(self.phone)
        existing = self.make_seat(user, "VICE_CHAIR")
        resp = self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主甲"}, token=token)
        self.assert_ok(resp, 201)
        seat = self.reload()
        self.assertIsNone(seat.user_id)
        self.assertIsNotNone(seat.bind_conflict_at)
        rows = self.api("get", "/admin/committee/seats", token=self.admin_token).json()["results"]
        states = {r["id"]: r["bind_state"] for r in rows}
        self.assertEqual(states[self.seat.id], "CONFLICT")
        self.assertEqual(self.actions("SEAT_BIND_CONFLICT").latest("id").detail["user_id"], user.id)
        existing.refresh_from_db()
        self.assertEqual((existing.user_id, existing.position, existing.status), (user.id, "VICE_CHAIR", "ACTIVE"))

    def test_tc_int_1035_seat_bound_once_second_user_does_not_rebind(self):
        """TC-INT-1035 / AC-257-07、NFUNC-049(3)：同一业主甲两个号码对应两个账号；第一个认证绑定后，第二个再认证 → 席位持有人不变，不重复绑定（SEAT_BOUND 仍 1 条）。"""
        phone2 = next_phone()
        RegistryPhone.objects.create(unit=self.unit, owner=self.owner, phone=phone2)
        u1, t1 = self.new_registered_user(self.phone)
        u2, t2 = self.new_registered_user(phone2)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主甲"}, token=t1), 201)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主甲"}, token=t2), 201)
        self.assertEqual(self.reload().user_id, u1.id)
        self.assertEqual(self.actions("SEAT_BOUND").count(), 1)
        self.assertIsNone(self.assert_ok(self.api("get", "/me", token=t2)).data["identities"]["committee"])

    def test_tc_int_1036_representative_seat_binds_with_rep_identity_only(self):
        """TC-INT-1036 / AC-257-08：待绑定业主代表席位，业主甲认证后身份为业主代表，不具备业委会权限（表决 403、不属 is_member）。"""
        unit, owner, phones, _ = self.reg_unit(name="业主丁", room="905")
        rep = self.pending_seat(owner, "REPRESENTATIVE")
        user, token = self.new_registered_user(phones[0])
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id, "name": "业主丁"}, token=token), 201)
        rep.refresh_from_db()
        self.assertEqual(rep.user_id, user.id)
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertEqual(me["committee"]["position"], "REPRESENTATIVE")
        self.assertIn("业主代表", me["labels"])
        res = self.half_resolution()
        self.assert_error(self.api("post", f"/resolutions/{res.id}/votes", {"choice": "AGREE"}, token=token), 403, "FORBIDDEN")

    def test_tc_int_1037_term_not_extended_on_late_bind_and_expired_term_blocks_bind(self):
        """TC-INT-1037 / AC-257-09：授予日起 12 个月、第 3 个月才绑定（授予开始日=今天−90 天）→ 绑定后 term_start/term_end 不变；
        另一席位任期已结束（term_end<今天）后认证 → 不绑定，用户无席位角色。"""
        late_phone = next_phone()
        unit, owner, _, _ = self.reg_unit(name="业主戊", phones=[late_phone], room="906")
        start = today() - timedelta(days=90)
        seat = Seat.objects.get(id=self.grant_owner(owner, "MEMBER", start=start).data["id"])
        term = (seat.term_start, seat.term_end)
        self.assertEqual(term, (start, add_months(start, 12)))
        user, token = self.new_registered_user(late_phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id, "name": "业主戊"}, token=token), 201)
        seat.refresh_from_db()
        self.assertEqual(seat.user_id, user.id)
        self.assertEqual((seat.term_start, seat.term_end), term)
        # 任期已结束
        Seat.objects.filter(id=self.seat.id).update(term_end=today() - timedelta(days=1))
        user2, token2 = self.new_registered_user(self.phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": self.unit.id, "name": "业主甲"}, token=token2), 201)
        self.assertIsNone(self.reload().user_id)
        self.assertIsNone(self.assert_ok(self.api("get", "/me", token=token2)).data["identities"]["committee"])


class SeatListAndReconcileTests(SeatHolderBase):
    def test_tc_int_1040_list_distinguishes_bound_and_pending_and_hides_phone(self):
        """TC-INT-1040 / AC-258-01、AC-258-04：列表第 1 行已绑定用户（昵称），另 1 行待绑定清册业主（专有部分 · 姓名，状态 PENDING_BIND）；响应无手机号明文；查询数不随行数增长。"""
        user, _, _ = self.make_owner()
        user.nickname = "昵称甲"
        user.save()
        bound = self.make_seat(user, "MEMBER")
        unit, owner, phones, _ = self.reg_unit(name="业主乙")
        self.pending_seat(owner)
        resp = self.api("get", "/admin/committee/seats", token=self.admin_token)
        self.assert_ok(resp)
        rows = {r["id"]: r for r in resp.json()["results"]}
        bound_row = next(r for r in rows.values() if r["user"] and r["user"]["id"] == user.id)
        pend_row = next(r for r in rows.values() if r["user"] is None)
        self.assertEqual((bound_row["bind_state"], bound_row["user"]["nickname"]), ("BOUND", "昵称甲"))
        self.assertEqual((pend_row["bind_state"], pend_row["holder"]["unit_text"], pend_row["holder"]["owner_name"]),
                         ("PENDING_BIND", unit.specific_part, "业主乙"))
        self.assertNotIn(phones[0], resp.content.decode())
        self.assertNotIn(user.phone, resp.content.decode())

        counter = {"n": 0}

        def queries(extra):
            for _ in range(extra):
                counter["n"] += 1
                _, o, _, _ = self.reg_unit(name=f"业主增{counter['n']}", room=f"91{counter['n']}")
                self.pending_seat(o)
            with CaptureQueriesContext(connection) as ctx:
                self.assert_ok(self.api("get", "/admin/committee/seats", {"page_size": 50}, token=self.admin_token))
            return len(ctx)
        small = queries(1)
        large = queries(5)
        self.assertLessEqual(large, small + 1)

    def test_tc_int_1041_pending_seat_can_change_position_and_keeps_holder(self):
        """TC-INT-1041 / AC-258-02：待绑定席位可"变更职位"（新席位保留持有人记录、仍待绑定，原席位 REPLACED 释放原职位名额，审计 SEAT_CHANGED）。"""
        _, owner, _, _ = self.reg_unit()
        seat = self.pending_seat(owner, "MEMBER")
        resp = self.api("patch", f"/admin/committee/seats/{seat.id}", {"position": "VICE_CHAIR"}, token=self.admin_token)
        self.assert_ok(resp)
        body = resp.json()
        self.assertEqual((body["position"], body["bind_state"], body["holder"]["owner_name"]), ("VICE_CHAIR", "PENDING_BIND", "业主甲"))
        self.assertEqual(Seat.objects.filter(status="ACTIVE", position="MEMBER").count(), 0)
        seat.refresh_from_db()
        self.assertEqual(seat.status, "REPLACED")
        self.assertEqual(Seat.objects.filter(status="ACTIVE", holder_owner_id=owner.id).count(), 1)
        self.assertTrue(self.actions("SEAT_CHANGED").exists())

    def test_tc_int_1042_registry_owner_rename_invalidates_pending_seat_with_audit(self):
        """TC-INT-1042 / AC-258-03：清册改名（PUT owners 使业主甲不再是该专有部分业主）→ 待绑定席位 INVALIDATED，原因"清册变化"，审计 SEAT_INVALIDATED 1 条；已绑定席位不受影响。"""
        unit, owner, _, _ = self.reg_unit()
        seat = self.pending_seat(owner)
        bound = self.make_seat(self.make_owner()[0], "MEMBER")
        resp = self.api("put", f"/admin/registry/units/{unit.id}/owners",
                        {"owners": [{"name": "业主改名", "phones": [next_phone()]}]}, token=self.admin_token)
        self.assert_ok(resp)
        seat.refresh_from_db()
        self.assertEqual((seat.status, seat.end_reason), ("INVALIDATED", "REGISTRY_CHANGED"))
        log = self.actions("SEAT_INVALIDATED").latest("id")
        self.assertEqual((log.detail["reason"], log.detail["reason_label"]), ("REGISTRY_CHANGED", "清册变化"))
        bound.refresh_from_db()
        self.assertEqual(bound.status, "ACTIVE")
        # 失效后释放名额：该业主不再占用席位
        self.assertFalse(Seat.objects.filter(status="ACTIVE", holder_owner_id=owner.id).exists())

    def test_tc_int_1043_unit_delete_invalidates_pending_seat(self):
        """TC-INT-1043 / AC-258-03：删除专有部分 → 其业主的待绑定席位失效并审计。"""
        unit, owner, _, _ = self.reg_unit(room="907")
        seat = self.pending_seat(owner)
        resp = self.api("delete", f"/admin/registry/units/{unit.id}", token=self.admin_token)
        self.assertIn(resp.status_code, (200, 204))
        seat.refresh_from_db()
        self.assertEqual((seat.status, seat.end_reason), ("INVALIDATED", "REGISTRY_CHANGED"))
        self.assertTrue(self.actions("SEAT_INVALIDATED").filter(object_id=str(seat.id)).exists())

    def test_tc_int_1044_reconcile_idempotent_and_keeps_unchanged_owner(self):
        """TC-INT-1044 / AC-258-03、NFUNC-049：reconcile_registry_seats 幂等；业主姓名未变的待绑定席位不被误失效。"""
        _, owner, _, _ = self.reg_unit(room="908")
        seat = self.pending_seat(owner)
        self.assertEqual(CommitteeCommands.reconcile_registry_seats(), 0)
        seat.refresh_from_db()
        self.assertEqual(seat.status, "ACTIVE")
        RegistryOwner.objects.filter(id=owner.id).update(name="被改名者")
        self.assertEqual(CommitteeCommands.reconcile_registry_seats(), 1)
        self.assertEqual(CommitteeCommands.reconcile_registry_seats(), 0)
        self.assertEqual(self.actions("SEAT_INVALIDATED").filter(object_id=str(seat.id)).count(), 1)
