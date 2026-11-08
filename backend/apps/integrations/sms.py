"""短信网关协议与开发替身（MOD-002 / IFC-011）。"""
from typing import Literal, Protocol

from django.conf import settings

KIND = Literal["RATE_LIMITED", "INVALID_NUMBER", "QUOTA_OR_BALANCE", "CONFIG", "UPSTREAM"]


class SmsSendError(Exception):
    def __init__(self, kind: KIND, provider_code: str | None = None, retryable: bool = False):
        self.kind = kind
        self.provider_code = provider_code
        self.retryable = retryable
        super().__init__(kind)


class SmsGateway(Protocol):
    def send_code(self, phone: str, code: str, purpose: str) -> None: ...


class ConsoleSmsGateway:
    """开发替身：不发送，只写日志（不含验证码明文）。"""

    def send_code(self, phone: str, code: str, purpose: str) -> None:
        import logging

        logging.getLogger("ocap.sms").info("console sms sent to %s****%s purpose=%s", phone[:3], phone[-4:], purpose)


def get_sms_gateway() -> SmsGateway:
    backend = settings.SMS_GATEWAY_BACKEND
    if backend == "memory":
        from .fakes import FakeSmsGateway

        return FakeSmsGateway.shared()
    if backend == "aliyun":
        from .aliyun_sms import AliyunSmsGateway

        return AliyunSmsGateway()
    return ConsoleSmsGateway()
