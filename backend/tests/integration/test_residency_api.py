"""PHASE_08 集成测试：清册、认证、申诉、同住人、席位。"""
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.committee.models import Seat
from apps.residency.models import Membership
from tests.support import ApiTestBase, next_phone


class RegistryAndCertificationTests(ApiTestBase):
    def test_unit_options_paged_by_level(self):
        unit = self.make_unit()
        user, token = self.make_user()
        resp = self.api("get", "/units/options?building=1", token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["level"], "unit_no")
        self.assertTrue(resp.data["options"])
        resp = self.api("get", f"/units/options?building=1&unit_no={unit.unit_no}&floor=1",
                        token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["level"], "room")

    def test_admin_registry_import_dry_run_and_commit(self):
        _, admin_token = self.make_admin()
        content = "楼栋,单元,楼层,户号,手机号\n2,1,3,301,13800000001\n2,1,3,302,13800000002\n"
        file = SimpleUploadedFile("registry.csv", content.encode("utf-8-sig"), content_type="text/csv")
        resp = self.upload("/admin/registry/import?dry_run=1", {"file": file}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["imported"], 0)
        file = SimpleUploadedFile("registry.csv", content.encode("utf-8-sig"), content_type="text/csv")
        resp = self.upload("/admin/registry/import", {"file": file}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["imported"], 2)

    def test_admin_unit_phones_then_certify_as_head(self):
        user, token = self.make_user()
        unit = self.make_unit()
        _, admin_token = self.make_admin()
        resp = self.api("put", f"/admin/registry/units/{unit.id}/phones",
                        {"phones": [user.phone]}, token=admin_token)
        self.assert_ok(resp)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["role"], "HEAD")

    def test_certification_phone_mismatch_422(self):
        user, token = self.make_user()
        unit = self.make_unit(phones=[next_phone()])
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        body = self.assert_error(resp, 422, "PHONE_NOT_IN_REGISTRY")
        self.assertTrue(body["details"]["appeal_available"])

    def test_second_owner_becomes_owner_and_duplicate_rejected(self):
        unit = self.make_unit(phones=[next_phone(), next_phone()])
        first, first_token = self.make_user(phone=unit.phones.all()[0].phone)
        second, second_token = self.make_user(phone=unit.phones.all()[1].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=first_token), 201)
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=second_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["role"], "OWNER")
        resp = self.api("post", "/certifications", {"unit_id": unit.id}, token=second_token)
        self.assert_error(resp, 409, "ALREADY_CERTIFIED")

    def test_unit_not_found(self):
        _, token = self.make_user()
        resp = self.api("post", "/certifications", {"unit_id": 999999}, token=token)
        self.assert_error(resp, 404, "NOT_FOUND")


class AppealTests(ApiTestBase):
    def test_appeal_requires_proof_and_admin_approve_makes_owner(self):
        user, token = self.make_user()
        unit = self.make_unit(phones=[next_phone()])
        resp = self.api("post", "/appeals", {"unit_id": unit.id}, token=token)
        self.assert_error(resp, 400, "PROOF_REQUIRED")
        proof = SimpleUploadedFile("proof.png", b"\x89PNG\r\n\x1a\n" + b"1" * 32,
                                   content_type="image/png")
        uploaded = self.upload("/attachments", {"file": proof, "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(uploaded, 201)
        resp = self.api("post", "/appeals", {"unit_id": unit.id,
                                             "proof_ids": [uploaded.data["id"]]}, token=token)
        self.assert_ok(resp, 201)
        appeal_id = resp.data["id"]
        _, admin_token = self.make_admin()
        resp = self.api("post", f"/admin/appeals/{appeal_id}/decision",
                        {"decision": "APPROVE"}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "APPROVED")
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, role="HEAD").exists())

    def test_appeal_reject_requires_reason(self):
        _, token = self.make_user()
        unit = self.make_unit(phones=[next_phone()])
        proof = SimpleUploadedFile("proof.png", b"\x89PNG\r\n\x1a\n" + b"2" * 32,
                                   content_type="image/png")
        uploaded = self.upload("/attachments", {"file": proof, "purpose": "APPEAL_PROOF"}, token=token)
        appeal = self.api("post", "/appeals", {"unit_id": unit.id,
                                               "proof_ids": [uploaded.data["id"]]}, token=token)
        _, admin_token = self.make_admin()
        resp = self.api("post", f"/admin/appeals/{appeal.data['id']}/decision",
                        {"decision": "REJECT"}, token=admin_token)
        self.assert_error(resp, 400, "INVALID_VALUE")
        resp = self.api("post", f"/admin/appeals/{appeal.data['id']}/decision",
                        {"decision": "REJECT", "reject_reason": "材料不清"}, token=admin_token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["status"], "REJECTED")


class ResidentTests(ApiTestBase):
    def test_owner_approves_and_removes_resident(self):
        unit = self.make_unit(phones=[next_phone()])
        owner, owner_token = self.make_user(phone=unit.phones.all()[0].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token), 201)
        resident, resident_token = self.make_user()
        resp = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=resident_token)
        self.assert_ok(resp, 201)
        app_id = resp.data["id"]
        resp = self.api("get", "/resident-applications/to-review", token=owner_token)
        self.assert_ok(resp)
        self.assertEqual(len(resp.data), 1)
        resp = self.api("post", f"/resident-applications/{app_id}/decision",
                        {"decision": "APPROVE"}, token=owner_token)
        self.assert_ok(resp)
        self.assertTrue(Membership.objects.filter(user=resident, unit=unit, role="RESIDENT").exists())
        resp = self.api("delete", f"/units/{unit.id}/residents/{resident.id}", token=owner_token)
        self.assert_ok(resp, 204)
        self.assertFalse(Membership.objects.filter(user=resident, unit=unit,
                                                   ended_at__isnull=True).exists())

    def test_only_owner_can_decide(self):
        unit = self.make_unit(phones=[next_phone()])
        owner, owner_token = self.make_user(phone=unit.phones.all()[0].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token), 201)
        _, stranger_token = self.make_user()
        resident, resident_token = self.make_user()
        app = self.api("post", "/resident-applications", {"unit_id": unit.id}, token=resident_token)
        resp = self.api("post", f"/resident-applications/{app.data['id']}/decision",
                        {"decision": "APPROVE"}, token=stranger_token)
        self.assert_error(resp, 403, "FORBIDDEN")

    def test_resident_can_leave(self):
        unit = self.make_unit(phones=[next_phone()])
        owner, owner_token = self.make_user(phone=unit.phones.all()[0].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token), 201)
        resident, resident_token = self.make_user()
        Membership.objects.create(user=resident, unit=unit, role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        resp = self.api("post", f"/units/{unit.id}/leave", token=resident_token)
        self.assert_ok(resp, 204)


class MembershipRevokeTests(ApiTestBase):
    def test_revoke_head_promotes_owner_and_ends_seat(self):
        unit = self.make_unit(phones=[next_phone(), next_phone()])
        head, head_token = self.make_user(phone=unit.phones.all()[0].phone)
        owner, owner_token = self.make_user(phone=unit.phones.all()[1].phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=head_token), 201)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id}, token=owner_token), 201)
        self.make_seat(head, "MEMBER")
        _, admin_token = self.make_admin()
        resp = self.api("post", "/admin/memberships/revoke",
                        {"user_id": head.id, "unit_id": unit.id}, token=admin_token)
        self.assert_ok(resp)
        self.assertFalse(Membership.objects.filter(user=head, ended_at__isnull=True).exists())
        promoted = Membership.objects.get(user=owner, unit=unit, ended_at__isnull=True)
        self.assertEqual(promoted.role, "HEAD")
        self.assertFalse(Seat.objects.filter(user=head, status="ACTIVE").exists())


class SeatTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        _, self.admin_token = self.make_admin()
        self.assert_ok(self.api("put", "/admin/committee/config",
                                {"term_months_chair": 12, "term_months_vice": 12,
                                 "term_months_member": 12, "term_months_rep": 12},
                                token=self.admin_token))

    def test_grant_requires_owner_and_returns_seat(self):
        admin_token = self.admin_token
        stranger, _ = self.make_user()
        today = date.today()
        resp = self.api("post", "/admin/committee/seats",
                        {"user_id": stranger.id, "position": "MEMBER",
                         "term_start": str(today), "term_end": str(today + timedelta(days=30))},
                        token=admin_token)
        self.assert_error(resp, 422, "NOT_AN_OWNER")
        owner, _, _ = self.make_owner()
        resp = self.api("post", "/admin/committee/seats",
                        {"user_id": owner.id, "position": "CHAIR",
                         "term_start": str(today)}, token=admin_token)
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["position"], "CHAIR")

    def test_config_cap_reports_over_cap(self):
        admin_token = self.admin_token
        resp = self.api("put", "/admin/committee/config", {"cap_member": 0}, token=admin_token)
        self.assert_ok(resp)
        owner, _, _ = self.make_owner()
        self.make_seat(owner, "MEMBER")
        resp = self.api("get", "/admin/committee/config", token=admin_token)
        self.assert_ok(resp)
        self.assertTrue(resp.data["over_cap"])

    def test_revoke_seat(self):
        owner, _, _ = self.make_owner()
        seat = self.make_seat(owner, "MEMBER")
        resp = self.api("delete", f"/admin/committee/seats/{seat.id}", token=self.admin_token)
        self.assert_ok(resp, 204)
        seat.refresh_from_db()
        self.assertEqual(seat.status, "REVOKED")

    def test_cap_enforced_on_grant(self):
        admin_token = self.admin_token
        self.assert_ok(self.api("put", "/admin/committee/config", {"cap_vice": 0}, token=admin_token))
        owner, _, _ = self.make_owner()
        resp = self.api("post", "/admin/committee/seats",
                        {"user_id": owner.id, "position": "VICE_CHAIR",
                         "term_start": str(date.today())}, token=admin_token)
        self.assertIn(resp.status_code, (409, 422), resp.content)
