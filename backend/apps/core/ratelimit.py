"""数据库限流与锁定（IFC-007，ADR-008）。"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Lockout, RateLimit


@dataclass
class RateDecision:
    allowed: bool
    retry_after: int = 0


class RateLimiter:
    @staticmethod
    def _window(now: datetime, seconds: int) -> datetime:
        epoch = int(now.timestamp())
        return datetime.fromtimestamp(epoch - (epoch % seconds), tz=now.tzinfo)

    @staticmethod
    def hit(key: str, *, limit: int, window_seconds: int) -> RateDecision:
        now = timezone.now()
        start = RateLimiter._window(now, window_seconds)
        with transaction.atomic():
            row, created = RateLimit.objects.select_for_update().get_or_create(
                key=key, window_start=start, defaults={"count": 0}
            )
            if created:
                row.count = 0
            if row.count >= limit:
                retry = int((start + timedelta(seconds=window_seconds) - now).total_seconds())
                return RateDecision(False, max(retry, 1))
            row.count += 1
            row.save(update_fields=["count"])
        return RateDecision(True, 0)

    @staticmethod
    def is_locked(key: str) -> RateDecision:
        now = timezone.now()
        row = Lockout.objects.filter(key=key).first()
        if row and row.locked_until and row.locked_until > now:
            return RateDecision(False, int((row.locked_until - now).total_seconds()))
        return RateDecision(True, 0)

    @staticmethod
    def register_failure(key: str, *, limit: int, window_seconds: int, lock_seconds: int) -> RateDecision:
        now = timezone.now()
        with transaction.atomic():
            row, _ = Lockout.objects.select_for_update().get_or_create(
                key=key, defaults={"fail_count": 0, "window_start": now}
            )
            if row.locked_until and row.locked_until > now:
                return RateDecision(False, int((row.locked_until - now).total_seconds()))
            if now - row.window_start > timedelta(seconds=window_seconds):
                row.fail_count = 0
                row.window_start = now
            row.fail_count += 1
            if row.fail_count >= limit:
                row.locked_until = now + timedelta(seconds=lock_seconds)
                row.save()
                return RateDecision(False, lock_seconds)
            row.save()
        return RateDecision(True, 0)

    @staticmethod
    def reset(key: str) -> None:
        Lockout.objects.filter(key=key).delete()


def client_ip(request) -> str:
    direct = request.META.get("REMOTE_ADDR", "") or "0.0.0.0"
    if direct in settings.TRUSTED_PROXY_ADDRS:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            hops = [h.strip() for h in forwarded.split(",") if h.strip()]
            if hops:
                return hops[-1]
    return direct
