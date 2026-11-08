"""PHASE_07 单元测试：核心工具与通用规则。"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.services import validate_password
from apps.committee.services import add_months
from apps.core.errors import ApiError, RateLimited
from apps.core.masking import mask_email, mask_phone
from apps.core.money import money
from apps.core.ratelimit import RateLimiter


class MoneyTests(TestCase):
    def test_none_is_zero(self):
        self.assertEqual(money(None), "0.00")

    def test_two_decimals_half_up(self):
        self.assertEqual(money(Decimal("1.005")), "1.01")
        self.assertEqual(money("300.5"), "300.50")
        self.assertEqual(money(Decimal("0.004")), "0.00")

    def test_negative_keeps_sign(self):
        self.assertEqual(money(Decimal("-12.345")), "-12.35")


class MaskingTests(TestCase):
    def test_phone_masked(self):
        self.assertEqual(mask_phone("13800138000"), "138****8000")
        self.assertEqual(mask_phone("bad"), "****")

    def test_email_masked(self):
        self.assertEqual(mask_email("alice@example.com"), "a***@example.com")
        self.assertEqual(mask_email("nope"), "****")


class PasswordRuleTests(TestCase):
    def test_reject_short(self):
        with self.assertRaises(ApiError) as ctx:
            validate_password("a1")
        self.assertEqual(ctx.exception.code, "PASSWORD_RULE_VIOLATION")

    def test_reject_digits_only(self):
        with self.assertRaises(ApiError):
            validate_password("12345678")

    def test_reject_weak(self):
        with self.assertRaises(ApiError):
            validate_password("password1")

    def test_accept_strong(self):
        validate_password("Ocap2026pass")


class AddMonthsTests(TestCase):
    def test_month_end_clamped(self):
        self.assertEqual(add_months(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(add_months(date(2023, 1, 31), 1), date(2023, 2, 28))
        self.assertEqual(add_months(date(2024, 12, 31), 2), date(2025, 2, 28))

    def test_year_rollover(self):
        self.assertEqual(add_months(date(2026, 11, 7), 12), date(2027, 11, 7))


class RateLimiterTests(TestCase):
    def test_hit_limit_and_deny(self):
        key = "unit:rate:1"
        self.assertTrue(RateLimiter.hit(key, limit=2, window_seconds=60).allowed)
        self.assertTrue(RateLimiter.hit(key, limit=2, window_seconds=60).allowed)
        decision = RateLimiter.hit(key, limit=2, window_seconds=60)
        self.assertFalse(decision.allowed)
        self.assertGreaterEqual(decision.retry_after, 1)

    def test_register_failure_locks(self):
        key = "unit:lock:1"
        for _ in range(2):
            RateLimiter.register_failure(key, limit=2, window_seconds=600, lock_seconds=600)
        locked = RateLimiter.is_locked(key)
        self.assertFalse(locked.allowed)
        RateLimiter.reset(key)
        self.assertTrue(RateLimiter.is_locked(key).allowed)

    def test_rate_limited_error_shape(self):
        err = RateLimited(30)
        self.assertEqual(err.code, "CODE_RATE_LIMITED")
        self.assertEqual(err.status_code, 429)
        self.assertEqual(err.details["retry_after"], 30)
