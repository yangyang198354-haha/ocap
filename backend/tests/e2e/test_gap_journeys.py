"""PHASE_09 E2E 旅程：GR-D-006-F01 补齐的 Must Have 故事（多步，经真实 HTTP API 串联）。

TC-E2E-014 账号与身份生命周期（US-006/010/013/025/028/035）
TC-E2E-015 业主代表赋予与身份失效后的在途事项（US-042/068/071）
TC-E2E-016 管理员账号与密码重置（US-011/073）
"""
from datetime import date, timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.approval.models import ApprovalInstance
from apps.core.models import RateLimit
from apps.polls.models import Poll
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase, next_phone


class AccountIdentityLifecycleJourneyTests(ApiTestBase):
    def test_register_certify_change_phone_cancel_reregister_and_recertify(self):
        """TC-E2E-014：注册（清册号码自动绑定户主）→ 换号 → 旧号不可登录/新号同账号 → 注销 → 同号再注册为全新游客
        → 清册号码已被管理员改为新号后重新认证。"""
        old_phone, new_phone = next_phone(), next_phone()
        unit = self.make_unit(phones=[old_phone])
        _, admin_token = self.make_admin()

        code = self.request_code(old_phone, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": old_phone, "code": code})
        self.assert_ok(reg, 201)
        user_id, token = reg.data["user"]["id"], reg.data["token"]
        # US-102：清册已登记该号码，注册即自动认证户主（原“注册后为游客”不再适用）
        self.assertEqual([row["unit_id"] for row in reg.data["auto_bound"]], [unit.id])
        self.assertIn("户主", self.api("get", "/me", token=token).data["identities"]["labels"])

        # 换号：身份保留，旧号不能再登录，新号进入同一账号
        RateLimit.objects.all().delete()
        old_code = self.request_me_code(token, "CHANGE_PHONE", target=old_phone)
        new_code = self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        changed = self.api("post", "/me/phone/change",
                           {"old_phone": old_phone, "new_phone": new_phone,
                            "old_code": old_code, "new_code": new_code}, token=token)
        self.assert_ok(changed)
        self.assertFalse(changed.data["merged"])
        self.assertFalse(User.objects.filter(phone=old_phone).exists())
        RateLimit.objects.all().delete()
        login = self.login_code(new_phone)
        self.assert_ok(login)
        self.assertEqual(login.data["user"]["id"], user_id)
        self.assertIn("户主", self.api("get", "/me", token=login.data["token"]).data["identities"]["labels"])

        # 注销后同号再注册：全新游客，身份不恢复
        RateLimit.objects.all().delete()
        cancel_code = self.request_me_code(login.data["token"], "CANCEL")
        self.assert_ok(self.api("post", "/me/cancel", {"phone": new_phone, "code": cancel_code},
                                token=login.data["token"]), 204)
        RateLimit.objects.all().delete()
        code = self.request_code(new_phone, "REGISTER")
        again = self.api("post", "/auth/register", {"phone": new_phone, "code": code})
        self.assert_ok(again, 201)
        self.assertNotEqual(again.data["user"]["id"], user_id)
        me = self.api("get", "/me", token=again.data["token"])
        self.assertEqual(me.data["identities"]["labels"], ["游客"])

        # 清册里仍是旧号：认证按清册比对被拒；管理员把清册改为新号后认证成功（AC-035-03）
        refused = self.api("post", "/certifications", {"unit_id": unit.id}, token=again.data["token"])
        self.assert_error(refused, 422, "PHONE_NOT_IN_REGISTRY")
        self.assert_ok(self.api("put", f"/admin/registry/units/{unit.id}/owners",
                                {"owners": [{"name": "新业主", "phones": [new_phone]}]}, token=admin_token))
        ok = self.api("post", "/certifications", {"unit_id": unit.id}, token=again.data["token"])
        self.assert_ok(ok, 201)
        self.assertEqual(ok.data["role"], "HEAD")


class RepresentativeInFlightJourneyTests(ApiTestBase):
    def test_grant_representatives_vote_then_seat_revoked_in_flight(self):
        """TC-E2E-015：管理员配置并赋予 2 名业主代表 → 主任发起代表投票 → R1 作答 → R2 身份被撤销后作答被拒
        → 另有在途决议发起人身份被撤销后仍由指定审批人通过。"""
        _, admin_token = self.make_admin()
        self.assert_ok(self.api("put", "/admin/committee/config",
                                {"term_months_rep": 12, "cap_rep": 2}, token=admin_token))
        chair, chair_token, _ = self.make_owner()
        chair_seat = self.make_seat(chair, "CHAIR")
        approver, approver_token, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        reps = []
        for _ in range(2):
            rep, rep_token, _ = self.make_owner()
            granted = self.api("post", "/admin/committee/seats",
                               {"user_id": rep.id, "position": "REPRESENTATIVE",
                                "term_start": str(date.today())}, token=admin_token)
            self.assert_ok(granted, 201)
            reps.append((rep, rep_token, granted.data["id"]))
        flow = self.make_flow(scope="RESOLUTION", mode="DESIGNATED", approvers=[approver])
        resolution = self.api("post", "/resolutions",
                              {"title": "在途决议", "content": "内容", "approval_flow_id": flow.id},
                              token=chair_token)
        self.assert_ok(resolution, 201)
        poll = self.api("post", "/polls",
                        {"title": "代表投票", "kind": "REP_VOTE",
                         "deadline": (timezone.now() + timedelta(days=1)).isoformat(),
                         "questions": [{"title": "同意?", "qtype": "AGREE_OPPOSE_ABSTAIN"}]},
                        token=chair_token)
        self.assert_ok(poll, 201)
        row = Poll.objects.get(id=poll.data["id"])
        self.assertEqual(row.participant_count, 2)
        answers = {"answers": [{"question_id": row.questions.get().id, "value": "AGREE"}]}
        self.assert_ok(self.api("post", f"/polls/{row.id}/responses", answers, token=reps[0][1]), 201)

        # R2 身份被撤销、发起人（主任）身份被撤销
        self.assert_ok(self.api("delete", f"/admin/committee/seats/{reps[1][2]}", token=admin_token), 204)
        self.assert_error(self.api("post", f"/polls/{row.id}/responses", answers, token=reps[1][1]), 403)
        self.assert_ok(self.api("delete", f"/admin/committee/seats/{chair_seat.id}", token=admin_token), 204)

        # 在途事项不变；审批人仍可通过；已提交的答卷保持，分母仍为发起时的 2
        self.assertEqual(Resolution.objects.get(id=resolution.data["id"]).status, "PENDING")
        instance = ApprovalInstance.objects.get(subject_type="resolution",
                                                subject_id=resolution.data["id"])
        self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                {"action": "APPROVE"}, token=approver_token))
        self.assertEqual(Resolution.objects.get(id=resolution.data["id"]).status, "APPROVED")
        row.refresh_from_db()
        self.assertEqual((row.responses.count(), row.participant_count), (1, 2))


class AdminPasswordResetJourneyTests(ApiTestBase):
    def test_admin_creates_admin_then_resets_password(self):
        """TC-E2E-016：管理员 A 创建管理员 B → B 登录 → A 重置 B 密码 → B 旧令牌/旧密码失效、新密码可登录 → 普通用户无权重置。"""
        a, a_token = self.make_admin(password="AdminA12345")
        created = self.api("post", "/admin/admins", {"username": "journeyb", "password": "AdminB12345"},
                           token=a_token)
        self.assert_ok(created, 201)
        b_id = created.data["id"]
        b_login = self.api("post", "/admin/auth/login", {"username": "journeyb", "password": "AdminB12345"})
        self.assert_ok(b_login)
        _, user_token = self.make_user()
        self.assert_error(self.api("post", f"/admin/admins/{b_id}/reset-password",
                                   {"password": "NewPass2026x"}, token=user_token), 403)
        self.assert_ok(self.api("post", f"/admin/admins/{b_id}/reset-password",
                                {"password": "NewPass2026x"}, token=a_token), 204)
        self.assert_error(self.api("get", "/admin/audit-logs", token=b_login.data["token"]), 401)
        self.assert_error(self.api("post", "/admin/auth/login",
                                   {"username": "journeyb", "password": "AdminB12345"}), 400)
        again = self.api("post", "/admin/auth/login", {"username": "journeyb", "password": "NewPass2026x"})
        self.assert_ok(again)
        self.assert_ok(self.api("get", "/admin/audit-logs", token=again.data["token"]))
