"""PHASE_07 单元测试：GROUP_C 返工（CR-018/CR-024）的规则。"""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from django.test import TestCase

from apps.ledger.models import LedgerReport
from apps.ledger.services import LedgerService

BACKEND = Path(__file__).resolve().parents[2]


class GenerateDueIdempotencyTests(TestCase):
    """AC-061-01/02：generate_due 生成上一季度与上一年度，幂等；账目变化后只重算过期报表。"""

    TODAY = date(2026, 11, 8)

    def test_generates_prev_quarter_and_prev_year_once(self):
        first = LedgerService.generate_due(self.TODAY)
        self.assertEqual({(r.period_type, r.year, r.quarter) for r in first},
                         {("QUARTER", 2026, 3), ("YEAR", 2025, None)})
        second = LedgerService.generate_due(self.TODAY)
        self.assertEqual(second, [])
        self.assertEqual(LedgerReport.objects.count(), 2)

    def test_first_quarter_uses_previous_year_q4(self):
        reports = LedgerService.generate_due(date(2026, 2, 1))
        self.assertEqual({(r.period_type, r.year, r.quarter) for r in reports},
                         {("QUARTER", 2025, 4), ("YEAR", 2025, None)})

    def test_stale_report_regenerated_only_for_affected_period(self):
        LedgerService.generate_due(self.TODAY)
        LedgerService.post(direction="EXPENSE", amount=50, occurred_on=date(2026, 8, 1),
                           entry_type="REIMBURSEMENT", source_type="claim", source_id=9001)
        regenerated = LedgerService.generate_due(self.TODAY)
        self.assertEqual([(r.period_type, r.year, r.quarter) for r in regenerated],
                         [("QUARTER", 2026, 3)])
        self.assertEqual(str(regenerated[0].total_expense), "50.00")
        self.assertEqual(LedgerReport.objects.count(), 2)


class SecretKeyStartupTests(TestCase):
    """CR-024：缺少 DJANGO_SECRET_KEY 时（非 DEBUG、未显式允许临时密钥）拒绝启动。"""

    def _run(self, **extra):
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("DJANGO_") and k != "DJANGO_SETTINGS_MODULE"}
        env.update(extra)
        code = ("import config.settings as s; "
                "print('OK', len(s.SECRET_KEY) > 0, ','.join(s.ALLOWED_HOSTS))")
        return subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env=env,
                              capture_output=True, text=True, timeout=60)

    def test_missing_secret_key_refuses_to_start(self):
        proc = self._run()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ImproperlyConfigured", proc.stderr)
        self.assertIn("DJANGO_SECRET_KEY", proc.stderr)

    def test_empty_secret_key_refuses_to_start(self):
        proc = self._run(DJANGO_SECRET_KEY="")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ImproperlyConfigured", proc.stderr)

    def test_provided_secret_key_starts_with_safe_default_hosts(self):
        proc = self._run(DJANGO_SECRET_KEY="unit-test-secret-value")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "OK True localhost,127.0.0.1")

    def test_debug_allows_ephemeral_key(self):
        proc = self._run(DJANGO_DEBUG="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("OK True"))
