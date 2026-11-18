"""集成测试：showcode 管理命令（测试辅助，还原验证码明文）。"""
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import VerificationCode
from apps.accounts.services import _code_hmac
from tests.support import ApiTestBase, next_phone


class ShowCodeCommandTests(ApiTestBase):
    def _make_code(self, target: str, code: str, purpose: str = "REGISTER",
                   target_type: str = "PHONE", ttl: int = 300) -> str:
        VerificationCode.objects.create(
            target=target, target_type=target_type, purpose=purpose,
            code_hmac=_code_hmac(target, purpose, code),
            expires_at=timezone.now() + timedelta(seconds=ttl))
        return code

    def test_tc_int_showcode_recovers_latest_code(self):
        # 经真实接口下发一次（验证 HMAC 还原与线上路径一致）
        phone = next_phone()
        code = self.request_code(phone, "REGISTER")
        out = StringIO()
        call_command("showcode", phone, stdout=out)
        text = out.getvalue()
        self.assertIn(code, text)
        self.assertIn("purpose=REGISTER", text)
        self.assertIn("状态=有效", text)

    def test_tc_int_showcode_filters_by_purpose(self):
        phone = next_phone()
        reg = self._make_code(phone, "135790", "REGISTER")
        login = self._make_code(phone, "246801", "LOGIN")
        self.assertNotEqual(reg, login)
        out = StringIO()
        call_command("showcode", phone, "--purpose", "REGISTER", stdout=out)
        text = out.getvalue()
        self.assertIn(reg, text)
        self.assertNotIn(login, text)

    def test_tc_int_showcode_not_found_raises(self):
        with self.assertRaises(CommandError):
            call_command("showcode", next_phone())

    @override_settings(SMS_GATEWAY_BACKEND="aliyun")
    def test_tc_int_showcode_refused_on_real_sms(self):
        phone = next_phone()
        with self.assertRaises(CommandError):
            call_command("showcode", phone)
