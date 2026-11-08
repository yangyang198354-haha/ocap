"""收入视图（IFC-100~105）。"""
import csv
import io
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approval.models import ApprovalFlow
from apps.approval.services import ApprovalEngine
from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError
from apps.core.money import money
from apps.core.permissions import IsIncomeMember, IsMember
from apps.core.serializers import page_response

from .models import IncomeRecord, IncomeSheet
from .services import recalculate, void_sheet

COLUMNS = ["日期", "金额", "收入类别", "来源说明", "备注"]
MAX_AMOUNT = Decimal("1000000.00")


def _parse_date(raw) -> object:
    if hasattr(raw, "year"):
        return raw
    text = str(raw).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("日期格式不正确")


def _parse_amount(raw) -> Decimal:
    try:
        amount = Decimal(str(raw).replace(",", "").strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("金额格式不正确") from exc
    if amount <= 0 or amount > MAX_AMOUNT or amount.as_tuple().exponent < -2:
        raise ValueError("金额须为正数、最多两位小数且不超过 1000000")
    return amount


def _record_row(values: dict, line_no: int = 1) -> dict:
    occurred_on = _parse_date(values["日期"])
    category = str(values.get("收入类别", "") or "").strip()
    if len(category) > 32:
        raise ValueError("收入类别超长")
    source_note = str(values.get("来源说明", "") or "").strip()
    if len(source_note) > 200:
        raise ValueError("来源说明超长")
    remark = str(values.get("备注", "") or "").strip()
    if len(remark) > 200:
        raise ValueError("备注超长")
    return {"line_no": line_no, "occurred_on": occurred_on, "amount": _parse_amount(values["金额"]),
            "category": category, "source_note": source_note, "remark": remark}


def _parse_rows(rows: list[list]) -> dict:
    if len(rows) > 5001:
        raise ApiError("IMPORT_FILE_INVALID", "文件行数超过 5000")
    if not rows:
        raise ApiError("IMPORT_COLUMNS_MISSING", "缺少列", 400, {"columns": COLUMNS})
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise ApiError("IMPORT_COLUMNS_MISSING", "缺少列", 400, {"columns": missing})
    index = {c: header.index(c) for c in COLUMNS}
    valid, errors = [], []
    total = 0
    for row_no, row in enumerate(rows[1:], start=2):
        if not any(str(c).strip() for c in row if c is not None):
            continue
        total += 1
        values = {c: (row[index[c]] if index[c] < len(row) else "") for c in COLUMNS}
        try:
            valid.append(_record_row(values, line_no=total))
        except ValueError as exc:
            errors.append({"row": row_no, "reason": str(exc)})
    if total == 0:
        raise ApiError("IMPORT_FILE_INVALID", "文件没有数据行")
    if len(errors) / total > 0.02:
        raise ApiError("IMPORT_ROW_ERRORS", "行级错误超过 2%", 400, {"errors": errors[:100]})
    return {"records": valid, "errors": errors, "total": total}


class IncomeImportView(APIView):
    permission_classes = [IsIncomeMember]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("file")
        if file is None:
            raise ApiError("FILE_REQUIRED", "缺少文件")
        if file.size > 5 * 1024 * 1024:
            raise ApiError("FILE_TOO_LARGE", "文件超过 5 MB", 413)
        name = (file.name or "").lower()
        raw = file.read()
        try:
            rows = _read_csv(raw) if name.endswith(".csv") else _read_xlsx(raw)
        except ImportError as exc:
            raise ApiError("IMPORT_UNAVAILABLE", "服务端缺少 xlsx 解析依赖", 503) from exc
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError("IMPORT_FILE_INVALID", "文件无法解析") from exc
        parsed = _parse_rows(rows)
        title = request.data.get("title") or None
        from apps.committee.services import CommitteeQuery

        with transaction.atomic():
            sheet = IncomeSheet.objects.create(title=title, source="IMPORT",
                                               creator_labels=",".join(
                                                   CommitteeQuery.identity_labels(request.user.id)),
                                               submitted_by=request.user)
            IncomeRecord.objects.bulk_create([IncomeRecord(sheet=sheet, **row)
                                              for row in parsed["records"]])
            recalculate(sheet)
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.identity_label),
                            action="INCOME_IMPORTED", object_type="income_sheet",
                            object_id=str(sheet.id), result="SUCCESS",
                            detail={"rows": parsed["total"], "failed": len(parsed["errors"])})
        return Response({**sheet_view(sheet), "import_summary": {
            "total_rows": parsed["total"], "imported": len(parsed["records"]),
            "failed": len(parsed["errors"]), "errors": parsed["errors"][:100],
        }}, status=status.HTTP_201_CREATED)


def _read_csv(raw: bytes) -> list[list]:
    return [row for row in csv.reader(io.StringIO(raw.decode("utf-8-sig")))]


def _read_xlsx(raw: bytes) -> list[list]:
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = []
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        if i > 5000:
            break
        rows.append(list(row))
    workbook.close()
    return rows


class AdminSheetListView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request):
        qs = IncomeSheet.objects.order_by("-created_at")
        for param in ("status",):
            value = request.query_params.get(param)
            if value:
                qs = qs.filter(**{param: value})
        return page_response(qs, request, SheetSerializer)


class AdminSheetDetailView(APIView):
    permission_classes = [IsIncomeMember]

    def get(self, request, sheet_id: int):
        return Response(sheet_view(_get_sheet(sheet_id)))

    def patch(self, request, sheet_id: int):
        sheet = _get_sheet(sheet_id)
        if sheet.status not in {"DRAFT", "REJECTED", "WITHDRAWN"}:
            raise ApiError("IMMUTABLE", "该收入表不可编辑", 409)
        data = request.data or {}
        rows = data.get("records")
        if rows is None:
            raise ApiError("INVALID_VALUE", "缺少 records")
        total = len(rows)
        valid, errors = [], []
        for idx, raw in enumerate(rows, start=1):
            try:
                valid.append(_record_row(raw, line_no=idx))
            except ValueError as exc:
                errors.append({"row": idx, "reason": str(exc)})
        if total and len(errors) / total > 0.02:
            raise ApiError("IMPORT_ROW_ERRORS", "行级错误超过 2%", 400, {"errors": errors[:100]})
        with transaction.atomic():
            sheet.records.all().delete()
            IncomeRecord.objects.bulk_create([IncomeRecord(sheet=sheet, **row) for row in valid])
            if "title" in data:
                sheet.title = data["title"] or None
            recalculate(sheet)
        return Response({**sheet_view(sheet), "errors": errors})


class SheetSubmitView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, sheet_id: int):
        sheet = _get_sheet(sheet_id)
        if sheet.status != "DRAFT":
            raise ApiError("NOT_SUBMITTABLE", "仅草稿可提交", 409)
        flow = _flow(request.data or {})
        if not sheet.records.exists():
            raise ApiError("INCOME_SHEET_EMPTY", "收入表没有记录", 409)
        recalculate(sheet)
        with transaction.atomic():
            instance = ApprovalEngine.submit(scope="INCOME", subject_type="income_sheet",
                                             subject_id=sheet.id, flow_id=flow.id,
                                             submitter=request.user)
            sheet.status = "PENDING"
            sheet.approval_instance_id = instance.id
            sheet.save(update_fields=["status", "approval_instance_id"])
        AuditService.record(actor=AuditActor("ADMIN", request.user.id, request.user.identity_label),
                            action="INCOME_SUBMITTED", object_type="income_sheet",
                            object_id=str(sheet.id), result="SUCCESS")
        return Response(sheet_view(sheet))


class SheetResubmitView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, sheet_id: int):
        sheet = _get_sheet(sheet_id)
        if sheet.status not in {"REJECTED", "WITHDRAWN"}:
            raise ApiError("NOT_RESUBMITTABLE", "当前状态不可重新提交", 409)
        flow = _flow(request.data or {})
        if not sheet.records.exists():
            raise ApiError("INCOME_SHEET_EMPTY", "收入表没有记录", 409)
        recalculate(sheet)
        with transaction.atomic():
            sheet.status = "PENDING"
            sheet.revision += 1
            sheet.decided_at = None
            sheet.save(update_fields=["status", "revision", "decided_at"])
            instance = ApprovalEngine.resubmit(scope="INCOME", subject_type="income_sheet",
                                               subject_id=sheet.id, flow_id=flow.id,
                                               submitter=sheet.submitted_by, revision=sheet.revision)
            sheet.approval_instance_id = instance.id
            sheet.save(update_fields=["approval_instance_id"])
        return Response(sheet_view(sheet))


class SheetWithdrawView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, sheet_id: int):
        sheet = _get_sheet(sheet_id)
        if sheet.status != "PENDING":
            raise ApiError("ALREADY_DECIDED", "该收入表已处理", 409)
        if sheet.submitted_by_id != request.user.id:
            raise ApiError("FORBIDDEN", "仅提交人可撤回", 403)
        instance = ApprovalEngine.pending_instance("income_sheet", sheet.id)
        if instance is None:
            raise ApiError("NOT_FOUND", "审批实例不存在", 404)
        ApprovalEngine.withdraw(instance.id, request.user)
        sheet.refresh_from_db()
        return Response(sheet_view(sheet))


class SheetVoidView(APIView):
    permission_classes = [IsIncomeMember]

    def post(self, request, sheet_id: int):
        sheet = void_sheet(sheet_id, request.user)
        return Response(sheet_view(sheet))


class IncomeSheetListView(APIView):
    # DEF-002：已生效收入表对所有登录用户可见，录入/审批入口仍在 admin 视图。
    permission_classes = [IsMember]

    def get(self, request):
        qs = IncomeSheet.objects.filter(status="EFFECTIVE").order_by("-period_start", "-id")
        period_start = request.query_params.get("period_start")
        period_end = request.query_params.get("period_end")
        if period_start:
            qs = qs.filter(period_end__gte=period_start)
        if period_end:
            qs = qs.filter(period_start__lte=period_end)
        return page_response(qs, request, SheetSerializer)


class IncomeSheetDetailView(APIView):
    # DEF-002：已生效收入表明细对所有登录用户可见。
    permission_classes = [IsMember]

    def get(self, request, sheet_id: int):
        sheet = _get_sheet(sheet_id)
        if sheet.status != "EFFECTIVE":
            raise ApiError("FORBIDDEN", "无权查看", 403)
        return Response(sheet_detail_view(sheet))


class SheetSerializer:
    def __init__(self, rows, many=False, context=None):
        rows = rows if many else [rows]
        self.data = [sheet_view(r) for r in rows]


def sheet_view(sheet: IncomeSheet) -> dict:
    return {
        "id": sheet.id, "title": sheet.title, "source": sheet.source,
        "period_start": sheet.period_start, "period_end": sheet.period_end,
        "total_amount": money(sheet.total_amount), "status": sheet.status,
        "submitted_by": sheet.submitted_by_id, "created_at": sheet.created_at,
        "decided_at": sheet.decided_at,
    }


def sheet_detail_view(sheet: IncomeSheet) -> dict:
    return {**sheet_view(sheet), "records": [{
        "id": r.id, "line_no": r.line_no, "occurred_on": r.occurred_on,
        "amount": money(r.amount), "category": r.category, "source_note": r.source_note,
        "remark": r.remark,
    } for r in sheet.records.all()]}


def _get_sheet(sheet_id: int) -> IncomeSheet:
    sheet = IncomeSheet.objects.filter(id=sheet_id).first()
    if sheet is None:
        raise ApiError("NOT_FOUND", "收入表不存在", 404)
    return sheet


def _flow(data: dict) -> ApprovalFlow:
    try:
        return ApprovalFlow.objects.get(id=int(data.get("approval_flow_id")), scope="INCOME",
                                        is_active=True)
    except (TypeError, ValueError, ApprovalFlow.DoesNotExist) as exc:
        raise ApiError("INVALID_VALUE", "审批流程不可用") from exc


_ = (uuid, timezone)
