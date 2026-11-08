"""PHASE_08 集成测试：认证、账号与个人信息。"""
from django.core import mail

from tests.support import ApiTestBase, next_phone


class RegistrationAndLoginTests(ApiTestBase):
    def test_register_with_sms_code(self):
        phone = next_phone()
        code = self.request_code(phone, "REGISTER")
        resp = self.api("post", "/auth/register", {"phone": phone, "code": code})
        self.assert_ok(resp, 201)
        self.assertEqual(resp.data["user"]["status"], "ACTIVE")
        self.assertTrue(resp.data["token"])
        me = self.api("get", "/me", token=resp.data["token"])
        self.assert_ok(me)
        self.assertIn("游客", me.data["identities"]["labels"])

    def test_duplicate_phone_returns_409(self):
        user, _ = self.make_user()
        resp = self.api("post", "/auth/codes", {"target": user.phone, "target_type": "PHONE",
                                                "purpose": "REGISTER"})
        self.assert_error(resp, 409, "PHONE_ALREADY_REGISTERED")

    def test_wrong_code_then_locked(self):
        phone = next_phone()
        self.request_code(phone, "REGISTER")
        for _ in range(5):
            resp = self.api("post", "/auth/register", {"phone": phone, "code": "000000"})
            self.assertIn(resp.status_code, (400, 429))
        resp = self.api("post", "/auth/register", {"phone": phone, "code": "000000"})
        self.assert_error(resp, 429, "CODE_LOCKED")

    def test_code_resend_rate_limited(self):
        phone = next_phone()
        self.request_code(phone, "REGISTER")
        resp = self.api("post", "/auth/codes", {"target": phone, "target_type": "PHONE",
                                                "purpose": "REGISTER"})
        self.assert_error(resp, 429, "CODE_RATE_LIMITED")

    def test_login_by_code(self):
        user, _ = self.make_user()
        resp = self.login_code(user.phone)
        self.assert_ok(resp)
        self.assertTrue(resp.data["token"])

    def test_login_by_password_and_lockout(self):
        user, token = self.make_user()
        password = "Ocap2026pass"
        resp = self.api("put", "/me/password", {"password": password,
                                                "password_confirm": password}, token=token)
        self.assert_ok(resp, 204)
        for _ in range(4):
            resp = self.api("post", "/auth/login/password",
                            {"identifier": user.account_no, "password": "Wrong0000"})
            self.assertEqual(resp.status_code, 400, resp.content)
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.account_no, "password": "Wrong0000"})
        self.assert_error(resp, 429, "LOGIN_LOCKED")
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.account_no, "password": password})
        self.assert_error(resp, 429, "LOGIN_LOCKED")

    def test_login_by_password_after_set(self):
        user, token = self.make_user()
        password = "Ocap2026pass"
        self.assert_ok(self.api("put", "/me/password", {"password": password,
                                                        "password_confirm": password}, token=token), 204)
        resp = self.api("post", "/auth/login/password",
                        {"identifier": user.account_no, "password": password})
        self.assert_ok(resp)
        self.assertTrue(resp.data["token"])

    def test_logout_revokes_token(self):
        _, token, _ = self.register()
        self.assert_ok(self.api("post", "/auth/logout", token=token), 204)
        self.assert_error(self.api("get", "/me", token=token), 401)

    def test_miniapp_login_unavailable_without_sdk(self):
        resp = self.api("post", "/auth/wechat/miniapp", {"code": "mock-mini-001"})
        self.assert_error(resp, 503, "WECHAT_UNAVAILABLE")


class ProfileTests(ApiTestBase):
    def test_edit_profile_and_forbidden_field(self):
        _, token, _ = self.register()
        resp = self.api("patch", "/me/profile", {"nickname": "业主甲"}, token=token)
        self.assert_ok(resp)
        self.assertEqual(resp.data["nickname"], "业主甲")
        resp = self.api("patch", "/me/profile", {"identity_label": "主任"}, token=token)
        self.assert_error(resp, 400, "FIELD_NOT_EDITABLE")

    def test_nickname_length_validated(self):
        _, token, _ = self.register()
        resp = self.api("patch", "/me/profile", {"nickname": "x" * 31}, token=token)
        self.assert_error(resp, 400, "INVALID_VALUE")

    def test_avatar_upload_and_reject_bad_type(self):
        _, token, _ = self.register()
        from django.core.files.uploadedfile import SimpleUploadedFile

        good = SimpleUploadedFile("avatar.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32,
                                  content_type="image/png")
        resp = self.upload("/me/avatar", {"file": good}, token=token)
        self.assert_ok(resp, 201)
        bad = SimpleUploadedFile("avatar.exe", b"MZ", content_type="application/octet-stream")
        resp = self.upload("/me/avatar", {"file": bad}, token=token)
        self.assert_error(resp, 400)

    def test_email_verify_and_login_by_email(self):
        user, token, _ = self.register(email="owner@example.com")
        code = self.request_me_code(token, "EMAIL_VERIFY")
        resp = self.api("post", "/me/email/verify", {"email": "owner@example.com", "code": code},
                        token=token)
        self.assert_ok(resp)
        from apps.core.models import RateLimit

        RateLimit.objects.filter(key__contains="owner@example.com").delete()
        resp = self.api("post", "/auth/codes", {"target": "owner@example.com",
                                                "target_type": "EMAIL", "purpose": "EMAIL_LOGIN"})
        self.assert_ok(resp, 202)
        body = mail.outbox[-1].body
        import re

        email_code = re.search(r"(\d{6})", body).group(1)
        resp = self.api("post", "/auth/login/email", {"email": "owner@example.com", "code": email_code})
        self.assert_ok(resp)
        self.assertEqual(resp.data["user"]["id"], user["id"])

    def test_cancel_account_requires_code(self):
        user, token = self.make_user()
        code = self.request_me_code(token, "CANCEL")
        resp = self.api("post", "/me/cancel", {"phone": user.phone, "code": code}, token=token)
        self.assert_ok(resp, 204)
        self.assert_error(self.api("get", "/me", token=token), 401)


class AdminAuthTests(ApiTestBase):
    def test_admin_login_and_audit(self):
        admin, _ = self.make_admin(username="boss")
        resp = self.api("post", "/admin/auth/login", {"username": "boss", "password": "Admin12345"})
        self.assert_ok(resp)
        token = resp.data["token"]
        resp = self.api("get", "/admin/audit-logs", token=token)
        self.assert_ok(resp)

    def test_admin_login_wrong_password(self):
        self.make_admin(username="boss2")
        resp = self.api("post", "/admin/auth/login", {"username": "boss2", "password": "bad"})
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_member_token_cannot_call_admin(self):
        _, token, _ = self.register()
        resp = self.api("get", "/admin/audit-logs", token=token)
        self.assert_error(resp, 403)
