"""阿里云短信网关（MOD-002 / IFC-011 / ADR-022）。

错误码归类出处：[P11: https://api.aliyun.com/document/Dysmsapi/2017-05-25/errorCode 2026-11-07]
"""
import json
import logging

from django.conf import settings

from .sms import SmsSendError

logger = logging.getLogger("ocap.sms")

RATE_LIMITED_CODES = {"isv.BUSINESS_LIMIT_CONTROL", "isv.DAY_LIMIT_CONTROL", "isv.MONTH_LIMIT_CONTROL"}
CONFIG_CODES = {
    "isv.SMS_SIGNATURE_ILLEGAL", "isv.SMS_TEMPLATE_ILLEGAL", "isv.TEMPLATE_MISSING_PARAMETERS",
    "isv.INVALID_PARAMETERS", "isv.ACCOUNT_ABNORMAL", "isp.RAM_PERMISSION_DENY",
}


class AliyunSmsGateway:
    def send_code(self, phone: str, code: str, purpose: str) -> None:
        try:
            from alibabacloud_dysmsapi20170525.client import Client  # type: ignore
            from alibabacloud_dysmsapi20170525 import models as dysms_models  # type: ignore
            from alibabacloud_tea_openapi import models as openapi_models  # type: ignore
        except ImportError as exc:
            raise SmsSendError("CONFIG", provider_code="SDK_MISSING") from exc
        if not all([settings.ALIYUN_ACCESS_KEY_ID, settings.ALIYUN_ACCESS_KEY_SECRET,
                    settings.ALIYUN_SMS_SIGN_NAME, settings.ALIYUN_SMS_TEMPLATE_CODE]):
            raise SmsSendError("CONFIG", provider_code="NOT_CONFIGURED")
        config = openapi_models.Config(
            access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
            access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
        )
        config.endpoint = "dysmsapi.aliyuncs.com"
        request = dysms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.ALIYUN_SMS_SIGN_NAME,
            template_code=settings.ALIYUN_SMS_TEMPLATE_CODE,
            template_param=json.dumps({"code": code}),
        )
        try:
            response = Client(config).send_sms(request)
        except Exception as exc:  # 网络/超时
            raise SmsSendError("UPSTREAM", retryable=True) from exc
        body = response.body
        if body.code == "OK":
            logger.info("aliyun sms sent biz_id=%s request_id=%s", body.biz_id, body.request_id)
            return
        provider_code = body.code or ""
        if provider_code in RATE_LIMITED_CODES:
            raise SmsSendError("RATE_LIMITED", provider_code)
        if provider_code == "isv.MOBILE_NUMBER_ILLEGAL":
            raise SmsSendError("INVALID_NUMBER", provider_code)
        if provider_code == "isv.AMOUNT_NOT_ENOUGH":
            raise SmsSendError("QUOTA_OR_BALANCE", provider_code)
        if provider_code in CONFIG_CODES:
            raise SmsSendError("CONFIG", provider_code)
        raise SmsSendError("UPSTREAM", provider_code, retryable=True)
