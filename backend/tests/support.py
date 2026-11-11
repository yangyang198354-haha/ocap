"""测试支撑：API 客户端、工厂与验证码读取（GROUP_D）。"""
import re
from datetime import timedelta
from uuid import uuid4

from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import AdminAccount, User
from apps.accounts.services import AccountService
from apps.approval.models import ApprovalFlow, FlowApprover
from apps.committee.models import Seat
from apps.integrations.fakes import FakeSmsGateway
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Membership

_counter = {"n": 0}


def next_phone() -> str:
    _counter["n"] += 1
    return f"139{_counter['n']:08d}"


def next_account_no() -> str:
    _counter["n"] += 1
    return f"8{_counter['n']:09d}"


def next_specific_part(prefix: str = "1栋1单元") -> str:
    _counter["n"] += 1
    return f"{prefix}{_counter['n']:04d}号{uuid4().hex[:4]}"


class ApiTestBase(APITestCase):
    def setUp(self):
        super().setUp()
        FakeSmsGateway.shared().reset()
        mail.outbox.clear()
        self._clients = []

    # ---------- HTTP ----------
    def client_for(self, token: str | None = None) -> APIClient:
        client = APIClient()
        if token:
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self._clients.append(client)
        return client

    def api(self, method: str, path: str, data=None, token=None, **extra):
        client = self.client_for(token)
        return getattr(client, method)(f"/api/v1{path}", data if data is not None else {},
                                       format="json", **extra)

    def upload(self, path: str, files: dict, data=None, token=None):
        client = self.client_for(token)
        return client.post(f"/api/v1{path}", {**(data or {}), **files}, format="multipart")

    # ---------- 账号 ----------
    def request_code(self, target: str, purpose: str = "REGISTER", target_type: str = "PHONE") -> str:
        resp = self.api("post", "/auth/codes", {"target": target, "target_type": target_type,
                                                "purpose": purpose})
        assert resp.status_code == 202, resp.content
        if target_type == "PHONE":
            rows = [r for r in FakeSmsGateway.shared().sent if r[0] == target and r[2] == purpose]
            assert rows, "未捕获短信验证码"
            return rows[-1][1]
        body = mail.outbox[-1].body
        found = re.search(r"(\d{6})", body)
        assert found, "未捕获邮件验证码"
        return found.group(1)

    def request_me_code(self, token: str, purpose: str, target: str | None = None) -> str:
        payload = {"purpose": purpose}
        if target:
            payload["target"] = target
        resp = self.api("post", "/me/codes", payload, token=token)
        assert resp.status_code == 202, resp.content
        if purpose == "EMAIL_VERIFY":
            body = mail.outbox[-1].body
            return re.search(r"(\d{6})", body).group(1)
        target = target or self.user_of(token).phone
        rows = [r for r in FakeSmsGateway.shared().sent if r[0] == target]
        assert rows, "未捕获短信验证码"
        return rows[-1][1]

    def register(self, phone: str | None = None, email: str | None = None):
        phone = phone or next_phone()
        code = self.request_code(phone, "REGISTER")
        resp = self.api("post", "/auth/register", {"phone": phone, "code": code, "email": email})
        assert resp.status_code == 201, resp.content
        return resp.data["user"], resp.data["token"], phone

    def login_code(self, phone: str):
        code = self.request_code(phone, "LOGIN")
        return self.api("post", "/auth/login/code", {"phone": phone, "code": code})

    def make_user(self, phone: str | None = None, nickname: str | None = None):
        user = User.objects.create(account_no=next_account_no(), phone=phone or next_phone(),
                                   nickname=nickname)
        return user, AccountService.issue_token(user)

    def user_of(self, token: str) -> User:
        from apps.accounts.models import AuthToken
        from apps.accounts.services import _sha256

        row = AuthToken.objects.filter(key_hash=_sha256(token)).first()
        assert row is not None and row.user_id, "令牌对应用户不存在"
        return row.user

    def make_admin(self, username: str | None = None, password: str = "Admin12345"):
        from django.contrib.auth.hashers import make_password

        admin = AdminAccount.objects.create(username=username or f"admin{uuid4().hex[:8]}",
                                            password=make_password(password))
        return admin, AccountService.issue_token(admin)

    def token_of(self, user) -> str:
        return AccountService.issue_token(user)

    # ---------- 资源 ----------
    def make_unit(self, phones=None, name: str = "业主甲") -> RegistryUnit:
        unit = RegistryUnit.objects.create(
            building="1", unit_no=f"u{next_account_no()}", floor="1", room="101",
        )
        if phones:
            owner = RegistryOwner.objects.create(unit=unit, name=name)
            for phone in phones:
                RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def make_owner(self, phone: str | None = None, unit: RegistryUnit | None = None,
                   role: str = "HEAD"):
        user, token = self.make_user(phone=phone)
        unit = unit or self.make_unit(phones=[user.phone])
        Membership.objects.create(user=user, unit=unit, role=role, source="CERTIFIED",
                                  active_slot=1, head_slot=1 if role == "HEAD" else None)
        return user, token, unit

    def make_resident(self, unit: RegistryUnit):
        user, token = self.make_user()
        Membership.objects.create(user=user, unit=unit, role="RESIDENT", source="APPLICATION",
                                  active_slot=1)
        return user, token

    def make_seat(self, user: User, position: str = "MEMBER", days: int = 365) -> Seat:
        today = timezone.localdate()
        return Seat.objects.create(user=user, position=position, term_start=today,
                                   term_end=today + timedelta(days=days), status="ACTIVE",
                                   active_slot=1)

    def make_flow(self, scope: str = "RESOLUTION", mode: str = "DESIGNATED", approvers=(),
                  name: str | None = None) -> ApprovalFlow:
        flow = ApprovalFlow.objects.create(scope=scope, mode=mode,
                                           name=name or f"{scope}-{uuid4().hex[:8]}")
        for user in approvers:
            FlowApprover.objects.create(flow=flow, user=user)
        return flow

    # ---------- 断言 ----------
    def assert_ok(self, resp, status_code=200):
        self.assertEqual(resp.status_code, status_code, getattr(resp, "content", b""))
        return resp

    def assert_error(self, resp, status_code: int, code: str | None = None):
        self.assertEqual(resp.status_code, status_code, getattr(resp, "content", b""))
        body = resp.json()
        self.assertIn("code", body)
        self.assertIn("message", body)
        if code:
            self.assertEqual(body["code"], code)
        return body
