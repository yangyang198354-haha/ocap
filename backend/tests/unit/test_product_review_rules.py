"""ocap_product_review GROUP_D：后端单元用例（TC-UNIT-505 起）。

单模块、不经 HTTP；DB 仅用于需要模型的纯规则（Django TestCase + SQLite 内存库）。
"""
import ast
import re
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.accounts.directory import POSITION_RANK, ROLE_RANK, identity_view
from apps.accounts.models import User
from apps.accounts.views import _check_client, _session_kind
from apps.claims.views import _parse_amount as claim_parse_amount
from apps.committee.models import Seat
from apps.committee.services import CommitteeQuery
from apps.core import limits
from apps.core.audit import AUDIT_ACTIONS
from apps.core.config import (AMOUNT_MAX_CEILING, AMOUNT_MAX_DEFAULT, EDITABLE_KEYS, EDITABLE_VALIDATORS,
                              SystemConfig, validate_amount_max)
from apps.core.errors import ApiError
from apps.income.views import _parse_amount as income_parse_amount
from apps.income.views import _parse_rows
from apps.residency.models import Appeal, Membership, ResidentApplication
from apps.residency.services import ROLE_RANK as SERVICE_ROLE_RANK
from apps.residency.services import PendingRequestService
from apps.jobs import e2e_fixture
from apps.registry.models import RegistryUnit

ROOT = Path(__file__).resolve().parents[3]


class AmountMaxValidationTests(SimpleTestCase):
    def test_tc_unit_505_validate_amount_max_accepts_and_normalizes(self):
        """TC-UNIT-505 / AC-170-01、AC-170-04：合法值规范化为两位小数字符串。"""
        for raw, expected in ((500000, "500000.00"), ("500000", "500000.00"), ("0.01", "0.01"),
                              (" 12.5 ", "12.50"), (Decimal("3"), "3.00"), ("999999999999.99", "999999999999.99")):
            self.assertEqual(validate_amount_max(raw), expected, raw)

    def test_tc_unit_506_validate_amount_max_rejects_invalid(self):
        """TC-UNIT-506 / AC-170-04：0、负数、非数字、布尔、None、三位小数、超列范围、NaN 均拒绝（INVALID_VALUE）。"""
        for raw in (0, "0", -1, "-0.01", "abc", "", True, None, "1.234", "1000000000000.00", "NaN",
                    "Infinity", [], {}):
            with self.assertRaises(ApiError, msg=repr(raw)) as ctx:
                validate_amount_max(raw)
            self.assertEqual(ctx.exception.code, "INVALID_VALUE", repr(raw))

    def test_tc_unit_507_editable_keys_and_default(self):
        """TC-UNIT-507 / AC-170-02：claim.amount_max 可编辑且有校验器；默认 1,000,000.00；上限 999999999999.99。"""
        self.assertIn("claim.amount_max", EDITABLE_KEYS)
        self.assertIn("claim.amount_max", EDITABLE_VALIDATORS)
        self.assertEqual(AMOUNT_MAX_DEFAULT, Decimal("1000000.00"))
        self.assertEqual(AMOUNT_MAX_CEILING, Decimal("999999999999.99"))
        self.assertEqual(set(EDITABLE_KEYS), set(EDITABLE_VALIDATORS))

    def test_tc_unit_508_claim_parse_amount_with_explicit_limit(self):
        """TC-UNIT-508 / AC-170-01、AC-170-02：_parse_amount 带 limit：边界值通过、超 0.01 失败并带 details。"""
        limit = Decimal("500000.00")
        self.assertEqual(claim_parse_amount("500000.00", limit), Decimal("500000.00"))
        with self.assertRaises(ApiError) as ctx:
            claim_parse_amount("500000.01", limit)
        self.assertEqual(ctx.exception.details, {"max_amount": "500000.00"})
        self.assertIn("当前上限 500000.00 元", ctx.exception.message)
        with self.assertRaises(ApiError):
            claim_parse_amount("0.001", limit)
        with self.assertRaises(ApiError):
            claim_parse_amount("abc", limit)

    def test_tc_unit_509_income_parse_amount_and_rows_with_limit(self):
        """TC-UNIT-509 / AC-170-05：收入金额解析与按行解析遵循显式 limit。"""
        self.assertEqual(income_parse_amount("500.00", Decimal("500.00")), Decimal("500.00"))
        with self.assertRaises(ValueError) as ctx:
            income_parse_amount("500.01", Decimal("500.00"))
        self.assertIn("500.00", str(ctx.exception))
        rows = [["日期", "金额", "收入类别", "来源说明", "备注"], ["2026-01-01", "600", "", "", ""]]
        self.assertEqual(_parse_rows(rows, limit=Decimal("500"))["errors"][0]["reason"], "INVALID_FIELD")
        self.assertEqual(_parse_rows(rows, limit=Decimal("600"))["errors"], [])


class SessionKindTests(TestCase):
    def test_tc_unit_510_check_client_values(self):
        """TC-UNIT-510 / AC-155-01、AC-155-03：client 缺省 web；web/miniapp 合法；其余非法（含非字符串）。"""
        self.assertEqual(_check_client({}), "web")
        self.assertEqual(_check_client({"client": "web"}), "web")
        self.assertEqual(_check_client({"client": "miniapp"}), "miniapp")
        for bad in ("ios", "", "MINIAPP", 1, None, ["miniapp"], {}):
            with self.assertRaises(ApiError, msg=repr(bad)):
                _check_client({"client": bad})

    def test_tc_unit_511_session_kind_rules(self):
        """TC-UNIT-511 / AC-155-01~03：小程序默认 EXTENDED；Web 勾选记住我使用 REMEMBER，未勾选为 IDLE。"""
        self.assertEqual(_session_kind({"client": "miniapp"}), "EXTENDED")
        self.assertEqual(_session_kind({"remember_me": True}), "REMEMBER")
        self.assertEqual(_session_kind({"client": "web", "remember_me": True}), "REMEMBER")
        self.assertEqual(_session_kind({}), "IDLE")
        self.assertEqual(_session_kind({"client": "web"}), "IDLE")
        self.assertEqual(_session_kind({}, default="EXTENDED"), "EXTENDED")
        SystemConfig.set("session.miniapp_extended", False, None)
        self.assertEqual(_session_kind({"client": "miniapp"}), "IDLE")
        self.assertEqual(_session_kind({"client": "miniapp", "remember_me": True}), "EXTENDED")


class IdentityRulesTests(TestCase):
    def _user(self):
        return User.objects.create(account_no=f"6{User.objects.count():09d}", phone=f"137{User.objects.count():08d}")

    def _unit(self):
        return RegistryUnit.objects.create(building="1", unit_no=f"u{RegistryUnit.objects.count()}", floor="1", room="1")

    def test_tc_unit_512_identity_view_precedence_and_expired_seat(self):
        """TC-UNIT-512 / AC-157-01~03：职务 > 产权业主（HEAD/OWNER 同码同文案）> 同住人 > 游客；过期席位不计；同级取认证最早。"""
        user = self._user()
        a, b = self._unit(), self._unit()
        m_res = Membership.objects.create(user=user, unit=a, role="RESIDENT", source="APPLICATION", active_slot=1)
        m_head = Membership.objects.create(user=user, unit=b, role="HEAD", source="APPEAL", active_slot=1, head_slot=1)
        self.assertEqual(identity_view(memberships=[m_res], seats=[])["identity_label"], "同住人")
        self.assertEqual(identity_view(memberships=[m_res, m_head], seats=[])["identity_code"], "OWNER")
        self.assertEqual(identity_view(memberships=[], seats=[])["identity_label"], "游客")
        today = timezone.localdate()
        expired = Seat.objects.create(user=user, position="CHAIR", term_start=today - timedelta(days=60),
                                      term_end=today - timedelta(days=1), status="ACTIVE", active_slot=1)
        self.assertEqual(identity_view(memberships=[m_head], seats=[expired])["identity_code"], "OWNER")
        expired.term_end = today
        self.assertEqual(identity_view(memberships=[m_head], seats=[expired])["identity_label"], "业委会主任")

    def test_tc_unit_513_rank_tables_consistent(self):
        """TC-UNIT-513 / AC-157-04：目录与 residency 服务使用同一角色排序（管理端与本人汇总同源）。"""
        self.assertEqual(ROLE_RANK, SERVICE_ROLE_RANK)
        self.assertGreater(POSITION_RANK["CHAIR"], POSITION_RANK["VICE_CHAIR"])
        self.assertGreater(POSITION_RANK["MEMBER"], POSITION_RANK["REPRESENTATIVE"])

    def test_tc_unit_514_identity_labels_equal_identity_view(self):
        """TC-UNIT-514 / AC-157-02：identity_labels 与 identity_view 最高身份一致（多户取最高，不取第一条）。"""
        user = self._user()
        a, b = self._unit(), self._unit()
        Membership.objects.create(user=user, unit=a, role="RESIDENT", source="APPLICATION", active_slot=1)
        Membership.objects.create(user=user, unit=b, role="OWNER", source="CERTIFIED", active_slot=1)
        self.assertEqual(CommitteeQuery.identity_labels(user.id), ["产权业主"])
        self.assertEqual(CommitteeQuery.identity_labels(self._user().id), ["游客"])


class PendingRequestRuleTests(TestCase):
    def test_tc_unit_515_close_only_pending_and_release_slot(self):
        """TC-UNIT-515 / AC-164-01、AC-164-03、AC-164-04：只关闭 PENDING、释放唯一槽、不改驳回原因；无待处理项返回 0。"""
        user = User.objects.create(account_no="6100000001", phone="13710000001")
        unit = RegistryUnit.objects.create(building="1", unit_no="u1", floor="1", room="1")
        unit2 = RegistryUnit.objects.create(building="1", unit_no="u2", floor="1", room="1")
        app = ResidentApplication.objects.create(applicant=user, unit=unit)
        appeal = Appeal.objects.create(user=user, unit=unit)
        done = Appeal.objects.create(user=user, unit=unit2, status="REJECTED", pending_slot=None, reject_reason="旧")
        self.assertEqual(PendingRequestService.close_for_cancelled_user(user),
                         {"resident_applications": 1, "appeals": 1})
        for row in (app, appeal, done):
            row.refresh_from_db()
        self.assertEqual((app.status, appeal.status, done.status), ("CLOSED", "CLOSED", "REJECTED"))
        self.assertEqual((app.pending_slot, appeal.pending_slot, done.reject_reason), (None, None, "旧"))
        self.assertTrue(app.decided_at and appeal.decided_at)
        self.assertEqual(PendingRequestService.close_for_cancelled_user(user),
                         {"resident_applications": 0, "appeals": 0})
        # 唯一槽已释放：同一房屋可再次提交待审申请
        ResidentApplication.objects.create(applicant=user, unit=unit)

    def test_tc_unit_516_closed_status_registered_and_audit_actions(self):
        """TC-UNIT-516 / AC-164-01：CLOSED 是两个模型的合法状态；两个关闭审计动作已登记。"""
        for model in (Appeal, ResidentApplication):
            self.assertIn("CLOSED", dict(model.STATUSES))
        self.assertIn("RESIDENT_APPLICATION_CLOSED", AUDIT_ACTIONS)
        self.assertIn("APPEAL_CLOSED", AUDIT_ACTIONS)


class LimitsConstantTests(TestCase):
    def test_tc_unit_517_limits_constants_and_current_limits(self):
        """TC-UNIT-517 / AC-172-01、AC-173-01、AC-173-02、AC-170-02：规则限制常量与 current_limits 键/值。"""
        self.assertEqual((limits.POLL_OPTIONS_MIN, limits.POLL_OPTIONS_MAX), (2, 10))
        self.assertEqual((limits.INCOME_IMPORT_MAX_ROWS, limits.INCOME_MANUAL_MAX_RECORDS), (5000, 500))
        cur = limits.current_limits()
        self.assertEqual(set(cur), {"claim_amount_max", "poll_max_questions", "poll_options_min",
                                    "poll_options_max", "vote_min_window_minutes", "income_import_max_rows",
                                    "income_manual_max_records"})
        self.assertEqual((cur["claim_amount_max"], cur["poll_max_questions"], cur["vote_min_window_minutes"]),
                         ("1000000.00", 50, 60))
        SystemConfig.set("claim.amount_max", "12.5", None)
        self.assertEqual(limits.current_limits()["claim_amount_max"], "12.50")
        SystemConfig.set("claim.amount_max", "not-a-number", None)  # 损坏值回退默认
        self.assertEqual(limits.current_limits()["claim_amount_max"], "1000000.00")


class FixtureConstantsTests(SimpleTestCase):
    def test_tc_unit_518_fixture_prefixes_protect_real_data(self):
        """TC-UNIT-518 / 画像 P4-1：夹具前缀 e2e_ 与预留号段 1990000；两者不得为空或过短（双条件护栏的前提）。"""
        self.assertEqual(e2e_fixture.E2E_PREFIX, "e2e_")
        self.assertTrue(e2e_fixture.E2E_PHONE_PREFIX.startswith("199"))
        self.assertGreaterEqual(len(e2e_fixture.E2E_PHONE_PREFIX), 7)


class FrontendLabelFilesTests(SimpleTestCase):
    """前后端文案与键集合的静态对照（不运行前端）。"""

    @staticmethod
    def _exports(path: Path) -> dict[str, str]:
        src = path.read_text(encoding="utf-8")
        return {m.group(1): re.sub(r"\s+", "", m.group(2))
                for m in re.finditer(r"export const (\w+_LABELS)\s*=\s*(\{.*?\n\})", src, re.S)}

    def test_tc_unit_519_web_and_miniprogram_label_tables_identical(self):
        """TC-UNIT-519 / AC-167-01~03（ADR-092）：Web 与小程序 labels.js 的 *_LABELS 键与取值逐项相同。"""
        web = self._exports(ROOT / "frontend/src/shared/labels.js")
        mini = self._exports(ROOT / "miniprogram/utils/labels.js")
        self.assertTrue(web)
        self.assertEqual(web, mini)

    def test_tc_unit_520_labels_have_no_english_codes_as_values(self):
        """TC-UNIT-520 / AC-167-01、AC-167-03：中文映射表的取值不含 HEAD/OWNER/ACTIVE/true/false 等英文代码。"""
        src = (ROOT / "frontend/src/shared/labels.js").read_text(encoding="utf-8")
        for m in re.finditer(r":\s*'([^']*)'", src):
            value = m.group(1)
            if value:
                self.assertIsNone(re.fullmatch(r"[A-Za-z_]+", value), f"英文代码值：{value}")

    def test_tc_unit_521_python_module_syntax_of_new_backend_files(self):
        """TC-UNIT-521 / AC-178-01：新增后端模块可解析，且迁移 0002 为手写（无 "Generated by Django"）。"""
        for rel in ("backend/apps/core/limits.py", "backend/apps/residency/housing.py",
                    "backend/apps/jobs/e2e_fixture.py", "backend/apps/residency/migrations/0002_closed_status.py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            ast.parse(text)
        mig = (ROOT / "backend/apps/residency/migrations/0002_closed_status.py").read_text(encoding="utf-8")
        self.assertNotIn("Generated by Django", mig)
        self.assertIn("手写", mig)
