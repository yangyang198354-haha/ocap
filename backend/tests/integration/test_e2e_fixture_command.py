"""MOD-081：e2e_fixture 命令（GROUP_C 自验证；GROUP_D 可扩充）。"""
import json
import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import AdminAccount, User
from apps.approval.models import ApprovalFlow
from apps.claims.models import Claim
from apps.committee.models import Seat
from apps.ledger.models import LedgerEntry
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase

ENV = {"OCAP_E2E_FIXTURE": "1", "OCAP_E2E_PASSWORD": "Fixture12345"}


def run(*args, env=None):
    out = StringIO()
    with mock.patch.dict(os.environ, env if env is not None else ENV, clear=False):
        call_command("e2e_fixture", *args, stdout=out)
    return json.loads(out.getvalue())


class E2EFixtureTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        for i in range(5):
            RegistryUnit.objects.create(building=f"{i + 1}栋", unit_no="1单元", floor="1", room=f"10{i}",
                                        unit_type="RESIDENCE")
        # 非住宅与已有关系的房屋不得被选中
        self.shop = RegistryUnit.objects.create(building="9栋", room="S1", unit_type="SHOP")
        self.busy = RegistryUnit.objects.first()
        self.real_user, _ = self.make_user()
        Membership.objects.create(user=self.real_user, unit=self.busy, role="HEAD", source="REGISTRY",
                                  active_slot=1, head_slot=1)
        owner = RegistryOwner.objects.create(unit=self.busy, name="真实业主")
        RegistryPhone.objects.create(unit=self.busy, owner=owner, phone="13800000000")
        self.registry_before = (RegistryUnit.objects.count(), RegistryOwner.objects.count(),
                                RegistryPhone.objects.count())

    def registry_now(self):
        return (RegistryUnit.objects.count(), RegistryOwner.objects.count(), RegistryPhone.objects.count())

    def test_requires_gate_and_password(self):
        """TC-INT-533 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：缺 OCAP_E2E_FIXTURE 门闩/密码或参数越界时拒绝。"""
        with self.assertRaises(CommandError):
            run("status", env={"OCAP_E2E_FIXTURE": "0"})
        with self.assertRaises(CommandError):
            run("setup", env={"OCAP_E2E_FIXTURE": "1", "OCAP_E2E_PASSWORD": ""})
        with self.assertRaises(CommandError):
            run("setup", "--units", "2")
        with self.assertRaises(CommandError):
            run("setup", "--bulk-users", "61")

    def test_setup_is_idempotent_and_never_touches_registry(self):
        """TC-INT-534 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：setup 幂等，且不改 RegistryUnit/Owner/Phone 行数。"""
        report = run("setup", "--bulk-users", "3", "--bulk-resolutions", "2")
        self.assertEqual(self.registry_now(), self.registry_before)
        unit_ids = {u["unit_id"] for u in report["units"]}
        self.assertNotIn(self.busy.id, unit_ids)
        self.assertNotIn(self.shop.id, unit_ids)
        self.assertEqual(len(unit_ids), 3)
        self.assertEqual(User.objects.filter(nickname__startswith="e2e_").count(), 10 + 3)
        self.assertTrue(all("password" not in json.dumps(a) for a in report["accounts"]))
        self.assertTrue(all("****" in a["phone_masked"] for a in report["accounts"] if a["kind"] == "member"))
        self.assertEqual(Seat.objects.filter(status="ACTIVE").count(), 3)
        self.assertEqual(Resolution.objects.filter(title__startswith="e2e_").count(), 2)
        self.assertEqual(ApprovalFlow.objects.filter(name__startswith="e2e_").count(), 2)
        again = run("setup", "--bulk-users", "3", "--bulk-resolutions", "2")
        self.assertEqual([u["unit_id"] for u in again["units"]], [u["unit_id"] for u in report["units"]])
        self.assertEqual(User.objects.filter(nickname__startswith="e2e_").count(), 13)
        self.assertEqual(Membership.objects.filter(user__nickname__startswith="e2e_").count(), 9)
        self.assertEqual(AdminAccount.objects.filter(username="e2e_admin").count(), 1)
        self.assertEqual(run("status")["registry_counts"], report["registry_counts"])

    def test_cleanup_dry_run_then_execute_leaves_nothing(self):
        """TC-INT-535 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：cleanup 先 dry-run 后 --execute，清理后 e2e 计数全 0、清册不变、真实用户保留。"""
        run("setup", "--bulk-users", "2", "--bulk-resolutions", "1", "--units", "4")
        member = User.objects.get(nickname="e2e_member")
        Claim.objects.create(type="REIMBURSEMENT", submitter=member, amount=1, reason="x")
        dry = run("cleanup")
        self.assertFalse(dry["executed"])
        self.assertEqual(User.objects.filter(nickname__startswith="e2e_").count(), 12)
        result = run("cleanup", "--execute")
        self.assertTrue(result["executed"])
        self.assertEqual(self.registry_now(), self.registry_before)
        left = run("status")
        self.assertTrue(all(v == 0 for v in left["e2e"].values()), left)
        self.assertEqual(left["claim_amount_max"], "1000000.00")
        self.assertEqual(AdminAccount.objects.filter(username__startswith="e2e_").count(), 0)
        self.assertTrue(User.objects.filter(id=self.real_user.id).exists())
        self.assertTrue(Membership.objects.filter(user=self.real_user).exists())
        run("cleanup", "--execute")  # 幂等

    def test_ledger_entries_block_cleanup_with_exit_code_2(self):
        """TC-INT-536 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：e2e 数据产生账本分录时 cleanup 退出码 2 且不删除任何数据。"""
        run("setup")
        member = User.objects.get(nickname="e2e_member")
        claim = Claim.objects.create(type="REIMBURSEMENT", submitter=member, amount=1, reason="x")
        LedgerEntry.objects.create(direction="EXPENSE", amount=1, occurred_on="2026-01-01",
                                   entry_type="REIMBURSEMENT", source_type="claim", source_id=claim.id)
        with self.assertRaises(CommandError) as ctx:
            run("cleanup", "--execute")
        self.assertEqual(ctx.exception.returncode, 2)
        self.assertTrue(User.objects.filter(nickname="e2e_member").exists())

    def test_dual_condition_guard(self):
        """TC-INT-537 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：双条件护栏：昵称与号段不一致的用户不被删、占用号段时 setup 拒绝。"""
        User.objects.create(account_no="7000000001", phone="13700000001", nickname="e2e_stray")
        with self.assertRaises(CommandError):
            run("cleanup", "--execute")
        self.assertTrue(User.objects.filter(nickname="e2e_stray").exists())
        User.objects.filter(nickname="e2e_stray").delete()
        User.objects.create(account_no="7000000002", phone="19900000099", nickname="real_person")
        with self.assertRaises(CommandError):
            run("setup")

    def test_not_enough_free_units(self):
        """TC-INT-538 / 画像 P4-1、Q-PR-05（MOD-081，GROUP_C 自验证，GROUP_D 接管）：可选房屋不足时 setup 拒绝且不创建任何数据。"""
        RegistryUnit.objects.filter(unit_type="RESIDENCE").exclude(id=self.busy.id).first().delete()
        RegistryUnit.objects.filter(unit_type="RESIDENCE").exclude(id=self.busy.id).first().delete()
        with self.assertRaises(CommandError):
            run("setup")
        self.assertFalse(User.objects.filter(nickname__startswith="e2e_").exists())
