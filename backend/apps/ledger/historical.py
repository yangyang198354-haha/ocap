"""历史支出批量导入（MOD-194 / IFC-408~412）：解析、校验、去重、写台账与作废。"""
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.config import SystemConfig
from apps.core.errors import ApiError
from apps.core.limits import INCOME_IMPORT_MAX_ROWS

from .models import HistoricalExpenseBatch, HistoricalExpenseRow
from .services import LedgerService

TEMPLATE_COLUMNS = ("日期", "金额", "支出类别", "用途/事由", "备注")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = INCOME_IMPORT_MAX_ROWS
SOURCE_TYPE = "historical_expense"


@dataclass(frozen=True)
class ParsedRow:
    line_no: int
    occurred_on: date
    amount: Decimal
    category: str
    purpose: str
    remark: str

    @property
    def duplicate_key(self) -> tuple:
        return self.occurred_on, self.amount, self.category, self.purpose


def _parse_date(raw) -> date | None:
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    text = str(raw or "").strip().replace("/", "-")
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_amount(raw) -> Decimal | None:
    try:
        amount = Decimal(str(raw).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    if amount <= 0 or amount > SystemConfig.amount_max() or amount.as_tuple().exponent < -2:
        return None
    return amount


def _validate(values: dict, line_no: int) -> ParsedRow | str:
    occurred_on = _parse_date(values.get("日期"))
    if occurred_on is None:
        return "日期格式不正确"
    if occurred_on > timezone.localdate():
        return "日期不得晚于今天"
    amount = _parse_amount(values.get("金额"))
    if amount is None:
        return "金额须为正数、最多两位小数且不超过系统上限"
    category = str(values.get("支出类别") or "").strip()
    purpose = str(values.get("用途/事由") or "").strip()
    remark = str(values.get("备注") or "").strip()
    if len(category) > 32:
        return "支出类别超长"
    if len(purpose) > 200:
        return "用途/事由超长"
    if len(remark) > 200:
        return "备注超长"
    return ParsedRow(line_no=line_no, occurred_on=occurred_on, amount=amount,
                     category=category, purpose=purpose, remark=remark)


def _read_rows(file_name: str, raw: bytes) -> list[list]:
    name = (file_name or "").lower()
    if name.endswith(".csv"):
        try:
            return [row for row in csv.reader(io.StringIO(raw.decode("utf-8-sig")))]
        except UnicodeDecodeError as exc:
            raise ApiError("IMPORT_FILE_INVALID", "CSV 须为 UTF-8 编码") from exc
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook

        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sheet = workbook[workbook.sheetnames[0]]
        rows = []
        data_rows = 0
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            values = list(row)
            rows.append(values)
            if index == 0:
                continue
            if any(str(cell).strip() for cell in values if cell is not None):
                data_rows += 1
                # 超限必须在解析阶段就判定，避免大表被静默截断（AC-334-04）
                if data_rows > MAX_ROWS:
                    workbook.close()
                    raise ApiError("IMPORT_FILE_INVALID", f"数据行超过 {MAX_ROWS} 行")
        workbook.close()
        return rows
    raise ApiError("IMPORT_FILE_INVALID", "仅支持 xlsx 或 csv 文件")


def build_template(file_type: str = "xlsx") -> tuple[bytes, str]:
    if file_type not in {"xlsx", "csv"}:
        raise ApiError("INVALID_VALUE", "file_type 仅支持 xlsx 或 csv")
    if file_type == "csv":
        buffer = io.StringIO()
        csv.writer(buffer).writerow(TEMPLATE_COLUMNS)
        return ("\ufeff" + buffer.getvalue()).encode("utf-8"), "text/csv; charset=utf-8"
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "历史支出"
    ws.append(TEMPLATE_COLUMNS)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for column, width in {"A": 14, "B": 12, "C": 16, "D": 28, "E": 24}.items():
        ws.column_dimensions[column].width = width
    notes = wb.create_sheet("填写说明")
    for line in (
        "列顺序固定：日期、金额、支出类别、用途/事由、备注；表头不可改名或删除。",
        "日期格式 YYYY-MM-DD（也兼容 YYYY/MM/DD），不得晚于今天；金额大于 0、最多两位小数。",
        "支出类别 ≤32 字，用途/事由 ≤200 字，备注 ≤200 字；日期、金额必填。",
        "支持 xlsx / CSV，文件 ≤5MB、数据行 ≤5000 行。",
        "重复行（日期+金额+支出类别+用途/事由全同）会被跳过；错误行跳过并提示行号。",
        "导入后直接写入台账，不生成报销单或审批待办；如导入错误，请整批作废后重新导入。",
    ):
        notes.append([line])
    notes.column_dimensions["A"].width = 100
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def import_file(*, file_name: str, raw: bytes, user) -> tuple[HistoricalExpenseBatch | None, list[dict], int]:
    if len(raw) > MAX_FILE_BYTES:
        raise ApiError("FILE_TOO_LARGE", "文件超过 5 MB", 413)
    rows = _read_rows(file_name, raw)
    if not rows:
        raise ApiError("IMPORT_FILE_INVALID", "文件没有数据行")
    header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
    missing = [column for column in TEMPLATE_COLUMNS if column not in header]
    if missing:
        raise ApiError("IMPORT_COLUMNS_MISSING", "缺少列", 400, {"columns": missing})
    index = {column: header.index(column) for column in TEMPLATE_COLUMNS}
    data_rows = []
    for line_no, row in enumerate(rows[1:], start=2):
        if not any(str(cell).strip() for cell in row if cell is not None):
            continue
        data_rows.append((line_no, {column: (row[index[column]] if index[column] < len(row) else "")
                                    for column in TEMPLATE_COLUMNS}))
    if len(data_rows) > MAX_ROWS:
        raise ApiError("IMPORT_FILE_INVALID", f"数据行超过 {MAX_ROWS} 行")

    parsed, errors = [], []
    for line_no, values in data_rows:
        result = _validate(values, line_no)
        if isinstance(result, str):
            errors.append({"row": line_no, "reason": "INVALID_FIELD", "detail": result})
        else:
            parsed.append(result)

    existing = set(
        HistoricalExpenseRow.objects.filter(status="IMPORTED", batch__status="IMPORTED")
        .values_list("occurred_on", "amount", "category", "purpose")
    )
    valid = []
    seen = set()
    for row in parsed:
        key = row.duplicate_key
        if key in existing or key in seen:
            errors.append({"row": row.line_no, "reason": "DUPLICATE", "detail": "与已有历史支出或文件内其他行重复"})
        else:
            seen.add(key)
            valid.append(row)

    if not valid:
        return None, errors, len(data_rows)

    with transaction.atomic():
        batch = HistoricalExpenseBatch.objects.create(file_name=file_name[:255], imported_by=user,
                                                      total_rows=len(data_rows))
        imported = 0
        total_amount = Decimal("0.00")
        error_by_line = {item["row"]: item for item in errors}
        valid_by_line = {row.line_no: row for row in valid}
        for line_no, values in data_rows:
            error = error_by_line.get(line_no)
            row = valid_by_line.get(line_no)
            if error is not None:
                HistoricalExpenseRow.objects.create(
                    batch=batch, line_no=line_no, status="DUPLICATE" if error["reason"] == "DUPLICATE" else "ERROR",
                    occurred_on=_parse_date(values.get("日期")), amount=_parse_amount(values.get("金额")),
                    category=str(values.get("支出类别") or "")[:32],
                    purpose=str(values.get("用途/事由") or "")[:200],
                    remark=str(values.get("备注") or "")[:200],
                    error_message=str(error["detail"])[:200],
                )
                continue
            entry = LedgerService.post(
                direction="EXPENSE", amount=row.amount, occurred_on=row.occurred_on,
                entry_type=row.category or "历史支出", summary=row.purpose or None,
                source_type=SOURCE_TYPE, source_id=batch.id, seq=line_no,
            )
            HistoricalExpenseRow.objects.create(
                batch=batch, line_no=line_no, status="IMPORTED", occurred_on=row.occurred_on,
                amount=row.amount, category=row.category, purpose=row.purpose, remark=row.remark,
                ledger_entry=entry,
            )
            imported += 1
            total_amount += row.amount
        duplicate_count = sum(1 for item in errors if item["reason"] == "DUPLICATE")
        batch.imported_rows = imported
        batch.skipped_rows = duplicate_count
        batch.failed_rows = len(errors) - duplicate_count
        batch.total_amount = total_amount
        batch.save(update_fields=["imported_rows", "skipped_rows", "failed_rows", "total_amount"])

    AuditService.record(
        actor=AuditActor("MEMBER", user.id, getattr(user, "identity_label", "")),
        action="HISTORICAL_EXPENSE_IMPORTED", object_type="historical_expense_batch",
        object_id=str(batch.id), result="SUCCESS",
        detail={"file_name": batch.file_name, "total_rows": batch.total_rows,
                "imported_rows": batch.imported_rows, "skipped_rows": batch.skipped_rows,
                "failed_rows": batch.failed_rows, "total_amount": str(batch.total_amount)},
    )
    return batch, errors, len(data_rows)


def void_batch(batch_id: int, *, user, reason: str) -> HistoricalExpenseBatch:
    reason = str(reason or "").strip()
    if not (1 <= len(reason) <= 200):
        raise ApiError("INVALID_VALUE", "作废原因须为 1~200 字符")
    batch = HistoricalExpenseBatch.objects.filter(id=batch_id).first()
    if batch is None:
        raise ApiError("NOT_FOUND", "导入批次不存在", 404)
    if batch.status == "VOIDED":
        raise ApiError("ALREADY_VOIDED", "该批次已作废", 409)
    with transaction.atomic():
        LedgerService.void_by_source(SOURCE_TYPE, batch.id)
        batch.status = "VOIDED"
        batch.voided_by = user
        batch.voided_at = timezone.now()
        batch.void_reason = reason
        batch.save(update_fields=["status", "voided_by", "voided_at", "void_reason"])
    AuditService.record(
        actor=AuditActor("MEMBER", user.id, getattr(user, "identity_label", "")),
        action="HISTORICAL_EXPENSE_VOIDED", object_type="historical_expense_batch",
        object_id=str(batch.id), result="SUCCESS",
        detail={"reason": reason, "imported_rows": batch.imported_rows,
                "total_amount": str(batch.total_amount)},
    )
    return batch
