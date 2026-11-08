import re

from rest_framework import serializers

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def mask_phone(phone: str) -> str:
    if not isinstance(phone, str) or not PHONE_RE.match(phone):
        return "****"
    return f"{phone[:3]}****{phone[-4:]}"


def mask_email(email: str) -> str:
    if not isinstance(email, str) or "@" not in email:
        return "****"
    local, _, domain = email.partition("@")
    if not local:
        return "****"
    return f"{local[0]}***@{domain}"


class MaskedPhoneField(serializers.CharField):
    def to_representation(self, value):
        return mask_phone(value)


class PlainPhoneField(serializers.CharField):
    """仅 /admin/registry/** 使用（US-019 AC-019-06）。"""
