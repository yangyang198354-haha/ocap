"""清册视图（IFC-040/041/042）。"""
import csv
import io

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.core.masking import PHONE_RE
from apps.core.permissions import IsAdmin, IsMember
from apps.core.serializers import page_response

from .models import RegistryPhone, RegistryUnit
from .serializers import RegistryUnitAdminSerializer
from .services import RegistryService

IMPORT_COLUMNS = ["楼栋", "单元", "楼层", "户号", "手机号"]


def _clean(value: str) -> str:
    return str(value or "").strip()


class UnitOptionsView(APIView):
    permission_classes = [IsMember]

    def get(self, request):
        building = request.query_params.get("building")
        unit_no = request.query_params.get("unit_no")
        floor = request.query_params.get("floor")
        if unit_no and not building:
            raise ApiError("INVALID_QUERY", "缺少上级参数")
        if floor and not unit_no:
            raise ApiError("INVALID_QUERY", "缺少上级参数")
        return Response(RegistryService.options(building=building, unit_no=unit_no, floor=floor))


class AdminUnitListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = RegistryUnit.objects.prefetch_related("phones").order_by("id")
        q = request.query_params.get("q")
        if q:
            qs = qs.filter(specific_part__icontains=q)
        return page_response(qs, request, RegistryUnitAdminSerializer)

    def post(self, request):
        data = request.data or {}
        _validate_unit_fields(data)
        unit = RegistryUnit.objects.create(
            building=data["building"].strip(), unit_no=data["unit_no"].strip(),
            floor=data["floor"].strip(), room=data["room"].strip(),
        )
        _audit(request, unit, "create")
        return Response(RegistryUnitAdminSerializer(unit).data, status=status.HTTP_201_CREATED)


class AdminUnitDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, unit_id: int):
        unit = RegistryUnit.objects.filter(id=unit_id).first()
        if unit is None:
            raise NotFound("专有部分不存在")
        data = request.data or {}
        _validate_unit_fields({**{"building": unit.building, "unit_no": unit.unit_no,
                                  "floor": unit.floor, "room": unit.room}, **data})
        for field in ("building", "unit_no", "floor", "room"):
            if field in data:
                setattr(unit, field, data[field].strip())
        unit.save()
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


class AdminUnitPhonesView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, unit_id: int):
        unit = RegistryUnit.objects.filter(id=unit_id).first()
        if unit is None:
            raise NotFound("专有部分不存在")
        phones = (request.data or {}).get("phones", [])
        if not isinstance(phones, list) or len(phones) > 10:
            raise ApiError("INVALID_VALUE", "手机号须为不超过 10 个的列表")
        normalized: list[str] = []
        for phone in phones:
            phone = str(phone)
            if not PHONE_RE.match(phone):
                raise ApiError("INVALID_VALUE", "手机号格式不正确")
            if phone not in normalized:
                normalized.append(phone)
        unit.phones.all().delete()
        RegistryPhone.objects.bulk_create([RegistryPhone(unit=unit, phone=p) for p in normalized])
        _audit(request, unit, "phones")
        return Response(RegistryUnitAdminSerializer(unit).data)


class AdminRegistryImportView(APIView):
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if file is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        if file.size > 5 * 1024 * 1024:
            raise ApiError("FILE_TOO_LARGE", "文件超过 5 MB", 413)
        name = (file.name or "").lower()
        if not name.endswith((".csv", ".xlsx")):
            raise ApiError("IMPORT_FILE_INVALID", "仅支持 xlsx 或 csv")
        raw = file.read()
        try:
            rows = _read_csv(raw) if name.endswith(".csv") else _read_xlsx(raw)
        except ImportError as exc:
            raise ApiError("IMPORT_UNAVAILABLE", "服务端缺少 xlsx 解析依赖", 503) from exc
        except Exception as exc:
            raise ApiError("IMPORT_FILE_INVALID", "文件无法解析") from exc
        if len(rows) > 5001:
            raise ApiError("IMPORT_FILE_INVALID", "文件行数超过 5000")
        if not rows:
            raise ApiError("IMPORT_COLUMNS_MISSING", "缺少列", 400, {"columns": IMPORT_COLUMNS})
        header = [_clean(c) for c in rows[0]]
        missing = [c for c in IMPORT_COLUMNS if c not in header]
        if missing:
            raise ApiError("IMPORT_COLUMNS_MISSING", "缺少列", 400, {"columns": missing})
        dry_run = str(request.query_params.get("dry_run", "")).lower() in {"1", "true"} or bool(
            (request.data or {}).get("dry_run")
        )
        index = {c: header.index(c) for c in IMPORT_COLUMNS}
        imported = updated = failed = 0
        errors: list[dict] = []
        for row_no, row in enumerate(rows[1:], start=2):
            values = {c: _clean(row[index[c]]) if index[c] < len(row) else "" for c in IMPORT_COLUMNS}
            reason = _row_error(values)
            if reason:
                failed += 1
                errors.append({"row": row_no, "reason": reason})
                continue
            if dry_run:
                continue
            unit, created = RegistryUnit.objects.get_or_create(
                building=values["楼栋"], unit_no=values["单元"], floor=values["楼层"], room=values["户号"],
                defaults={"specific_part": f"{values['楼栋']}-{values['单元']}-{values['楼层']}-{values['户号']}"},
            )
            for phone in {p.strip() for p in values["手机号"].split(";") if p.strip()}:
                if not PHONE_RE.match(phone):
                    failed += 1
                    errors.append({"row": row_no, "reason": "手机号格式不正确"})
                    continue
                RegistryPhone.objects.get_or_create(unit=unit, phone=phone)
            imported += 1 if created else 0
            updated += 0 if created else 1
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                            action="REGISTRY_IMPORTED", object_type="registry", object_id="import",
                            result="SUCCESS", detail={"imported": imported, "updated": updated,
                                                      "failed": failed, "dry_run": dry_run})
        return Response({"imported": imported, "updated": updated, "failed": failed, "errors": errors})


def _validate_unit_fields(data: dict) -> None:
    for field in ("building", "unit_no", "floor", "room"):
        value = str(data.get(field, ""))
        if not (1 <= len(value.strip()) <= 32) or "-" in value:
            raise ApiError("INVALID_VALUE", f"{field} 须为 1~32 字符且不含 -")


def _row_error(values: dict) -> str | None:
    for field in ("楼栋", "单元", "楼层", "户号"):
        if not values[field] or len(values[field]) > 32:
            return f"{field} 为空或超长"
    if not values["手机号"]:
        return "手机号为空"
    return None


def _read_csv(raw: bytes) -> list[list[str]]:
    text = raw.decode("utf-8-sig")
    return [row for row in csv.reader(io.StringIO(text))]


def _read_xlsx(raw: bytes) -> list[list[str]]:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = []
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        if i > 5000:
            break
        rows.append(["" if cell is None else str(cell) for cell in row])
    workbook.close()
    return rows


def _audit(request, unit: RegistryUnit, change: str) -> None:
    AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.username),
                        action="REGISTRY_UNIT_CHANGED", object_type="registry_unit",
                        object_id=str(unit.id), result="SUCCESS", detail={"change": change})
