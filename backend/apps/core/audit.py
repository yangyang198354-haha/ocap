"""审计写入（IFC-001）。同事务写入；detail 写入前脱敏。"""
from dataclasses import dataclass
from typing import Any, Literal

from .masking import PHONE_RE
from .models import AuditLog

AuditResult = Literal["SUCCESS", "FAILURE", "DENIED"]

AUDIT_ACTIONS = {
    "ADMIN_LOGIN", "ADMIN_LOGIN_FAILED", "REGISTER", "CERTIFY_BY_REGISTRY",
    "HEAD_ASSIGNED", "HEAD_SUCCEEDED", "APPEAL_SUBMITTED", "APPEAL_DECIDED",
    "RESIDENT_APPLICATION_DECIDED", "RESIDENT_REMOVED", "RESIDENT_LEFT",
    "CERTIFICATION_REVOKED", "ACCOUNT_CANCELLED", "ACCOUNTS_MERGED", "PHONE_CHANGED",
    "PHONE_BOUND", "EMAIL_OWNERSHIP_CHANGED", "REGISTRY_IMPORTED", "REGISTRY_UNIT_CHANGED",
    "SEAT_GRANTED", "SEAT_CHANGED", "SEAT_REVOKED", "SEAT_EXPIRED", "SEAT_INVALIDATED",
    "COMMITTEE_CONFIG_CHANGED", "APPROVAL_FLOW_CHANGED", "RESOLUTION_SUBMITTED",
    "RESOLUTION_WITHDRAWN", "RESOLUTION_DECIDED", "CLAIM_SUBMITTED", "CLAIM_WITHDRAWN",
    "CLAIM_DECIDED", "INCOME_SUBMITTED", "INCOME_WITHDRAWN", "INCOME_DECIDED",
    "INCOME_VOIDED", "INCOME_IMPORTED", "POLL_CREATED", "POLL_CLOSED",
    "REPORT_GENERATED", "AUDIT_PURGED", "ADMIN_CREATED", "ADMIN_PASSWORD_RESET",
    "SYSTEM_CONFIG_CHANGED", "MERGE_ANSWER_DISCARDED", "POLL_VOTED",
    "CONTENT_POST_PUBLISHED", "CONTENT_POST_UPDATED", "CONTENT_POST_OFFLINED",
    "CONTENT_POST_DELETED", "CONTENT_SERVICE_CONFIG_CHANGED", "CONTENT_SERVICE_TESTED",
    "CONTENT_VIDEO_REQUESTED", "CONTENT_VIDEO_COMPLETED", "CONTENT_MEDIA_DELETED",
    "CONTENT_PLATFORM_ACCOUNT_CHANGED", "CONTENT_DRAFT_PUSHED", "CONTENT_PACK_EXPORTED",
    "CONTENT_PLATFORM_AUTH_EXPIRED",
}

SENSITIVE_KEYS = {"password", "code", "token", "session_key", "secret", "authorization"}


@dataclass(frozen=True)
class AuditActor:
    type: str
    id: int | None = None
    label: str = ""


def _scrub(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "***"
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if str(k).lower() in SENSITIVE_KEYS:
                result[k] = "***"
            else:
                result[k] = _scrub(v, depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        return [_scrub(v, depth + 1) for v in value]
    if isinstance(value, str):
        if PHONE_RE.match(value):
            return value[:3] + "****" + value[-4:]
        return value
    return value


class AuditService:
    @staticmethod
    def record(*, actor: AuditActor, action: str, object_type: str, object_id: str,
               result: AuditResult, detail: dict | None = None, ip: str | None = None) -> None:
        if action not in AUDIT_ACTIONS:
            raise ValueError(f"未登记的审计动作: {action}")
        AuditLog.objects.create(
            actor_type=actor.type,
            actor_id=actor.id,
            actor_label=actor.label[:64],
            action=action,
            object_type=object_type,
            object_id=str(object_id)[:64],
            result=result,
            detail=_scrub(detail or {}),
            ip=ip,
        )


def system_actor() -> AuditActor:
    return AuditActor(type="SYSTEM", id=None, label="系统")
