"""PHASE_07 单元测试：领域规则（金额解析、导入、投票、决议、席位）。"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.committee.models import Seat
from apps.committee.services import CommitteeQuery
from apps.claims.views import _parse_amount as parse_claim_amount
from apps.core.errors import ApiError
from apps.income.views import _parse_rows
from apps.polls.models import Poll, PollAnswer, PollResponse, Question
from apps.polls.services import PollService
from apps.polls.views import _validate_questions
from apps.registry.models import RegistryUnit
from apps.resolutions.models import Resolution, Vote
from apps.resolutions.services import ResolutionService
from apps.residency.models import Membership
from apps.residency.services import MembershipService

from tests.support import next_account_no, next_phone


def make_user():
    from apps.accounts.models import User

    return User.objects.create(account_no=next_account_no(), phone=next_phone())


class ClaimAmountRuleTests(TestCase):
    def test_accept_two_decimals(self):
        self.assertEqual(parse_claim_amount("300.50"), Decimal("300.50"))

    def test_reject_three_decimals(self):
        with self.assertRaises(ApiError) as ctx:
            parse_claim_amount("300.555")
        self.assertEqual(ctx.exception.code, "INVALID_VALUE")

    def test_reject_zero_and_overflow(self):
        with self.assertRaises(ApiError):
            parse_claim_amount("0")
        with self.assertRaises(ApiError):
            parse_claim_amount("1000000.01")

    def test_reject_non_numeric(self):
        with self.assertRaises(ApiError):
            parse_claim_amount("abc")


class IncomeParseRuleTests(TestCase):
    HEADER = ["日期", "金额", "收入类别", "来源说明", "备注"]

    def test_parse_ok_with_comma_amount(self):
        parsed = _parse_rows([self.HEADER, ["2026-01-05", "1,000.50", "物业费", "1月", ""]])
        self.assertEqual(parsed["total"], 1)
        self.assertEqual(parsed["records"][0]["amount"], Decimal("1000.50"))

    def test_missing_column(self):
        with self.assertRaises(ApiError) as ctx:
            _parse_rows([["日期", "金额", "收入类别"], ["2026-01-05", "10.00", "物业费"]])
        self.assertEqual(ctx.exception.code, "IMPORT_COLUMNS_MISSING")

    def test_row_error_ratio_over_2_percent(self):
        rows = [self.HEADER]
        for i in range(40):
            rows.append(["2026-01-05", "10.00", "物业费", f"项目{i}", ""])
        rows += [["bad-date", "10.00", "物业费", "x", ""], ["2026-01-05", "-1", "物业费", "y", ""],
                 ["2026-01-05", "1.001", "物业费", "z", ""]]
        with self.assertRaises(ApiError) as ctx:
            _parse_rows(rows)
        self.assertEqual(ctx.exception.code, "IMPORT_ROW_ERRORS")

    def test_row_error_ratio_within_2_percent(self):
        rows = [self.HEADER]
        for i in range(60):
            rows.append(["2026-01-05", "10.00", "物业费", f"项目{i}", ""])
        rows.append(["bad-date", "10.00", "物业费", "x", ""])
        parsed = _parse_rows(rows)
        self.assertEqual(parsed["total"], 61)
        self.assertEqual(len(parsed["errors"]), 1)


class PollQuestionRuleTests(TestCase):
    def test_accept_valid(self):
        _validate_questions([{"title": "是否同意", "qtype": "SINGLE",
                              "options": ["同意", "反对"]}])

    def test_reject_single_option(self):
        with self.assertRaises(ApiError):
            _validate_questions([{"title": "q", "qtype": "SINGLE", "options": ["A"]}])

    def test_reject_too_many_options(self):
        with self.assertRaises(ApiError):
            _validate_questions([{"title": "q", "qtype": "SINGLE",
                                  "options": [f"o{i}" for i in range(11)]}])


class PollResultRuleTests(TestCase):
    def test_percentage_uses_responses(self):
        poll = Poll.objects.create(creator=make_user(), title="投票",
                                   deadline=timezone.now() + timedelta(hours=1))
        question = Question.objects.create(poll=poll, title="是否同意", qtype="SINGLE",
                                           options=["同意", "反对"])
        for choice in ("同意", "反对", "同意"):
            user = make_user()
            response = PollResponse.objects.create(poll=poll, user=user)
            PollAnswer.objects.create(response=response, question=question, value=choice)
        result = PollService.results(poll)
        self.assertEqual(result["responses"], 3)
        options = {o["value"]: o for o in result["questions"][0]["options"]}
        self.assertEqual(options["同意"]["count"], 2)
        self.assertEqual(options["同意"]["percentage"], 66.7)
        self.assertEqual(options["反对"]["percentage"], 33.3)


class ResolutionJudgeRuleTests(TestCase):
    def setUp(self):
        self.voters = [make_user() for _ in range(3)]
        today = timezone.localdate()
        for user in self.voters:
            Seat.objects.create(user=user, position="MEMBER", term_start=today,
                                term_end=today + timedelta(days=365), status="ACTIVE", active_slot=1)

    def _resolution(self, choices):
        resolution = Resolution.objects.create(
            initiator=self.voters[0], title="测试决议", content="内容",
            approval_mode="HALF_MAJORITY", vote_deadline=timezone.now() - timedelta(minutes=1),
        )
        for user, choice in zip(self.voters, choices):
            Vote.objects.create(resolution=resolution, revision=1, voter=user, choice=choice)
        return resolution

    def test_half_majority_passed(self):
        resolution = self._resolution(["AGREE", "AGREE", "DISAGREE"])
        self.assertEqual(ResolutionService.judge_if_due(resolution.id), "PASSED")
        resolution.refresh_from_db()
        self.assertEqual(resolution.status, "APPROVED")
        self.assertEqual(resolution.result["denominator"], 3)

    def test_half_majority_failed(self):
        resolution = self._resolution(["AGREE", "DISAGREE", "ABSTAIN"])
        self.assertEqual(ResolutionService.judge_if_due(resolution.id), "FAILED")
        resolution.refresh_from_db()
        self.assertEqual(resolution.status, "REJECTED")

    def test_judge_not_due(self):
        resolution = Resolution.objects.create(
            initiator=self.voters[0], title="未到期", content="内容",
            approval_mode="HALF_MAJORITY", vote_deadline=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(ResolutionService.judge_if_due(resolution.id), "NOT_DUE")

    def test_judge_twice_idempotent(self):
        resolution = self._resolution(["AGREE", "AGREE", "AGREE"])
        ResolutionService.judge_if_due(resolution.id)
        self.assertEqual(ResolutionService.judge_if_due(resolution.id), "ALREADY_DECIDED")


class CommitteeRuleTests(TestCase):
    def test_member_vs_representative(self):
        member, rep = make_user(), make_user()
        today = timezone.localdate()
        Seat.objects.create(user=member, position="MEMBER", term_start=today,
                            term_end=today + timedelta(days=30), status="ACTIVE", active_slot=1)
        Seat.objects.create(user=rep, position="REPRESENTATIVE", term_start=today,
                            term_end=today + timedelta(days=30), status="ACTIVE", active_slot=1)
        self.assertTrue(CommitteeQuery.is_member(member.id))
        self.assertFalse(CommitteeQuery.is_member(rep.id))
        self.assertTrue(CommitteeQuery.is_representative(rep.id))
        self.assertEqual(CommitteeQuery.denominator_for_half_majority("ACTIVE"), 1)


class HeadPromotionRuleTests(TestCase):
    def test_promote_owner_when_head_vacant(self):
        unit = RegistryUnit.objects.create(building="1", unit_no="1", floor="1", room="101",
                                           specific_part=f"1-1-101-{next_account_no()}")
        owner = make_user()
        Membership.objects.create(user=owner, unit=unit, role="OWNER", source="CERTIFIED", active_slot=1)
        promoted = MembershipService.promote_head_if_vacant(unit.id)
        self.assertEqual(promoted, owner.id)
        self.assertTrue(Membership.objects.filter(user=owner, role="HEAD", head_slot=1).exists())

    def test_no_owner_no_promotion(self):
        unit = RegistryUnit.objects.create(building="1", unit_no="2", floor="1", room="102",
                                           specific_part=f"1-1-102-{next_account_no()}")
        self.assertIsNone(MembershipService.promote_head_if_vacant(unit.id))
