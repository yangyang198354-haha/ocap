"""邮件网关（MOD-002 / IFC-012）。"""
from typing import Protocol

from django.conf import settings
from django.core.mail import send_mail


class EmailSendError(Exception):
    pass


class EmailGateway(Protocol):
    def send_code(self, email: str, code: str, purpose: str, ttl_minutes: int) -> None: ...


class DjangoEmailGateway:
    def send_code(self, email: str, code: str, purpose: str, ttl_minutes: int) -> None:
        subject = "ocap 验证码"
        body = f"您的验证码是 {code}，{ttl_minutes} 分钟内有效。如非本人操作请忽略。"
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        except Exception as exc:
            raise EmailSendError(str(exc)) from exc


_gateway: EmailGateway | None = None


def get_email_gateway() -> EmailGateway:
    global _gateway
    if _gateway is None:
        _gateway = DjangoEmailGateway()
    return _gateway


def set_email_gateway(gateway: EmailGateway | None) -> None:
    global _gateway
    _gateway = gateway
