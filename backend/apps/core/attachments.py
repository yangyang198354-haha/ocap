"""附件存取与下载策略（IFC-003/004/005）。"""
import hashlib
import logging
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

logger = logging.getLogger(__name__)

SPECS = {
    "RESOLUTION": {"ext": {"pdf", "jpg", "jpeg", "png", "docx", "xlsx"}, "single": 10 * 1024 * 1024,
                   "count": 10, "total": 50 * 1024 * 1024},
    "APPEAL_PROOF": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 5, "total": None},
    "INVOICE": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 10, "total": None},
    "INCOME_VOUCHER": {"ext": {"jpg", "jpeg", "png", "pdf"}, "single": 10 * 1024 * 1024, "count": 10, "total": None},
    # MOD-156 / REQ-FUNC-257：头像上限 5 MB（前端常量与文案须同步）
    "AVATAR": {"ext": {"jpg", "jpeg", "png"}, "single": 5 * 1024 * 1024, "count": 1, "total": 5 * 1024 * 1024},
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


@dataclass(frozen=True)
class ValidatedUpload:
    """MOD-139 / IFC-346：已通过全部校验、尚未落盘的上传内容。"""
    name: str
    ext: str
    data: bytes
    size: int
    sha256: str


@dataclass
class StoredFile:
    """MOD-139 / IFC-346：已落盘文件，供失败清理。"""
    attachment_id: uuid.UUID
    abs_path: str


class AttachmentService:
    @staticmethod
    def validate_upload(file, purpose: str) -> ValidatedUpload:
        """校验用途、扩展名、大小、魔数；不写磁盘、不写库（IFC-346）。"""
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
        return ValidatedUpload(name=name[:255], ext=ext, data=data, size=size,
                               sha256=hashlib.sha256(data).hexdigest())

    @staticmethod
    def store_validated(item: ValidatedUpload, *, purpose: str, owner,
                        linked_type: str | None = None,
                        linked_id: str | None = None) -> tuple[AttachmentRef, StoredFile]:
        """落盘并建 Attachment；给定 linked_* 时状态直接为 LINKED（不经 TEMP）。"""
        storage = f"{uuid.uuid4().hex}.{item.ext}"
        target_dir = os.path.join(settings.MEDIA_ROOT, purpose.lower())
        os.makedirs(target_dir, exist_ok=True)
        abs_path = os.path.join(target_dir, storage)
        with open(abs_path, "wb") as fh:
            fh.write(item.data)
        stored = StoredFile(attachment_id=uuid.uuid4(), abs_path=abs_path)
        try:
            owner_type = "ADMIN" if getattr(owner, "is_admin_principal", False) else "MEMBER"
            extra = {}
            if linked_type is not None and linked_id is not None:
                extra = {"status": "LINKED", "linked_type": linked_type, "linked_id": str(linked_id)}
            row = Attachment.objects.create(
                id=stored.attachment_id, owner_type=owner_type, owner_id=owner.id, purpose=purpose,
                original_name=item.name, content_type=CONTENT_TYPES.get(item.ext, "application/octet-stream"),
                size=item.size, sha256=item.sha256, storage_path=os.path.join(purpose.lower(), storage),
                **extra,
            )
        except Exception:
            AttachmentService.discard([stored])
            raise
        return AttachmentRef(row.id, row.original_name, row.size, row.content_type), stored

    @staticmethod
    def discard(stored: list[StoredFile]) -> None:
        """删除已落盘文件（忽略不存在）；不抛异常，失败只记日志（IFC-346）。"""
        for item in stored:
            try:
                os.remove(item.abs_path)
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning("清理已落盘文件失败 attachment=%s", item.attachment_id)

    @staticmethod
    def store(*, file, purpose: str, owner) -> AttachmentRef:
        item = AttachmentService.validate_upload(file, purpose)
        ref, _stored = AttachmentService.store_validated(item, purpose=purpose, owner=owner)
        return ref

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
        elif row.purpose == "AVATAR" and principal is not None:
            pass  # IFC-360 / ADR-141：头像对任一已登录成员或管理员可读（视图已限 IsMemberOrAdmin）
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
