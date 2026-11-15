"""ocap_product_review（MOD-074~080）后端集成用例：GROUP_C 自验证用例，GROUP_D 已接管并编号（TC-INT-515 ~ 532）；
补充用例见 test_product_review_ac.py（TC-INT-424 起）。"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.db import connection
from rest_framework.exceptions import AuthenticationFailed
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import AuthToken
from apps.accounts.services import _sha256
from apps.committee.models import Seat
from apps.committee.services import CommitteeQuery
from apps.content.models import ContentPost, StyleTemplate
from apps.core.audit import AuditLog
from apps.core.config import validate_amount_max
from apps.core.errors import ApiError
from apps.core.models import Attachment
from apps.identity.services import IdentityService
from apps.ledger.models import LedgerReport
from apps.residency.models import Appeal, Membership, ResidentApplication
from apps.residency.services import PendingRequestService
from tests.support import ApiTestBase


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE", original_name="i.pdf",
        content_type="application/pdf", size=10, sha256="x" * 64,
        storage_path=f"tmp/{uuid4().hex}", status="TEMP")


class HousingTests(ApiTestBase):
    def test_owner_sees_residents_and_pending_count_only_for_owned_units(self):
        """TC-INT-515 / AC-151-01、AC-153-01、AC-157-01（GROUP_C 自验证，GROUP_D 接管）：/me/housing：产权业主见同住人名单与待审计数（仅名下房屋），无手机号，查询数有界。"""
        owner, token, unit = self.make_owner()
        resident, _ = self.make_resident(unit)
        other_unit = self.make_unit()
        Membership.objects.create(user=owner, unit=other_unit, role="RESIDENT", source="APPLICATION",
                                  active_slot=1)
        applicant, _ = self.make_user()
        ResidentApplication.objects.create(applicant=applicant, unit=unit)
        ResidentApplication.objects.create(applicant=applicant, unit=other_unit)
        with CaptureQueriesContext(connection) as ctx:
            data = self.assert_ok(self.api("get", "/me/housing", token=token)).data
        self.assertLessEqual(len(ctx), 12)
        self.assertEqual(data["summary"], {"code": "OWNER", "label": "产权业主"})
        self.assertEqual(data["pending_review_count"], 1)
        rows = {u["unit_id"]: u for u in data["units"]}
        self.assertEqual(rows[unit.id]["role_label"], "产权业主")
        self.assertEqual([r["user_id"] for r in rows[unit.id]["residents"]], [resident.id])
        self.assertNotIn("phone", rows[unit.id]["residents"][0])
        self.assertEqual(rows[other_unit.id]["residents"], [])
        self.assertEqual(rows[other_unit.id]["pending_application_count"], 0)

    def test_resident_and_guest_get_empty_aggregates(self):
        """TC-INT-516 / AC-157-03、AC-151-03（GROUP_C 自验证，GROUP_D 接管）：同住人/游客的 /me/housing 聚合为空；未登录 401、管理员 403。"""
        _, _, unit = self.make_owner()
        resident, rtoken = self.make_resident(unit)
        data = self.assert_ok(self.api("get", "/me/housing", token=rtoken)).data
        self.assertEqual(data["summary"]["code"], "RESIDENT")
        self.assertEqual(data["units"][0]["residents"], [])
        guest, gtoken = self.make_user()
        data = self.assert_ok(self.api("get", "/me/housing", token=gtoken)).data
        self.assertEqual(data, {"summary": {"code": "GUEST", "label": "游客"}, "units": [],
                                "pending_review_count": 0})
        self.assert_error(self.api("get", "/me/housing"), 401)
        _, admin_token = self.make_admin()
        self.assert_error(self.api("get", "/me/housing", token=admin_token), 403)

    def test_multi_unit_summary_and_labels_use_highest_role(self):
        """TC-INT-517 / AC-157-01、AC-157-02（GROUP_C 自验证，GROUP_D 接管）：多房屋时汇总身份与 labels 取最高身份。"""
        user, token = self.make_user()
        low, high = self.make_unit(), self.make_unit()
        Membership.objects.create(user=user, unit=low, role="RESIDENT", source="APPLICATION", active_slot=1)
        Membership.objects.create(user=user, unit=high, role="HEAD", source="APPEAL", active_slot=1,
                                  head_slot=1)
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertEqual(me["summary"], {"code": "OWNER", "label": "产权业主"})
        self.assertEqual(me["labels"], ["产权业主"])
        self.assertEqual({u["role_label"] for u in me["units"]}, {"同住人", "产权业主"})

    def test_me_committee_ignores_expired_seat(self):
        """TC-INT-518 / AC-157-02、AC-154-03（GROUP_C 自验证，GROUP_D 接管）：/me committee 忽略已到期席位。"""
        user, token, _ = self.make_owner()
        seat = self.make_seat(user, "MEMBER")
        seat.term_end = timezone.localdate() - timedelta(days=1)
        seat.save()
        me = self.assert_ok(self.api("get", "/me", token=token)).data["identities"]
        self.assertIsNone(me["committee"])
        self.assertEqual(me["summary"]["code"], "OWNER")


class ClosedStatusTests(ApiTestBase):
    def test_cancel_closes_pending_only_and_writes_audit(self):
        """TC-INT-519 / AC-164-01、AC-164-03、AC-164-04（GROUP_C 自验证，GROUP_D 接管）：注销只关闭待处理申请/申诉并写审计，历史记录不变，重复关闭为 0。"""
        owner, otoken, unit = self.make_owner()
        user, token = self.make_user()
        pending_app = ResidentApplication.objects.create(applicant=user, unit=unit)
        pending_appeal = Appeal.objects.create(user=user, unit=unit)
        done_unit = self.make_unit()
        done = Appeal.objects.create(user=user, unit=done_unit, status="REJECTED", pending_slot=None,
                                     reject_reason="x")
        counts = PendingRequestService.close_for_cancelled_user(user)
        self.assertEqual(counts, {"resident_applications": 1, "appeals": 1})
        pending_app.refresh_from_db(), pending_appeal.refresh_from_db(), done.refresh_from_db()
        self.assertEqual((pending_app.status, pending_appeal.status, done.status),
                         ("CLOSED", "CLOSED", "REJECTED"))
        self.assertIsNone(pending_app.pending_slot)
        self.assertEqual(AuditLog.objects.filter(action__in=["RESIDENT_APPLICATION_CLOSED",
                                                             "APPEAL_CLOSED"]).count(), 2)
        self.assertEqual(PendingRequestService.close_for_cancelled_user(user),
                         {"resident_applications": 0, "appeals": 0})
        self.assertEqual(self.api("get", "/resident-applications/to-review", token=otoken).data, [])
        mine = self.api("get", "/resident-applications/mine", token=token).data
        self.assertEqual(mine[0]["status"], "CLOSED")

    def test_closed_records_cannot_be_decided(self):
        """TC-INT-520 / AC-164-02（GROUP_C 自验证，GROUP_D 接管）：已关闭记录再审批 → 409 ALREADY_CLOSED，不产生房屋关系。"""
        owner, otoken, unit = self.make_owner()
        user, _ = self.make_user()
        application = ResidentApplication.objects.create(applicant=user, unit=unit)
        appeal = Appeal.objects.create(user=user, unit=unit)
        PendingRequestService.close_for_cancelled_user(user)
        resp = self.api("post", f"/resident-applications/{application.id}/decision",
                        {"decision": "APPROVE"}, token=otoken)
        self.assert_error(resp, 409, "ALREADY_CLOSED")
        _, admin_token = self.make_admin()
        resp = self.api("post", f"/admin/appeals/{appeal.id}/decision", {"decision": "APPROVE"},
                        token=admin_token)
        self.assert_error(resp, 409, "ALREADY_CLOSED")
        self.assertFalse(Membership.objects.filter(user=user).exists())

    def test_identity_cancel_closes_pending(self):
        """TC-INT-521 / AC-164-01（GROUP_C 自验证，GROUP_D 接管）：IdentityService.cancel 关闭待处理申请。"""
        owner, _, unit = self.make_owner()
        user, _ = self.make_user()
        ResidentApplication.objects.create(applicant=user, unit=unit)
        code = self.request_me_code(self.token_of(user), "CANCEL")
        IdentityService.cancel(user, user.phone, code)
        self.assertEqual(ResidentApplication.objects.get(applicant=user).status, "CLOSED")


class ClaimPermissionAndLimitTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.member, self.mtoken, _ = self.make_owner()
        self.make_seat(self.member, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        self.flow = self.make_flow(scope="EXPENSE", approvers=[approver])
        self.admin, self.admin_token = self.make_admin()

    def _post(self, token, amount="100.00", member=None):
        invoice = _invoice(member or self.member)
        return self.api("post", "/claims/reimbursements", {
            "amount": amount, "reason": "r", "occurred_on": str(date.today()),
            "invoice_ids": [str(invoice.id)], "approval_flow_id": self.flow.id}, token=token)

    def test_only_active_committee_members_can_create(self):
        """TC-INT-522 / AC-154-01、AC-154-03（GROUP_C 自验证，GROUP_D 接管）：仅现任委员可发起报销/备用金；非成员/业主代表/到期席位 403；管理员令牌 401。"""
        plain, ptoken, _ = self.make_owner()
        rep, rtoken, _ = self.make_owner()
        self.make_seat(rep, "REPRESENTATIVE")
        expired, etoken, _ = self.make_owner()
        seat = self.make_seat(expired, "MEMBER")
        seat.term_end = timezone.localdate() - timedelta(days=1)
        seat.save()
        for token, who in ((ptoken, plain), (rtoken, rep), (etoken, expired)):
            resp = self._post(token, member=who)
            self.assert_error(resp, 403, "FORBIDDEN")
            resp = self.api("post", "/claims/advances", {"amount": "1.00"}, token=token)
            self.assert_error(resp, 403, "FORBIDDEN")
        self.assert_ok(self._post(self.mtoken), 201)
        self.assertEqual(self.api("post", "/claims/reimbursements", {}, token=self.admin_token)
                         .status_code, 401)

    def test_amount_limit_is_configurable_and_audited(self):
        """TC-INT-523 / AC-170-01、AC-170-02、AC-170-03（GROUP_C 自验证，GROUP_D 接管）：默认上限边界；管理员改为 500000 后新上限生效、旧记录不变、写审计。"""
        resp = self._post(self.mtoken, "1000000.01")
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertEqual(resp.json()["details"], {"max_amount": "1000000.00"})
        self.assert_ok(self._post(self.mtoken, "1000000.00"), 201)
        big = self._post(self.mtoken, "800000.00")
        self.assert_ok(big, 201)
        resp = self.api("put", "/admin/system-config/claim.amount_max", {"value": "500000"},
                        token=self.admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["value"], "500000.00")
        self.assertEqual(AuditLog.objects.filter(action="SYSTEM_CONFIG_CHANGED").count(), 1)
        resp = self._post(self.mtoken, "500000.01")
        self.assert_error(resp, 400, "INVALID_VALUE")
        self.assertIn("500000.00", resp.json()["message"])
        self.assert_ok(self._post(self.mtoken, "500000.00"), 201)
        self.assertEqual(self.api("get", f"/claims/{big.data['id']}", token=self.mtoken).data["amount"],
                         "800000.00")
        listing = self.api("get", "/admin/system-config", token=self.admin_token).data
        self.assertEqual(listing["claim.amount_max"], "500000.00")

    def test_amount_limit_validation_and_permission(self):
        """TC-INT-524 / AC-170-04（GROUP_C 自验证，GROUP_D 接管）：非法值 400、非管理员 403、既有键错误码不变。"""
        for bad in (0, -1, "abc", None, True, "1.234", "1000000000000.00"):
            resp = self.api("put", "/admin/system-config/claim.amount_max", {"value": bad},
                            token=self.admin_token)
            self.assert_error(resp, 400, "INVALID_VALUE")
        self.assert_error(self.api("put", "/admin/system-config/claim.amount_max", {"value": "1"},
                                   token=self.mtoken), 403)
        self.assertEqual(validate_amount_max(100), "100.00")
        with self.assertRaises(ApiError):
            validate_amount_max("")
        # 既有键的错误码不变
        resp = self.api("put", "/admin/system-config/audit.retention_months", {"value": 3},
                        token=self.admin_token)
        self.assert_error(resp, 400, "RETENTION_TOO_SHORT")

    def test_income_manual_and_import_respect_limit(self):
        """TC-INT-525 / AC-170-05（GROUP_C 自验证，GROUP_D 接管）：收入逐条录入与导入遵循同一金额上限。"""
        from apps.core.config import SystemConfig
        from apps.income.views import _parse_amount, _parse_rows

        SystemConfig.set("claim.amount_max", "500.00", None)
        record = {"occurred_on": "2026-01-01", "amount": "500.01", "category": "a"}
        resp = self.api("post", "/admin/income/sheets", {"records": [record]}, token=self.mtoken)
        self.assert_error(resp, 400, "INCOME_RECORD_INVALID")
        self.assertIn("500.00", str(resp.json()["details"]))
        record["amount"] = "500.00"
        self.assert_ok(self.api("post", "/admin/income/sheets", {"records": [record]}, token=self.mtoken), 201)
        self.assertEqual(_parse_amount("500.00"), Decimal("500.00"))
        rows = [["日期", "金额", "收入类别", "来源说明", "备注"], ["2026-01-01", "501", "", "", ""]]
        parsed = _parse_rows(rows)
        self.assertEqual(parsed["errors"][0]["reason"], "INVALID_FIELD")
        self.assertEqual(_parse_rows(rows, limit=Decimal("1000"))["errors"], [])

    def test_system_limits(self):
        """TC-INT-526 / AC-172-01、AC-170-02（GROUP_C 自验证，GROUP_D 接管）：/system/limits 的 7 个字段与鉴权（401/403）。"""
        data = self.assert_ok(self.api("get", "/system/limits", token=self.mtoken)).data
        self.assertEqual(data, {
            "claim_amount_max": "1000000.00", "poll_max_questions": 50, "poll_options_min": 2,
            "poll_options_max": 10, "vote_min_window_minutes": 60, "income_import_max_rows": 5000,
            "income_manual_max_records": 500})
        self.assert_error(self.api("get", "/system/limits"), 401)
        self.assert_error(self.api("get", "/system/limits", token=self.admin_token), 403)


class MiniappSessionTests(ApiTestBase):
    def _kind(self, resp):
        self.assert_ok(resp)
        return AuthToken.objects.get(key_hash=_sha256(resp.data["token"])).session_kind

    def _user_with_password(self):
        from django.contrib.auth.hashers import make_password

        user, _ = self.make_user()
        user.password = make_password("Passw0rd123")
        user.save()
        return user

    def test_client_miniapp_gets_extended_session_and_default_stays_idle(self):
        """TC-INT-527 / AC-155-01、AC-155-03（GROUP_C 自验证，GROUP_D 接管）：client=miniapp 的验证码/密码登录为 EXTENDED，缺省与 web 为 IDLE。"""
        user = self._user_with_password()
        body = {"identifier": user.phone, "password": "Passw0rd123"}
        self.assertEqual(self._kind(self.api("post", "/auth/login/password", body)), "IDLE")
        self.assertEqual(self._kind(self.api("post", "/auth/login/password", {**body, "client": "web"})),
                         "IDLE")
        self.assertEqual(self._kind(self.api("post", "/auth/login/password", {**body, "client": "miniapp"})),
                         "EXTENDED")
        code = self.request_code(user.phone, "LOGIN")
        resp = self.api("post", "/auth/login/code", {"phone": user.phone, "code": code, "client": "miniapp"})
        self.assertEqual(self._kind(resp), "EXTENDED")

    def test_invalid_client_rejected_and_admin_unchanged(self):
        """TC-INT-528 / AC-155-03（GROUP_C 自验证，GROUP_D 接管）：client 非法 400；管理员登录不受影响。"""
        user = self._user_with_password()
        for bad in ("ios", 1, None, ["miniapp"]):
            resp = self.api("post", "/auth/login/password",
                            {"identifier": user.phone, "password": "Passw0rd123", "client": bad})
            self.assert_error(resp, 400, "INVALID_VALUE")
        admin, _ = self.make_admin("adm1", "Admin12345")
        resp = self.api("post", "/admin/auth/login", {"username": "adm1", "password": "Admin12345",
                                                      "client": "miniapp"})
        self.assertEqual(AuthToken.objects.get(key_hash=_sha256(resp.data["token"])).session_kind, "IDLE")

    def test_extended_token_survives_31_minutes_but_not_7_days(self):
        """TC-INT-529 / AC-155-01、AC-155-02（GROUP_C 自验证，GROUP_D 接管）：7 天会话：31 分钟、6 天 23 小时有效，满 7 天失效。"""
        from apps.accounts.services import AccountService

        user = self._user_with_password()
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.phone, "password": "Passw0rd123", "client": "miniapp"})
        token = resp.data["token"]
        now = timezone.now()
        self.assertIsNotNone(AccountService.authenticate_token(token, now=now + timedelta(minutes=31)))
        row = AuthToken.objects.get(key_hash=_sha256(token))
        self.assertIsNotNone(AccountService.authenticate_token(
            token, now=row.created_at + timedelta(days=6, hours=23)))
        with self.assertRaises(AuthenticationFailed):
            AccountService.authenticate_token(token, now=row.created_at + timedelta(days=7, seconds=5))


class StyleAndReportTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.token = self.make_admin()

    def test_style_list_has_id_usage_and_delete_blocked_when_used(self):
        """TC-INT-530 / AC-162-04、AC-162-05（GROUP_C 自验证，GROUP_D 接管）：模板列表 id/usage_count；被引用禁删 409；内置不可寻址 404。"""
        created = self.assert_ok(self.api("post", "/admin/content/style-templates",
                                          {"name": "e2e_模板A", "tokens": {"font_size": 16}},
                                          token=self.token), 201).data
        self.assertEqual((created["usage_count"], created["builtin"]), (0, False))
        ContentPost.objects.create(title="x", style_key=created["key"], created_by_admin_id=self.admin.id)
        rows = self.api("get", "/admin/content/style-templates", token=self.token).data
        row = next(r for r in rows if r["key"] == created["key"])
        self.assertEqual((row["id"], row["usage_count"]), (created["id"], 1))
        self.assertTrue(all("id" not in r for r in rows if r["builtin"]))
        resp = self.api("delete", f"/admin/content/style-templates/{created['id']}", token=self.token)
        self.assert_error(resp, 409, "STYLE_IN_USE")
        self.assertEqual(resp.json()["details"], {"count": 1})
        ContentPost.objects.all().delete()
        self.assertEqual(self.api("delete", f"/admin/content/style-templates/{created['id']}",
                                  token=self.token).status_code, 204)
        self.assertFalse(StyleTemplate.objects.exists())
        self.assertEqual(self.api("delete", "/admin/content/style-templates/builtin:classic",
                                  token=self.token).status_code, 404)

    def test_report_detail_masks_expense_summary_unless_configured(self):
        """TC-INT-531 / AC-168-01（GROUP_C 自验证，GROUP_D 接管）：报表明细支出事由默认置空，配置开启后显示，不写回库。"""
        _, mtoken, _ = self.make_owner()
        detail = [{"direction": "EXPENSE", "amount": "1.00", "summary": "个人事由", "seq": 0},
                  {"direction": "INCOME", "amount": "2.00", "summary": "物业费", "seq": 0}]
        report = LedgerReport.objects.create(period_type="YEAR", year=2026, detail=detail)
        data = self.assert_ok(self.api("get", f"/ledger/reports/{report.id}", token=mtoken)).data
        self.assertIsNone(data["detail"][0]["summary"])
        self.assertEqual(data["detail"][1]["summary"], "物业费")
        report.refresh_from_db()
        self.assertEqual(report.detail[0]["summary"], "个人事由")
        from apps.core.config import SystemConfig

        SystemConfig.set("report.show_expense_reason", True, None)
        data = self.api("get", f"/ledger/reports/{report.id}", token=mtoken).data
        self.assertEqual(data["detail"][0]["summary"], "个人事由")


class IdentityLabelsTests(ApiTestBase):
    def test_labels_match_identity_view_and_ignore_order(self):
        """TC-INT-532 / AC-157-02（GROUP_C 自验证，GROUP_D 接管）：identity_labels 与 identity_view 一致。"""
        user, _ = self.make_user()
        a, b = self.make_unit(), self.make_unit()
        Membership.objects.create(user=user, unit=a, role="RESIDENT", source="APPLICATION", active_slot=1)
        Membership.objects.create(user=user, unit=b, role="OWNER", source="APPEAL", active_slot=1)
        self.make_seat(user, "VICE_CHAIR")
        self.assertEqual(CommitteeQuery.identity_labels(user.id), ["副主任"])  # C-34：职务直接显示，不并列"产权业主"
        self.assertEqual(Seat.objects.filter(user=user).count(), 1)
