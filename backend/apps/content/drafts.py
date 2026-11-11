"""MOD-053：草稿推送批次与处理器（IFC-186）。"""
import uuid
from datetime import datetime
from typing import Sequence

from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.integrations.draft import MediaFile, get_draft_adapter

from .conf import ContentSettings
from .jobs import Done, Fail, JobContext, JobService
from .models import ContentJob, DraftPush, MediaItem, PlatformAccount
from .posts import PostService
from .richtext import render_html, render_text, unsupported_features
from .styles import StyleService


def _actor(admin):
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or "")


def _out(row: DraftPush) -> dict:
    account = row.account
    return {
        "id": row.id, "batch_id": str(row.batch_id), "platform": row.platform,
        "display_name": account.display_name if account else "",
        "mode": row.mode, "status": row.status,
        "error_code": row.error_code, "error_message": row.error_message,
        "unsupported": list(row.unsupported or []), "remote_ref": row.remote_ref,
        "created_at": row.created_at, "finished_at": row.finished_at,
        "operator": row.created_by_label,
    }


class DraftPushService:
    @staticmethod
    def build_payload(post, adapter) -> dict:
        ttl = int(ContentSettings.get("content.media.push_url_ttl_seconds"))

        def resolve(media_id):
            row = MediaItem.objects.filter(id=media_id).first()
            if row is None:
                return None
            from .media import sign_media_url
            return {"url": sign_media_url(row.id, ttl_seconds=ttl, absolute=True),
                    "media_type": row.media_type, "title": row.title}

        tokens = StyleService.resolve_tokens(post.style_key)
        html = render_html(post.doc, tokens, mode="inline", resolve=resolve)
        media = []
        for link in post.media_links.select_related("media"):
            row = link.media
            media.append(MediaFile(media_id=str(row.id), path=row.storage_path,
                                   content_type=row.content_type,
                                   media_type=row.media_type, name=row.title or row.original_name))
        from apps.integrations.draft import DraftPayload
        return DraftPayload(title=post.title, html=html,
                            text=render_text(post.doc), media=tuple(media))

    @staticmethod
    def start_batch(post_id: int, account_ids: Sequence[int], admin):
        ids = []
        for raw in account_ids or []:
            try:
                value = int(raw)
            except (TypeError, ValueError):
                raise ApiError("INVALID_VALUE", "账户编号不合法", 400)
            if value not in ids:
                ids.append(value)
        if not ids:
            raise ApiError("NO_PLATFORM_SELECTED", "请至少选择一个平台", 400)
        if len(ids) > 3:
            raise ApiError("INVALID_VALUE", "一次最多选择 3 个平台", 400)
        post = PostService.get(post_id)
        accounts = list(PlatformAccount.objects.filter(id__in=ids))
        if len(accounts) != len(ids):
            raise ApiError("INVALID_VALUE", "平台账户不存在", 400)
        if not PostService.is_confirmed(post):
            raise ApiError("POST_NOT_CONFIRMED", "请先确认内容", 409)

        batch_id = uuid.uuid4()
        pushes = []
        has_pending = False
        now = timezone.now()
        for account in accounts:
            adapter = get_draft_adapter(account.platform)
            unsupported = unsupported_features(
                post.doc, platform_unsupported=adapter.unsupported_features)
            if adapter.capability == "MANUAL_EXPORT":
                unsupported = unsupported + ["style_not_carried"]
                status, mode, finished = "MANUAL_REQUIRED", "MANUAL", now
            elif not account.secret_keys:
                status, mode, finished = "FAILED", "AUTO", now
            else:
                status, mode, finished = "PENDING", "AUTO", None
                has_pending = True
            row = DraftPush.objects.create(
                post=post, account=account, platform=account.platform, batch_id=batch_id,
                mode=mode, status=status, unsupported=unsupported,
                error_code="NO_CREDENTIALS" if status == "FAILED" else "",
                error_message="未配置认证信息" if status == "FAILED" else "",
                finished_at=finished,
                created_by_admin_id=getattr(admin, "id", 0),
                created_by_label=getattr(admin, "username", "")[:64],
            )
            pushes.append(row)

        job = None
        if has_pending:
            job = JobService.enqueue(
                kind="DRAFT_PUSH",
                payload={"push_ids": [row.id for row in pushes if row.status == "PENDING"]},
                admin_id=getattr(admin, "id", 0),
                admin_label=getattr(admin, "username", "") or "",
                subject_type="content_post", subject_id=str(post.id), max_attempts=1,
            )
            DraftPush.objects.filter(id__in=[row.id for row in pushes if row.status == "PENDING"]).update(job=job)
        return str(batch_id), (job.id if job else None), [_out(row) for row in pushes]

    @staticmethod
    def retry(push_id: int, admin):
        row = DraftPush.objects.filter(id=push_id).first()
        if row is None:
            raise NotFound("推送记录不存在")
        if row.mode != "AUTO" or row.status not in {"FAILED", "UNKNOWN"}:
            raise ApiError("DRAFT_PUSH_STATE_INVALID", "该记录不可重试", 409)
        new_row = DraftPush.objects.create(
            post=row.post, account=row.account, platform=row.platform,
            batch_id=uuid.uuid4(), mode="AUTO", status="PENDING",
            unsupported=list(row.unsupported or []), retry_of=row,
            created_by_admin_id=getattr(admin, "id", 0),
            created_by_label=getattr(admin, "username", "")[:64],
        )
        job = JobService.enqueue(
            kind="DRAFT_PUSH", payload={"push_ids": [new_row.id]},
            admin_id=getattr(admin, "id", 0),
            admin_label=getattr(admin, "username", "") or "",
            subject_type="content_post", subject_id=str(row.post_id), max_attempts=1,
        )
        DraftPush.objects.filter(id=new_row.id).update(job=job)
        return job.id, _out(new_row)

    @staticmethod
    def history(post_id: int, *, batch_id=None):
        qs = DraftPush.objects.filter(post_id=post_id).select_related("account")
        if batch_id:
            try:
                qs = qs.filter(batch_id=uuid.UUID(str(batch_id)))
            except (ValueError, TypeError):
                raise ApiError("INVALID_QUERY", "batch_id 不合法", 400)
        return qs.order_by("-created_at", "-id")


class DraftPushHandler:
    kind = "DRAFT_PUSH"
    idempotent = False

    def run(self, ctx: JobContext):
        results = []
        for push_id in ctx.job.payload.get("push_ids", []):
            row = DraftPush.objects.filter(id=push_id).first()
            if row is None or row.status != "PENDING":
                continue
            DraftPush.objects.filter(id=row.id).update(status="SENDING")
            account = row.account
            try:
                adapter = get_draft_adapter(row.platform)
                from .platforms import PlatformAccountService
                credentials = PlatformAccountService.credentials_of(account.id) if account else {}
                payload = DraftPushService.build_payload(row.post, adapter)
                from apps.integrations.draft import DraftPayload
                outcome = adapter.save_draft(
                    DraftPayload(payload.title, payload.html, payload.text, payload.media),
                    credentials)
            except Exception as exc:  # noqa: BLE001
                outcome = None
                error = str(exc)[:500]
            if outcome is None:
                DraftPush.objects.filter(id=row.id).update(
                    status="FAILED", error_code="INTERNAL", error_message=error,
                    finished_at=timezone.now())
                results.append({"platform": row.platform, "status": "FAILED", "error_code": "INTERNAL"})
                continue
            if outcome.status == "SAVED":
                DraftPush.objects.filter(id=row.id).update(
                    status="SAVED", remote_ref=outcome.remote_ref,
                    finished_at=timezone.now())
            elif outcome.status == "AUTH_EXPIRED":
                if account:
                    PlatformAccount.objects.filter(id=account.id).update(auth_status="EXPIRED")
                DraftPush.objects.filter(id=row.id).update(
                    status="FAILED", error_code="AUTH_EXPIRED",
                    error_message="认证已失效，请重新认证", finished_at=timezone.now())
            else:
                DraftPush.objects.filter(id=row.id).update(
                    status="FAILED", error_code=outcome.error_code or "UPSTREAM",
                    error_message=(outcome.message or "")[:500], finished_at=timezone.now())
            results.append({"platform": row.platform, "status": outcome.status,
                            "error_code": outcome.error_code})
        AuditService.record(
            actor=AuditActor("ADMIN", ctx.job.created_by_admin_id, ctx.job.created_by_label),
            action="CONTENT_DRAFT_PUSHED", object_type="content_draft_batch",
            object_id=str(ctx.job.id), result="SUCCESS", detail={"results": results})
        return Done({"results": results})

    def on_interrupted(self, job: ContentJob) -> None:
        now = timezone.now()
        DraftPush.objects.filter(job_id=job.id, status="SENDING").update(
            status="UNKNOWN", error_code="UNKNOWN",
            error_message="结果未知，请到平台草稿箱核对后重试", finished_at=now)
        DraftPush.objects.filter(job_id=job.id, status="PENDING").update(
            status="FAILED", error_code="INTERRUPTED", error_message="任务中断",
            finished_at=now)
