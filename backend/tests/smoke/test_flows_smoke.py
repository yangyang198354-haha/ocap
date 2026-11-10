"""最小冒烟测试（开发者自验证，文件名含 smoke，GROUP_D 可替换）。"""
import json
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AdminAccount, User
from apps.accounts.services import AccountService
from apps.committee.models import Seat
from apps.integrations.fakes import FakeSmsGateway
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit

PASSWORD = "Abc12345"


class ApiSmokeTest(TestCase):
    def setUp(self):
        FakeSmsGateway.shared().reset()
        self.client = APIClient()

    def code(self, phone, purpose="REGISTER", target_type="PHONE"):
        resp = self.client.post("/api/v1/auth/codes", {
            "target": phone, "target_type": target_type, "purpose": purpose,
        }, format="json")
        self.assertEqual(resp.status_code, 202, resp.content)
        return FakeSmsGateway.shared().sent[-1][1]

    def register(self, phone="13800000001"):
        code = self.code(phone)
        resp = self.client.post("/api/v1/auth/register", {
            "phone": phone, "code": code,
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()["token"], resp.json()["user"]["id"]

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def make_user(self, phone, nickname="业主", **kwargs):
        return User.objects.create(account_no=str(10_000_000_000 + User.objects.count() + 1),
                                   phone=phone, nickname=nickname, **kwargs)

    def make_admin(self, username="admin1"):
        return AdminAccount.objects.create(username=username, password=make_password(PASSWORD))

    def login_admin(self, admin):
        resp = self.client.post("/api/v1/admin/auth/login", {
            "username": admin.username, "password": PASSWORD,
        }, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.json()["token"]

    def make_unit(self, phone=None):
        unit = RegistryUnit.objects.create(building="1", unit_no="1", floor="1", room="101")
        if phone:
            owner = RegistryOwner.objects.create(unit=unit, name="业主甲")
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def test_register_login_and_profile(self):
        token, user_id = self.register()
        self.auth(token)
        resp = self.client.get("/api/v1/me/profile")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("138****0001", resp.json()["phone"])
        me = self.client.get("/api/v1/me")
        self.assertEqual(me.status_code, 200)
        self.assertIn("游客", me.json()["identities"]["labels"])

    def test_certification_and_duplicate(self):
        token, user_id = self.register("13800000002")
        unit = self.make_unit("13800000002")
        self.auth(token)
        resp = self.client.post("/api/v1/certifications", {"unit_id": unit.id}, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.json()["role"], "HEAD")
        again = self.client.post("/api/v1/certifications", {"unit_id": unit.id}, format="json")
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.json()["code"], "ALREADY_CERTIFIED")

    def test_certification_mismatch_returns_422(self):
        token, _ = self.register("13800000003")
        unit = self.make_unit("13900000000")
        self.auth(token)
        resp = self.client.post("/api/v1/certifications", {"unit_id": unit.id}, format="json")
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["code"], "PHONE_NOT_IN_REGISTRY")

    def test_resolution_designated_flow(self):
        initiator = self.make_user("13800000101", "主任")
        approver = self.make_user("13800000102", "委员")
        Seat.objects.create(user=initiator, position="CHAIR",
                            term_start=timezone.localdate(),
                            term_end=timezone.localdate() + timedelta(days=365), active_slot=1)
        Seat.objects.create(user=approver, position="MEMBER",
                            term_start=timezone.localdate(),
                            term_end=timezone.localdate() + timedelta(days=365), active_slot=1)
        admin = self.make_admin()
        admin_token = self.login_admin(admin)
        self.auth(admin_token)
        flow = self.client.post("/api/v1/admin/approval/flows", {
            "scope": "RESOLUTION", "name": "主任审批", "mode": "DESIGNATED",
            "approver_ids": [approver.id],
        }, format="json")
        self.assertEqual(flow.status_code, 201, flow.content)
        flow_id = flow.json()["id"]
        self.auth(AccountService.issue_token(initiator))
        created = self.client.post("/api/v1/resolutions", {
            "title": "测试决议", "content": "内容", "approval_flow_id": flow_id,
        }, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        resolution_id = created.json()["id"]
        self.auth(AccountService.issue_token(approver))
        tasks = self.client.get("/api/v1/approval/tasks")
        self.assertEqual(tasks.status_code, 200)
        self.assertEqual(tasks.json()["count"], 1)
        instance_id = tasks.json()["results"][0]["instance_id"]
        decision = self.client.post(f"/api/v1/approval/instances/{instance_id}/decision", {
            "action": "APPROVE",
        }, format="json")
        self.assertEqual(decision.status_code, 200, decision.content)
        detail = self.client.get(f"/api/v1/resolutions/{resolution_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status"], "APPROVED")

    def test_income_import_submit_and_approve(self):
        recorder = self.make_user("13800000201", "记账员")
        approver = self.make_user("13800000202", "主任")
        for user, position in ((recorder, "MEMBER"), (approver, "CHAIR")):
            Seat.objects.create(user=user, position=position, term_start=timezone.localdate(),
                                term_end=timezone.localdate() + timedelta(days=365), active_slot=1)
        admin = self.make_admin()
        admin_token = self.login_admin(admin)
        self.auth(admin_token)
        flow = self.client.post("/api/v1/admin/approval/flows", {
            "scope": "INCOME", "name": "收入审批", "mode": "DESIGNATED",
            "approver_ids": [approver.id],
        }, format="json")
        self.assertEqual(flow.status_code, 201, flow.content)
        flow_id = flow.json()["id"]
        self.auth(AccountService.issue_token(recorder))
        upload = SimpleUploadedFile(
            "income.csv",
            "日期,金额,收入类别,来源说明,备注\n2026-11-01,100.50,停车费,停车,\n2026-11-02,200,场地费,场地,\n".encode("utf-8"),
            content_type="text/csv",
        )
        imported = self.client.post("/api/v1/admin/income/sheets/import", {"file": upload},
                                    format="multipart")
        self.assertEqual(imported.status_code, 201, imported.content)
        sheet_id = imported.json()["id"]
        self.assertEqual(imported.json()["total_amount"], "300.50")
        submitted = self.client.post(f"/api/v1/admin/income/sheets/{sheet_id}/submit",
                                     {"approval_flow_id": flow_id}, format="json")
        self.assertEqual(submitted.status_code, 200, submitted.content)
        self.assertEqual(submitted.json()["status"], "PENDING")
        self.auth(AccountService.issue_token(approver))
        tasks = self.client.get("/api/v1/approval/tasks?scope=INCOME").json()
        instance_id = tasks["results"][0]["instance_id"]
        decided = self.client.post(f"/api/v1/approval/instances/{instance_id}/decision",
                                   {"action": "APPROVE"}, format="json")
        self.assertEqual(decided.status_code, 200, decided.content)
        detail = self.client.get(f"/api/v1/income/sheets/{sheet_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status"], "EFFECTIVE")

    def test_unauthenticated_and_forbidden(self):
        resp = self.client.get("/api/v1/me")
        self.assertEqual(resp.status_code, 401)
        token, _ = self.register("13800000301")
        self.auth(token)
        resp = self.client.post("/api/v1/resolutions", {
            "title": "x", "content": "y", "approval_flow_id": 1,
        }, format="json")
        self.assertEqual(resp.status_code, 403)


_ = (json, uuid)
