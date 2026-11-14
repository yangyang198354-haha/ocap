"""ocap_product_review MOD-075 / 画像 P6：迁移 residency 0002_closed_status 的正向与反向执行验证。

默认测试以 MIGRATION_MODULES 置空运行，迁移文件不被执行；本用例用子进程 + 临时 SQLite 文件库（tests/migration_settings.py）
真实执行 `manage.py migrate`：全量迁到最新 → 回退 residency 到 0001 → 再前进到 0002，并核对 CLOSED 行可写入与回退前后的数据保留。
不连接测试机或生产库（库文件在系统临时目录，测试结束删除）。
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

BACKEND = Path(__file__).resolve().parents[2]


class ResidencyMigration0002Tests(SimpleTestCase):
    def _manage(self, db: str, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "DJANGO_SETTINGS_MODULE": "tests.migration_settings", "OCAP_MIGRATION_DB": db,
               "DJANGO_ALLOW_EPHEMERAL_SECRET": "1"}
        return subprocess.run([sys.executable, "manage.py", *args], cwd=BACKEND, env=env, capture_output=True,
                              text=True, timeout=240)

    def _ok(self, db, *args) -> str:
        out = self._manage(db, *args)
        self.assertEqual(out.returncode, 0, f"manage.py {' '.join(args)} 失败：\n{out.stdout[-800:]}\n{out.stderr[-800:]}")
        return out.stdout

    def test_tc_int_497_migration_0002_forward_backward_forward(self):
        """TC-INT-497 / AC-155~164（REQ-FUNC-155 的 CLOSED 状态）、画像 P6：0002 正向、反向、再正向均成功；
        只改 choices（sqlmigrate 无 DDL 变更语句）；CLOSED 行可写入；回退不丢既有行。"""
        with tempfile.TemporaryDirectory(prefix="ocap-mig-") as tmp:
            db = str(Path(tmp) / "mig.sqlite3")
            self._ok(db, "migrate", "--noinput")
            listing = self._ok(db, "showmigrations", "residency")
            self.assertRegex(listing, r"\[X\] 0002_closed_status")
            # 写入数据：用户、专有部分、申诉（待审）
            seed = (
                "from django.utils import timezone\n"
                "from apps.accounts.models import User\n"
                "from apps.registry.models import RegistryUnit\n"
                "from apps.residency.models import Appeal, ResidentApplication\n"
                "u=User.objects.create(account_no='9900000001',phone='13900000001')\n"
                "x=RegistryUnit.objects.create(building='1',unit_no='1',floor='1',room='1')\n"
                "a=Appeal.objects.create(user=u,unit=x)\n"
                "r=ResidentApplication.objects.create(applicant=u,unit=x)\n"
                "Appeal.objects.filter(id=a.id).update(status='CLOSED',pending_slot=None)\n"
                "ResidentApplication.objects.filter(id=r.id).update(status='CLOSED',pending_slot=None)\n"
                "print('SEEDED', Appeal.objects.filter(status='CLOSED').count(), ResidentApplication.objects.filter(status='CLOSED').count())\n")
            self.assertIn("SEEDED 1 1", self._ok(db, "shell", "-c", seed))
            sql = self._ok(db, "sqlmigrate", "residency", "0002")
            self.assertNotRegex(sql.upper(), r"\b(DROP COLUMN|ADD COLUMN|CREATE TABLE|INSERT INTO|UPDATE )")
            back = self._ok(db, "migrate", "residency", "0001", "--noinput")
            self.assertIn("Unapplying residency.0002_closed_status", back)
            self.assertRegex(self._ok(db, "showmigrations", "residency"), r"\[ \] 0002_closed_status")
            # 回退只影响 choices，已有行（含 CLOSED）仍在、可读
            count = self._ok(db, "shell", "-c",
                             "from apps.residency.models import Appeal, ResidentApplication\n"
                             "print('ROWS', Appeal.objects.count(), ResidentApplication.objects.count())")
            self.assertIn("ROWS 1 1", count)
            fwd = self._ok(db, "migrate", "residency", "0002", "--noinput")
            self.assertIn("Applying residency.0002_closed_status", fwd)
            self.assertRegex(self._ok(db, "showmigrations", "residency"), r"\[X\] 0002_closed_status")
            # 漂移检查只针对 residency：全量检查会报出 content 应用既有的索引名/主键类型漂移（本批未改动 content 迁移，见 e2e 报告"观察项"）
            self.assertIn("No changes detected",
                          self._ok(db, "makemigrations", "residency", "--check", "--dry-run"))
