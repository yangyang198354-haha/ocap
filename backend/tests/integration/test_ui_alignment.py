"""REQ-FUNC-277/279/284/286：身份全称、公开决议排序、房屋关系专有部分过滤、申诉头像。"""
import importlib
from datetime import timedelta
from uuid import uuid4

from django.apps import apps as django_apps
from django.utils import timezone

from apps.income.models import IncomeSheet
from apps.registry.models import RegistryUnit
from apps.residency.models import Appeal, Membership
from apps.resolutions.models import Resolution
from tests.support import ApiTestBase


class UiAlignmentTests(ApiTestBase):
    def make_registry_unit(self, building, room):
        return RegistryUnit.objects.create(building=building, unit_no="1单元", floor="1", room=room)

    def add_membership(self, user, unit, role="HEAD"):
        Membership.objects.create(user=user, unit=unit, role=role, source="CERTIFIED", active_slot=1)

    def test_public_resolutions_pending_first(self):
        """REQ-FUNC-279：公开决议进行中优先，其余按发起时间倒序。"""
        user, token = self.make_user()
        pending = Resolution.objects.create(
            title="进行中", content="x", initiator=user, initiator_labels=[],
            approval_mode="HALF_MAJORITY", status="PENDING",
            vote_deadline=timezone.now() + timedelta(days=1),
        )
        Resolution.objects.create(title="已结束", content="x", initiator=user, initiator_labels=[],
                                  approval_mode="DESIGNATED", status="APPROVED")
        Resolution.objects.filter(pk=pending.pk).update(created_at=timezone.now() - timedelta(days=3))

        resp = self.api("get", "/resolutions", {"scope": "public"}, token=token)
        self.assert_ok(resp)
        self.assertEqual([row["title"] for row in resp.data["results"]], ["进行中", "已结束"])

    def test_membership_unit_keyword_matches_specific_part_and_room(self):
        """REQ-FUNC-284：专有部分标识/户号包含匹配，且与身份条件取交集。"""
        _, admin_token = self.make_admin()
        unit_a = self.make_registry_unit("1栋", "101")
        unit_b = self.make_registry_unit("2栋", "202")
        owner, _ = self.make_user()
        resident, _ = self.make_user()
        self.add_membership(owner, unit_a, "OWNER")
        self.add_membership(resident, unit_b, "RESIDENT")

        resp = self.api("get", "/admin/memberships", {"unit_keyword": "101"}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual([row["unit_id"] for row in resp.data["results"]], [unit_a.id])

        resp = self.api("get", "/admin/memberships", {"unit_keyword": "2栋1单元1层202"},
                        token=admin_token)
        self.assert_ok(resp)
        self.assertEqual([row["unit_id"] for row in resp.data["results"]], [unit_b.id])

        resp = self.api("get", "/admin/memberships",
                        {"unit_keyword": "101", "role": "RESIDENT"}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["results"], [])

    def test_appeal_list_returns_applicant_avatar_url(self):
        """REQ-FUNC-286：申诉列表返回申请人头像地址，手机号仍脱敏。"""
        _, admin_token = self.make_admin()
        user, _ = self.make_user()
        user.avatar_attachment_id = uuid4()
        user.save(update_fields=["avatar_attachment_id"])
        unit = self.make_registry_unit("3栋", "303")
        Appeal.objects.create(user=user, unit=unit, owner_name="")

        resp = self.api("get", "/admin/appeals", token=admin_token)
        self.assert_ok(resp)
        row = resp.data["results"][0]
        self.assertEqual(row["applicant"]["avatar_url"],
                         f"/api/v1/attachments/{user.avatar_attachment_id}/download")
        self.assertEqual(row["applicant"]["has_phone"], True)
        self.assertNotEqual(row["applicant"]["phone"], user.phone)

    def test_identity_label_migrations_rewrite_text_and_are_idempotent(self):
        """REQ-FUNC-277 / D-05：历史身份快照改为全称，重复执行不再变化。"""
        user, _ = self.make_user()
        resolution = Resolution.objects.create(
            title="历史决议", content="x", initiator=user,
            initiator_labels=["主任", "副主任", "委员", "业主代表"],
            approval_mode="DESIGNATED", status="APPROVED",
        )
        sheet = IncomeSheet.objects.create(submitted_by=user, creator_labels="主任,委员")

        resolutions_migration = importlib.import_module(
            "apps.resolutions.migrations.0003_identity_labels_full")
        income_migration = importlib.import_module(
            "apps.income.migrations.0005_identity_labels_full")
        for _ in range(2):
            resolutions_migration.forwards(django_apps, None)
            income_migration.forwards(django_apps, None)

        resolution.refresh_from_db()
        sheet.refresh_from_db()
        self.assertEqual(resolution.initiator_labels,
                         ["业委会主任", "业委会副主任", "业委会委员", "业主代表"])
        self.assertEqual(sheet.creator_labels, "业委会主任,业委会委员")
