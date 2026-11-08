"""附件存取与下载策略（IFC-003/004/005）。"""
import hashlib
import os
import uuid
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone

from .config import SystemConfig as ConfigService
from .errors import ApiError, NotFound
from .models import Attachment

SPECS = {
    "RESOLUTION": {"ext": {"pdf", "jpg", "jpeg", "png", "docx", "xlsx"}, "single": 10 * 1024 * 1024,
                   "count": 10, "total": 50 * 1024 * 1024},
    "APPEAL_PROOF": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 5, "total": None},
    "INVOICE": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 10, "total": None},
    "INCOME_VOUCHER": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 10, "total": None},
    "AVATAR": {"ext": {"jpg", "jpeg", "png"}, "single": 2 * 1024 * 1024, "count": 1, "total": 2 * 1024 * 1024},
}

MAGIC = {
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "pdf": [b"%PDF"],
    "docx": [b"PK\x03\x04"],
    "xlsx": [b"PK\x03\x04"],
}

CONTENT_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class AttachmentPolicy(Protocol):
    def can_open(self, linked_id: str, principal) -> bool: ...


_POLICIES: dict[str, AttachmentPolicy] = {}


def register_attachment_policy(linked_type: str, policy: AttachmentPolicy) -> None:
    _POLICIES[linked_type] = policy


@dataclass
class AttachmentRef:
    id: uuid.UUID
    name: str
    size: int
    content_type: str


class AttachmentService:
    @staticmethod
    def store(*, file, purpose: str, owner) -> AttachmentRef:
        if purpose not in SPECS:
            raise ApiError("FILE_TYPE_NOT_ALLOWED", "不支持的上传用途")
        spec = SPECS[purpose]
        name = os.path.basename(getattr(file, "name", "upload"))
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        data = file.read()
        size = len(data)
        if ext not in spec["ext"]:
            raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件类型不允许")
        if size > spec["single"]:
            raise ApiError("FILE_TOO_LARGE", "文件超过大小上限", 413)
        if not any(data.startswith(m) for m in MAGIC.get(ext, [])):
            raise ApiError("FILE_TYPE_NOT_ALLOWED", "文件内容与扩展名不一致")
        digest = hashlib.sha256(data).hexdigest()
        storage = f"{uuid.uuid4().hex}.{ext}"
        target_dir = os.path.join(settings.MEDIA_ROOT, purpose.lower())
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, storage), "wb") as fh:
            fh.write(data)
        owner_type = "ADMIN" if getattr(owner, "is_admin_principal", False) else "MEMBER"
        row = Attachment.objects.create(
            owner_type=owner_type, owner_id=owner.id, purpose=purpose,
            original_name=name[:255], content_type=CONTENT_TYPES.get(ext, "application/octet-stream"),
            size=size, sha256=digest, storage_path=os.path.join(purpose.lower(), storage),
        )
        return AttachmentRef(row.id, row.original_name, row.size, row.content_type)

    @staticmethod
    def link(attachment_ids, *, linked_type: str, linked_id: str, purpose: str, owner) -> None:
        rows = list(Attachment.objects.filter(id__in=attachment_ids, owner_id=owner.id, purpose=purpose))
        if len(rows) != len(set(attachment_ids)):
            raise ApiError("ATTACHMENT_LIMIT", "附件不存在或不属于本人")
        spec = SPECS[purpose]
        if len(rows) > spec["count"]:
            raise ApiError("ATTACHMENT_LIMIT", "附件数量超过上限")
        if spec["total"] is not None and sum(r.size for r in rows) > spec["total"]:
            raise ApiError("ATTACHMENT_LIMIT", "附件合计大小超过上限")
        now = timezone.now()
        for row in rows:
            if row.status == "LINKED" and row.linked_id != str(linked_id):
                raise ApiError("ATTACHMENT_LIMIT", "附件已被其他对象使用")
            row.status = "LINKED"
            row.linked_type = linked_type
            row.linked_id = str(linked_id)
            row.save(update_fields=["status", "linked_type", "linked_id"])
        _ = now

    @staticmethod
    def open(attachment_id, principal) -> FileResponse:
        row = Attachment.objects.filter(id=attachment_id).first()
        if row is None:
            raise NotFound()
        if row.status == "LINKED":
            policy = _POLICIES.get(row.linked_type or "")
            if policy is None or not policy.can_open(str(row.linked_id), principal):
                raise NotFound()
            if row.linked_type == "resolution" and row.linked_id:
                pass
        else:
            if row.owner_id != getattr(principal, "id", None):
                raise NotFound()
        path = os.path.join(settings.MEDIA_ROOT, row.storage_path)
        if not os.path.exists(path):
            raise NotFound("文件不存在")
        response = FileResponse(open(path, "rb"), content_type=row.content_type)
        response["Content-Disposition"] = f'attachment; filename="{row.original_name}"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


def count_limit(purpose: str) -> int:
    key = {
        "RESOLUTION": "attachment.max_count.resolution",
        "APPEAL_PROOF": "attachment.max_count.appeal",
        "INVOICE": "attachment.max_count.invoice",
        "INCOME_VOUCHER": "attachment.max_count.voucher",
    }.get(purpose)
    return int(ConfigService.get(key)) if key else SPECS[purpose]["count"]


def linked_attachment_list(linked_type: str, linked_id: str) -> list[dict]:
    rows = Attachment.objects.filter(linked_type=linked_type, linked_id=str(linked_id)).order_by("id")
    return [{"id": str(r.id), "name": r.original_name, "size": r.size,
             "content_type": r.content_type} for r in rows]
