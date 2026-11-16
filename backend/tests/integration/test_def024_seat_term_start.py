"""DEF-024 回归（ocap_fix_defb_def024）：POST /admin/committee/seats 的 term_start 为不存在日期时不得 500。

关联 US-205 / AC-205-01（补录授予席位）。层级：integration（目录即分层标记）。
"""
from django.utils import timezone

from apps.committee.models import CommitteeConfig, Seat
from tests.support import ApiTestBase


class SeatTermStartValidationTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        _, self.admin_token = self.make_admin()
        cfg = CommitteeConfig.load()  # 名额上限置为可授予（同 test_owner_auth_v2_seats.SeatBase）
        cfg.cap_member, cfg.cap_chair, cfg.cap_vice, cfg.cap_rep = 5, 2, 2, 5
        cfg.term_months_member = cfg.term_months_chair = cfg.term_months_vice = cfg.term_months_rep = 36
        cfg.save()

    def _post(self, user, term_start):
        return self.api("post", "/admin/committee/seats",
                        {"user_id": user.id, "position": "MEMBER", "term_start": term_start},
                        token=self.admin_token)

    def test_tc_int_720_nonexistent_or_malformed_term_start_returns_400(self):
        """TC-INT-720 / DEF-024、AC-205-01：2026-02-30、2026-13-01、abc → 400 INVALID_VALUE「term_start 格式不正确」，不产生席位。"""
        user, _, _ = self.make_owner()
        for bad in ("2026-02-30", "2026-13-01", "abc"):
            with self.subTest(term_start=bad):
                body = self.assert_error(self._post(user, bad), 400, "INVALID_VALUE")
                self.assertEqual(body["message"], "term_start 格式不正确")
        self.assertFalse(Seat.objects.filter(user=user).exists())

    def test_tc_int_721_valid_term_start_still_created(self):
        """TC-INT-721 / AC-205-01：合法日期 → 201，席位 term_start 为所传日期（正例，防止校验过严）。"""
        user, _, _ = self.make_owner()
        start = timezone.localdate()
        resp = self._post(user, str(start))
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Seat.objects.get(user=user).term_start, start)
