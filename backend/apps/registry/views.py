"""清册视图（MOD-032 / IFC-152~159）。"""
import time
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.core.masking import PHONE_RE
from apps.core.permissions import IsAdmin, IsMember
from apps.core.serializers import page_response

from .import_spec import (
    MAX_FILE_BYTES,
    parse_area,
    spec_payload,
    time_budget_seconds,
    validate_unit_fields,
)
from .import_template import build_csv, build_xlsx
from .importing import Deadline, apply_plan, plan_import, read_rows
from .models import UNIT_TYPE_CHOICES, RegistryOwner, RegistryPhone, RegistryUnit, build_specific_part
from .serializers import RegistryUnitAdminSerializer
from .services import RegistryService

UNIT_TYPE_CODES = {code for code, _ in UNIT_TYPE_CHOICES}
OWNER_NAME_LIMIT = 64


def _clean(value: object) -> str:
    return str(value if value is not None else "").strip()


def _area_value(value: object) -> tuple[Decimal | None, str | None]:
    """返回 (面积, 错误文案)；None 表示清除/未填。"""
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, "专有部分面积格式不正确"
    if isinstance(value, (int, float, Decimal)):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        return None, "专有部分面积格式不正确"
    area, _ = parse_area(text)
    if area is None:
        return None, "专有部分面积格式不正确"
    return area, None


class UnitOptionsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        levels = {}
        for key in ("building", "unit_no", "floor"):
            value = request.query_params.get(key)
            if value is not None and len(value) > 32:
                raise ApiError("INVALID_QUERY", f"{key} 过长（最多 32 字符）")
            levels[key] = value
        if levels["unit_no"] is not None and levels["building"] is None:
            raise ApiError("INVALID_QUERY", "缺少上级参数")
        if levels["floor"] is not None and levels["unit_no"] is None:
            raise ApiError("INVALID_QUERY", "缺少上级参数")
        return Response(RegistryService.options(**levels))


class AdminUnitListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = RegistryUnit.objects.prefetch_related("owners__phones").order_by("id")
        q = request.query_params.get("q")
        if q:
            if len(q) > 64:
                raise ApiError("INVALID_QUERY", "q 过长（最多 64 字符）")
            qs = qs.filter(specific_part__icontains=q)
        unit_type = request.query_params.get("unit_type")
        if unit_type is not None:
            if unit_type == "UNSET":
                qs = qs.filter(unit_type__isnull=True)
            elif unit_type in UNIT_TYPE_CODES:
                qs = qs.filter(unit_type=unit_type)
            else:
                raise ApiError("INVALID_QUERY", "unit_type 取值不合法")
        return page_response(qs, request, RegistryUnitAdminSerializer)

    def post(self, request):
        data = request.data or {}
        fields = {
            "building": _clean(data.get("building")),
            "unit_no": _clean(data.get("unit_no")),
            "floor": _clean(data.get("floor")),
            "room": _clean(data.get("room")),
        }
        error = validate_unit_fields(**fields)
        if error:
            raise ApiError("INVALID_VALUE", error)

        unit_type = data.get("unit_type")
        if unit_type not in UNIT_TYPE_CODES:
            raise ApiError("INVALID_VALUE", "请选择专有部分类型")
        area, area_error = _area_value(data.get("area"))
        if area_error:
            raise ApiError("INVALID_VALUE", area_error)
        if unit_type == "PARKING" and area is None:
            raise ApiError("INVALID_VALUE", "车位须填写专有部分面积")

        specific_part = build_specific_part(**fields)
        if RegistryUnit.objects.filter(specific_part=specific_part).exists():
            raise ApiError("UNIT_EXISTS", "专有部分已存在", 409)
        try:
            unit = RegistryUnit.objects.create(**fields, unit_type=unit_type, area=area)
        except IntegrityError as exc:
            raise ApiError("UNIT_EXISTS", "专有部分已存在", 409) from exc
        _audit(request, unit, "create")
        return Response(RegistryUnitAdminSerializer(unit).data, status=status.HTTP_201_CREATED)


class AdminUnitDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, unit_id: int):
        unit = RegistryUnit.objects.filter(id=unit_id).first()
        if unit is None:
            raise NotFound("专有部分不存在")
        data = request.data or {}

        merged = {
            "building": _clean(data.get("building")) if "building" in data else unit.building,
            "unit_no": _clean(data.get("unit_no")) if "unit_no" in data else unit.unit_no,
            "floor": _clean(data.get("floor")) if "floor" in data else unit.floor,
            "room": _clean(data.get("room")) if "room" in data else unit.room,
        }
        error = validate_unit_fields(**merged)
        if error:
            raise ApiError("INVALID_VALUE", error)

        unit_type = unit.unit_type
        if "unit_type" in data:
            unit_type = data.get("unit_type")
            if unit_type not in UNIT_TYPE_CODES:
                raise ApiError("INVALID_VALUE", "请选择专有部分类型")
        area = unit.area
        if "area" in data:
            area, area_error = _area_value(data.get("area"))
            if area_error:
                raise ApiError("INVALID_VALUE", area_error)
        if unit_type == "PARKING" and area is None:
            raise ApiError("INVALID_VALUE", "车位须填写专有部分面积")

        specific_part = build_specific_part(**merged)
        if RegistryUnit.objects.exclude(id=unit.id).filter(specific_part=specific_part).exists():
            raise ApiError("UNIT_EXISTS", "专有部分已存在", 409)

        for field, value in merged.items():
            setattr(unit, field, value)
        unit.unit_type = unit_type
        unit.area = area
        try:
            unit.save()
        except IntegrityError as exc:
            raise ApiError("UNIT_EXISTS", "专有部分已存在", 409) from exc
        _audit(request, unit, "update")
        return Response(RegistryUnitAdminSerializer(unit).data)

    def delete(self, request, unit_id: int):
        unit = RegistryUnit.objects.filter(id=unit_id).first()
        if unit is None:
            raise NotFound("专有部分不存在")
        from apps.residency.models import Membership

        if Membership.objects.filter(unit_id=unit_id, ended_at__isnull=True).exists():
            raise ApiError("UNIT_IN_USE", "该专有部分仍有有效成员，不能删除", 409)
        _audit(request, unit, "delete")
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUnitOwnersView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, unit_id: int):
        with transaction.atomic():
            unit = RegistryUnit.objects.select_for_update().filter(id=unit_id).first()
            if unit is None:
                raise NotFound("专有部分不存在")

            payload = request.data.get("owners") if isinstance(request.data, dict) else None
            if not isinstance(payload, list):
                raise ApiError("INVALID_VALUE", "业主列表格式不正确")

            existing = {owner.id: owner for owner in unit.owners.all()}
            prepared = self._prepare(payload, existing)

            keep_ids = {owner_id for owner_id, _, _ in prepared if owner_id is not None}
            RegistryOwner.objects.filter(id__in=[oid for oid in existing if oid not in keep_ids]).delete()

            renames = [
                owner_id for owner_id, name, _ in prepared
                if owner_id is not None and name is not None and existing[owner_id].name != name
            ]
            for owner_id in renames:
                RegistryOwner.objects.filter(id=owner_id).update(name=None)

            RegistryPhone.objects.filter(unit=unit).delete()

            phones: list[RegistryPhone] = []
            for owner_id, name, owner_phones in prepared:
                if owner_id is None:
                    owner = RegistryOwner.objects.create(unit=unit, name=name)
                else:
                    owner = existing[owner_id]
                    if owner.name != name:
                        owner.name = name
                        owner.save(update_fields=["name", "updated_at"])
                phones.extend(RegistryPhone(unit=unit, owner=owner, phone=phone) for phone in owner_phones)
            if phones:
                RegistryPhone.objects.bulk_create(phones, batch_size=500)

            _audit(request, unit, "owners", extra={"owner_count": len(prepared)})
            unit.refresh_from_db()
            return Response(RegistryUnitAdminSerializer(unit).data)

    @staticmethod
    def _prepare(payload: list, existing: dict) -> list[tuple[int | None, str | None, list[str]]]:
        prepared: list[tuple[int | None, str | None, list[str]]] = []
        seen_ids: set[int] = set()
        names: dict[str, int] = {}
        phone_owner: dict[str, int] = {}

        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise ApiError("INVALID_VALUE", "业主条目格式不正确")
            owner_id = item.get("id")
            if owner_id is not None:
                if not isinstance(owner_id, int) or isinstance(owner_id, bool) or owner_id not in existing:
                    raise ApiError("INVALID_VALUE", "业主不属于该专有部分")
                if owner_id in seen_ids:
                    raise ApiError("INVALID_VALUE", "业主重复")
                seen_ids.add(owner_id)

            raw_name = item.get("name")
            name = None if raw_name is None else str(raw_name).strip()
            if not name:
                if owner_id is None or existing[owner_id].name is not None:
                    raise ApiError("INVALID_VALUE", "业主姓名不能为空")
                name = None
            else:
                if len(name) > OWNER_NAME_LIMIT:
                    raise ApiError("INVALID_VALUE", f"业主姓名过长（最多 {OWNER_NAME_LIMIT} 字符）")
                key = name.casefold()
                if key in names:
                    raise ApiError("OWNER_NAME_DUPLICATE", "业主姓名重复", 400, {"index": index})
                names[key] = index

            raw_phones = item.get("phones")
            if raw_phones is None:
                raw_phones = []
            if not isinstance(raw_phones, list):
                raise ApiError("INVALID_VALUE", "手机号列表格式不正确")
            phones: list[str] = []
            for value in raw_phones:
                phone = _clean(value)
                if not PHONE_RE.match(phone):
                    raise ApiError("INVALID_VALUE", "手机号格式不正确")
                if phone in phones:
                    continue
                if phone in phone_owner:
                    raise ApiError("PHONE_DUPLICATE_IN_UNIT", "手机号已登记给同一专有部分的另一位业主",
                                   400, {"index": index})
                phone_owner[phone] = index
                phones.append(phone)
            prepared.append((owner_id, name, phones))
        return prepared


class AdminRegistryImportView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        started = time.monotonic()
        deadline = Deadline(time_budget_seconds())

        file = request.FILES.get("file")
        if file is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        if file.size > MAX_FILE_BYTES:
            raise ApiError("FILE_TOO_LARGE", "文件超过 5 MB", 413)
        name = (file.name or "").lower()
        if not name.endswith((".csv", ".xlsx")):
            raise ApiError("IMPORT_FILE_INVALID", "仅支持 xlsx 或 csv")

        dry_run = str(request.query_params.get("dry_run", "")).lower() in {"1", "true"} or str(
            (request.data or {}).get("dry_run", "")
        ).lower() in {"1", "true"}
        rows = read_rows(name, file.read(), deadline)
        plan = plan_import(rows, deadline)
        if not dry_run:
            apply_plan(plan, deadline)

        result = plan.summary()
        result["dry_run"] = dry_run
        result["elapsed_ms"] = int((time.monotonic() - started) * 1000)
        AuditService.record(
            actor=AuditActor("ADMIN", request.user.id, request.user.username),
            action="REGISTRY_IMPORTED", object_type="registry", object_id="import", result="SUCCESS",
            detail={"imported": result["imported"], "updated": result["updated"],
                    "failed": result["failed"], "rows_total": result["rows_total"],
                    "owners_created": result["owners_created"],
                    "phones_created": result["phones_created"], "dry_run": dry_run},
        )
        return Response(result)


class AdminRegistryTemplateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        file_type = request.query_params.get("file_type", "xlsx")
        if file_type not in {"xlsx", "csv"}:
            raise ApiError("INVALID_QUERY", "file_type 只能为 xlsx 或 csv")
        try:
            if file_type == "csv":
                body = build_csv()
                content_type = "text/csv; charset=utf-8"
            else:
                body = build_xlsx()
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except ImportError as exc:
            raise ApiError("IMPORT_UNAVAILABLE", "服务器缺少表格生成组件", 503) from exc
        response = HttpResponse(body, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="registry_import_template.{file_type}"'
        return response


class AdminRegistrySpecView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(spec_payload())


def _audit(request, unit: RegistryUnit, change: str, extra: dict | None = None) -> None:
    detail = {"change": change}
    if extra:
        detail.update(extra)
    AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                        action="REGISTRY_UNIT_CHANGED", object_type="registry_unit",
                        object_id=str(unit.id), result="SUCCESS", detail=detail)
