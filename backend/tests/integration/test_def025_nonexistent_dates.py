"""DEF-025 回归（ocap_fix_defb_def024）：请求体日期/时间格式合法但不存在（如 2026-02-30）时不得 500，应 400 INVALID_VALUE。

覆盖五处：accounts PATCH /me/profile birthday、claims 报销 occurred_on、备用金 expected_settle_on、
polls 创建 deadline、resolutions HALF_MAJORITY vote_deadline。层级：integration（目录即分层标记）。
"""
from datetime import date, timedelta
from uuid import uuid4

from django.utils import timezone

from apps.core.models import Attachment
from tests.support import ApiTestBase


def _invoice(user) -> Attachment:
    return Attachment.objects.create(
        owner_type="MEMBER", owner_id=user.id, purpose="INVOICE",
        original_name="inv.pdf", content_type="application/pdf", size=1024,
        sha256="x" * 64, storage_path=f"tmp/{uuid4().hex}", status="TEMP",
    )


class Def025NonexistentDateTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.chair, self.ctoken, _ = self.make_owner()
        self.make_seat(self.chair, "CHAIR")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        self.expense_flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[approver])

    # ---- accounts
    def test_tc_int_730_profile_birthday_nonexistent_or_non_string_400(self):
        """TC-INT-730 / DEF-025：PATCH /me/profile birthday=2026-02-30 / 2026-13-01 / 数字 123 → 400 INVALID_VALUE「生日格式不正确」。"""
        for bad in ("2026-02-30", "2026-13-01", 123):
            with self.subTest(birthday=bad):
                body = self.assert_error(self.api("patch", "/me/profile", {"birthday": bad}, token=self.ctoken),
                                         400, "INVALID_VALUE")
                self.assertEqual(body["message"], "生日格式不正确")

    def test_tc_int_731_profile_birthday_valid_still_ok(self):
        """TC-INT-731 / DEF-025 正例：birthday=1990-05-06 → 200 且读回一致。"""
        self.assert_ok(self.api("patch", "/me/profile", {"birthday": "1990-05-06"}, token=self.ctoken))
        self.assertEqual(self.api("get", "/me/profile", token=self.ctoken).json()["birthday"], "1990-05-06")

    # ---- claims
    def _reimb(self, **kw):
        body = {"amount": "1.00", "reason": "r", "occurred_on": str(date.today()),
                "invoice_ids": [str(_invoice(self.chair).id)], "approval_flow_id": self.expense_flow.id}
        body.update(kw)
        return self.api("post", "/claims/reimbursements", body, token=self.ctoken)

    def test_tc_int_732_reimbursement_occurred_on_nonexistent_400(self):
        """TC-INT-732 / DEF-025：报销 occurred_on=2026-02-30 → 400 INVALID_VALUE「请填写费用发生日期」。"""
        body = self.assert_error(self._reimb(occurred_on="2026-02-30"), 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "请填写费用发生日期")

    def test_tc_int_733_reimbursement_valid_still_201(self):
        """TC-INT-733 / DEF-025 正例：occurred_on=今天 → 201。"""
        self.assert_ok(self._reimb(), 201)

    def _advance(self, **kw):
        body = {"amount": "500.00", "reason": "预借", "expected_usage": "差旅",
                "expected_settle_on": str(date.today() + timedelta(days=10)),
                "approval_flow_id": self.expense_flow.id}
        body.update(kw)
        return self.api("post", "/claims/advances", body, token=self.ctoken)

    def test_tc_int_734_advance_expected_settle_on_nonexistent_400(self):
        """TC-INT-734 / DEF-025：备用金 expected_settle_on=2026-02-30 → 400 INVALID_VALUE「预计核销日期须晚于今日」。"""
        body = self.assert_error(self._advance(expected_settle_on="2026-02-30"), 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "预计核销日期须晚于今日")

    def test_tc_int_735_advance_valid_still_201(self):
        """TC-INT-735 / DEF-025 正例：expected_settle_on=10 天后 → 201。"""
        self.assert_ok(self._advance(), 201)

    # ---- polls
    def _poll(self, deadline):
        return self.api("post", "/polls", {
            "title": "t", "kind": "SURVEY", "survey_scope": "OWNERS_ONLY", "deadline": deadline,
            "questions": [{"title": "q", "qtype": "TEXT"}]}, token=self.ctoken)

    def test_tc_int_736_poll_deadline_nonexistent_400(self):
        """TC-INT-736 / DEF-025：创建投票 deadline=2026-02-30T10:00 → 400 INVALID_VALUE「截止时间格式不正确」。"""
        body = self.assert_error(self._poll("2026-02-30T10:00"), 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "截止时间格式不正确")

    def test_tc_int_737_poll_valid_still_201(self):
        """TC-INT-737 / DEF-025 正例：deadline=2 天后 → 201。"""
        self.assert_ok(self._poll((timezone.now() + timedelta(days=2)).isoformat()), 201)

    # ---- resolutions
    def _resolution(self, vote_deadline):
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        return self.api("post", "/resolutions", {"title": "t", "content": "c", "approval_flow_id": flow.id,
                                                 "vote_deadline": vote_deadline}, token=self.ctoken)

    def test_tc_int_738_resolution_vote_deadline_nonexistent_400(self):
        """TC-INT-738 / DEF-025：HALF_MAJORITY vote_deadline=2026-02-30T10:00 → 400 INVALID_VALUE「半数以上参与者同意的决议须填写投票截止时间」。"""
        body = self.assert_error(self._resolution("2026-02-30T10:00"), 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "半数以上参与者同意的决议须填写投票截止时间")

    def test_tc_int_739_resolution_valid_still_created(self):
        """TC-INT-739 / DEF-025 正例：vote_deadline=2 天后 → 201。"""
        self.assert_ok(self._resolution((timezone.now() + timedelta(days=2)).isoformat()), 201)
