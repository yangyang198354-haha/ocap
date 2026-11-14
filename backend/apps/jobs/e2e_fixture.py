# MOD-081 / implements IFC-278 / depends 各 app 模型（registry 只读）
"""E2E 夹具：创建 / 查看 / 清理 e2e_ 前缀测试数据。不写 RegistryUnit / RegistryOwner / RegistryPhone。"""
import os
from typing import TypedDict

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Exists, OuterRef, ProtectedError
from django.utils import timezone

from apps.accounts.models import AdminAccount, AuthToken, User
from apps.accounts.services import _new_account_no, validate_password
from apps.approval.models import ApprovalAction, ApprovalFlow, ApprovalInstance, FlowApprover
from apps.claims.models import Claim
from apps.committee.models import Seat
from apps.committee.services import add_months
from apps.content.models import ContentPost, StyleTemplate
from apps.core.config import SystemConfig
from apps.core.masking import mask_phone
from apps.core.models import Attachment
from apps.income.models import IncomeRecord, IncomeSheet
from apps.ledger.models import LedgerEntry
from apps.polls.models import Poll
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal, Membership, ResidentApplication
from apps.resolutions.models import Resolution, Vote

E2E_PREFIX: str = "e2e_"
E2E_PHONE_PREFIX: str = "1990000"  # 预留号段，后 4 位序号
ENV_GATE = "OCAP_E2E_FIXTURE"
ENV_PASSWORD = "OCAP_E2E_PASSWORD"
BATCH = 200
SEAT_POSITIONS = {"MEMBER": "委员", "REPRESENTATIVE": "业主代表"}

# key, 昵称, 手机后 4 位, 房屋关系 [(unit_key, role, source)], 席位
USER_SPECS: list[tuple] = [
    ("e2e_owner_a", "0001", [("U1", "HEAD", "APPEAL")], None),
    ("e2e_owner_b", "0002", [("U1", "OWNER", "APPEAL")], None),
    ("e2e_resident", "0003", [("U1", "RESIDENT", "APPLICATION")], None),
    ("e2e_applicant", "0004", [], None),
    ("e2e_guest", "0005", [], None),
    ("e2e_other_head", "0006", [("U2", "HEAD", "APPEAL")], None),
    ("e2e_multi", "0007", [("U3", "HEAD", "APPEAL"), ("U2", "RESIDENT", "APPLICATION")], None),
    ("e2e_member", "0008", [("U3", "OWNER", "APPEAL")], "MEMBER"),
    ("e2e_member2", "0009", [("U3", "OWNER", "APPEAL")], "MEMBER"),
    ("e2e_rep", "0010", [("U2", "OWNER", "APPEAL")], "REPRESENTATIVE"),
]
HEAD_ANCHORS = {"U1": "e2e_owner_a", "U2": "e2e_other_head", "U3": "e2e_multi"}


class FixtureError(Exception):
    """夹具失败；returncode 2 表示账本保护。"""

    def __init__(self, message: str, returncode: int = 1):
        super().__init__(message)
        self.returncode = returncode


class SetupReport(TypedDict):
    accounts: list[dict[str, object]]
    units: list[dict[str, object]]
    flows: list[dict[str, object]]
    registry_counts: dict[str, int]


def gate_enabled() -> bool:
    return os.environ.get(ENV_GATE) == "1"


def registry_counts() -> dict[str, int]:
    return {"RegistryUnit": RegistryUnit.objects.count(), "RegistryOwner": RegistryOwner.objects.count(),
            "RegistryPhone": RegistryPhone.objects.count()}


def _phone(suffix: str) -> str:
    return f"{E2E_PHONE_PREFIX}{suffix}"


def _e2e_users():
    return User.objects.filter(nickname__startswith=E2E_PREFIX, phone__startswith=E2E_PHONE_PREFIX)


def _check_phone_conflicts() -> None:
    """预留号段被未归属 e2e_ 的用户占用，或 e2e_ 昵称对应的手机不在号段内 → 报错（双条件）。"""
    stray = (User.objects.filter(phone__startswith=E2E_PHONE_PREFIX)
             .exclude(nickname__startswith=E2E_PREFIX))
    if stray.exists():
        raise FixtureError(f"预留号段 {E2E_PHONE_PREFIX}xxxx 已被非 e2e_ 用户占用：{stray.count()} 个")
    odd = User.objects.filter(nickname__startswith=E2E_PREFIX).exclude(phone__startswith=E2E_PHONE_PREFIX)
    if odd.exists():
        raise FixtureError(f"存在昵称以 {E2E_PREFIX} 开头但手机号不在预留号段的用户：{odd.count()} 个")


def _free_units(limit: int, exclude_ids: set[int]) -> list[RegistryUnit]:
    """只读选房：住宅类、无有效房屋关系、无待审申诉/同住人申请，按 id 升序。"""
    active = Membership.objects.filter(unit=OuterRef("pk"), ended_at__isnull=True)
    appeals = Appeal.objects.filter(unit=OuterRef("pk"), status="PENDING")
    apps = ResidentApplication.objects.filter(unit=OuterRef("pk"), status="PENDING")
    qs = (RegistryUnit.objects.filter(unit_type="RESIDENCE")
          .filter(~Exists(active), ~Exists(appeals), ~Exists(apps)).order_by("id"))
    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)
    return list(qs[:limit])


def _existing_anchor_units() -> dict[str, RegistryUnit]:
    found: dict[str, RegistryUnit] = {}
    for key, nickname in HEAD_ANCHORS.items():
        row = (Membership.objects.filter(user__nickname=nickname, user__phone__startswith=E2E_PHONE_PREFIX,
                                         role="HEAD", ended_at__isnull=True)
               .select_related("unit").first())
        if row is not None:
            found[key] = row.unit
    return found


def setup(*, units: int, bulk_users: int, bulk_resolutions: int, password: str) -> SetupReport:
    validate_password(password)
    before = registry_counts()
    with transaction.atomic():
        _check_phone_conflicts()
        anchors = _existing_anchor_units()
        missing_keys = [k for k in ("U1", "U2", "U3") if k not in anchors]
        extra_n = max(units - 3, 0)
        fresh = _free_units(len(missing_keys) + extra_n, {u.id for u in anchors.values()})
        if len(fresh) < len(missing_keys) + extra_n:
            raise FixtureError(
                f"可选房屋不足：需要 {len(missing_keys) + extra_n} 个无有效房屋关系的住宅，仅找到 {len(fresh)} 个")
        for key in missing_keys:
            anchors[key] = fresh.pop(0)
        extra_units = fresh  # 第 4 个起：空闲房屋，只报告，不建立任何关系

        admin, _ = AdminAccount.objects.get_or_create(
            username="e2e_admin", defaults={"password": make_password(password)})
        hashed = make_password(password)
        today = timezone.localdate()
        users: dict[str, User] = {}
        accounts: list[dict[str, object]] = [
            {"key": "e2e_admin", "kind": "admin", "username": admin.username, "roles": ["admin"]}]

        def ensure_user(nickname: str, phone: str) -> User:
            user = User.objects.filter(phone=phone).first()
            if user is None:
                user = User.objects.create(account_no=_new_account_no(), phone=phone,
                                           nickname=nickname, password=hashed)
            return user

        for nickname, suffix, relations, seat in USER_SPECS:
            user = ensure_user(nickname, _phone(suffix))
            users[nickname] = user
            roles = []
            for unit_key, role, source in relations:
                unit = anchors[unit_key]
                if not Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists():
                    Membership.objects.create(user=user, unit=unit, role=role, source=source, active_slot=1,
                                              head_slot=1 if role == "HEAD" else None)
                roles.append(f"{unit_key}:{role}")
            if seat and not Seat.objects.filter(user=user, status="ACTIVE").exists():
                Seat.objects.create(user=user, position=seat, term_start=today,
                                    term_end=add_months(today, 12), status="ACTIVE",
                                    granted_by_admin_id=admin.id, active_slot=1)
            if seat:
                roles.append(f"seat:{seat}")
            accounts.append({"key": nickname, "kind": "member", "account_no": user.account_no,
                             "nickname": nickname, "phone_masked": mask_phone(user.phone), "roles": roles})

        for n in range(1, bulk_users + 1):
            nickname = f"e2e_bulk_{n:02d}"
            user = ensure_user(nickname, _phone(f"{1000 + n}"))
            accounts.append({"key": nickname, "kind": "member", "account_no": user.account_no,
                             "nickname": nickname, "phone_masked": mask_phone(user.phone), "roles": []})

        flows: list[dict[str, object]] = []
        for name, scope in (("e2e_flow_expense", "EXPENSE"), ("e2e_flow_resolution", "RESOLUTION")):
            flow = ApprovalFlow.objects.filter(name=name).first()
            if flow is None:
                flow = ApprovalFlow.objects.create(scope=scope, name=name, mode="DESIGNATED", is_active=True)
                FlowApprover.objects.create(flow=flow, user=users["e2e_member2"])
            flows.append({"id": flow.id, "scope": flow.scope, "name": flow.name})

        initiator = users["e2e_member"]
        for n in range(1, bulk_resolutions + 1):
            title = f"e2e_决议{n:02d}"
            if not Resolution.objects.filter(title=title, initiator=initiator).exists():
                Resolution.objects.create(title=title, content="e2e 夹具数据", initiator=initiator,
                                          initiator_labels=["委员"], status="APPROVED",
                                          approval_mode="DESIGNATED", decided_at=timezone.now())

        unit_report = [{"key": key, "unit_id": anchors[key].id, "specific_part": anchors[key].specific_part}
                       for key in ("U1", "U2", "U3")]
        unit_report += [{"key": f"U{i}", "unit_id": u.id, "specific_part": u.specific_part}
                        for i, u in enumerate(extra_units, start=4)]
    after = registry_counts()
    if after != before:  # 防御：夹具不应改变清册
        raise FixtureError(f"清册行数发生变化：{before} → {after}")
    return {"accounts": accounts, "units": unit_report, "flows": flows, "registry_counts": after}


def _scope() -> dict[str, object]:
    """按双条件圈定 e2e 数据范围；任一不满足即中止。"""
    _check_phone_conflicts()
    users = list(_e2e_users().values_list("id", flat=True))
    admins = list(AdminAccount.objects.filter(username__startswith=E2E_PREFIX).values_list("id", flat=True))
    return {
        "users": users,
        "admins": admins,
        "flows": list(ApprovalFlow.objects.filter(name__startswith=E2E_PREFIX).values_list("id", flat=True)),
        "styles": list(StyleTemplate.objects.filter(name__startswith=E2E_PREFIX,
                                                    created_by_admin_id__in=admins)
                       .values_list("id", flat=True)),
        "posts": list(ContentPost.objects.filter(title__startswith=E2E_PREFIX,
                                                 created_by_admin_id__in=admins).values_list("id", flat=True)),
    }


def _counts(scope: dict[str, object]) -> dict[str, int]:
    users, admins = scope["users"], scope["admins"]
    return {
        "users": len(users), "admins": len(admins), "flows": len(scope["flows"]),
        "style_templates": len(scope["styles"]), "content_posts": len(scope["posts"]),
        "memberships": Membership.objects.filter(user_id__in=users).count(),
        "seats": Seat.objects.filter(user_id__in=users).count(),
        "appeals": Appeal.objects.filter(user_id__in=users).count(),
        "resident_applications": ResidentApplication.objects.filter(applicant_id__in=users).count(),
        "claims": Claim.objects.filter(submitter_id__in=users).count(),
        "income_sheets": IncomeSheet.objects.filter(submitted_by_id__in=users).count(),
        "polls": Poll.objects.filter(creator_id__in=users).count(),
        "resolutions": Resolution.objects.filter(initiator_id__in=users).count(),
        "votes": Vote.objects.filter(voter_id__in=users).count(),
        "approval_instances": ApprovalInstance.objects.filter(submitter_id__in=users).count(),
        "attachments": (Attachment.objects.filter(owner_type="MEMBER", owner_id__in=users).count()
                        + Attachment.objects.filter(owner_type="ADMIN", owner_id__in=admins).count()),
        "tokens": (AuthToken.objects.filter(user_id__in=users).count()
                   + AuthToken.objects.filter(admin_id__in=admins).count()),
    }


def _ledger_conflicts(scope: dict[str, object]) -> list[dict[str, object]]:
    users = scope["users"]
    claim_ids = list(Claim.objects.filter(submitter_id__in=users).values_list("id", flat=True))
    record_ids = list(IncomeRecord.objects.filter(sheet__submitted_by_id__in=users)
                      .values_list("id", flat=True))
    rows = list(LedgerEntry.objects.filter(source_type="claim", source_id__in=claim_ids)
                .values("id", "source_type", "source_id", "status"))
    for chunk in _chunks(record_ids):
        rows += list(LedgerEntry.objects.filter(source_type="income_record", source_id__in=chunk)
                     .values("id", "source_type", "source_id", "status"))
    return rows


def _chunks(ids: list[int], size: int = BATCH):
    for i in range(0, len(ids), size):
        yield ids[i:i + size]


def _delete(model, ids: list[int], field: str = "id__in") -> int:
    total = 0
    for chunk in _chunks(ids):
        deleted, _ = model.objects.filter(**{field: chunk}).delete()
        total += deleted
    return total


def status() -> dict[str, object]:
    scope = _scope()
    return {"e2e": _counts(scope), "registry_counts": registry_counts(),
            "claim_amount_max": f"{SystemConfig.amount_max():.2f}"}


def cleanup(*, execute: bool) -> dict[str, object]:
    scope = _scope()
    users, admins = scope["users"], scope["admins"]
    counts = _counts(scope)
    conflicts = _ledger_conflicts(scope)
    if conflicts:
        raise FixtureError("存在属于 e2e 用户的账本分录，未删除任何数据，请人工处理："
                           + ", ".join(f"{c['source_type']}#{c['source_id']}(entry {c['id']})"
                                       for c in conflicts[:20]), returncode=2)
    foreign = Resolution.objects.filter(initiator_id__in=users).exclude(title__startswith=E2E_PREFIX)
    if foreign.exists():
        raise FixtureError(f"e2e 用户发起了标题不以 {E2E_PREFIX} 开头的决议 {foreign.count()} 条，已中止")
    if not execute:
        return {"executed": False, "would_delete": counts, "registry_counts": registry_counts()}
    before = registry_counts()
    files: list[str] = []
    deleted: dict[str, int] = {}
    try:
        with transaction.atomic():
            deleted["tokens"] = (_delete(AuthToken, users, "user_id__in")
                                 + _delete(AuthToken, admins, "admin_id__in"))
            attachments = (Attachment.objects.filter(owner_type="MEMBER", owner_id__in=users)
                           | Attachment.objects.filter(owner_type="ADMIN", owner_id__in=admins))
            files = list(attachments.values_list("storage_path", flat=True))
            att_ids = list(attachments.values_list("id", flat=True))
            deleted["attachments"] = _delete(Attachment, att_ids)
            deleted["approval_actions"] = _delete(ApprovalAction, users, "actor_id__in")
            deleted["approval_instances"] = _delete(ApprovalInstance, users, "submitter_id__in")
            deleted["claims"] = _delete(Claim, users, "submitter_id__in")
            deleted["income_sheets"] = _delete(IncomeSheet, users, "submitted_by_id__in")
            deleted["polls"] = _delete(Poll, users, "creator_id__in")
            deleted["votes"] = _delete(Vote, users, "voter_id__in")
            res_ids = list(Resolution.objects.filter(initiator_id__in=users, title__startswith=E2E_PREFIX)
                           .values_list("id", flat=True))
            deleted["resolutions"] = _delete(Resolution, res_ids)
            deleted["appeals"] = _delete(Appeal, users, "user_id__in")
            deleted["resident_applications"] = _delete(ResidentApplication, users, "applicant_id__in")
            deleted["memberships"] = _delete(Membership, users, "user_id__in")
            deleted["seats"] = _delete(Seat, users, "user_id__in")
            deleted["flows"] = _delete(FlowApprover, scope["flows"], "flow_id__in") \
                + _delete(ApprovalFlow, scope["flows"])
            deleted["style_templates"] = _delete(StyleTemplate, scope["styles"])
            deleted["content_posts"] = _delete(ContentPost, scope["posts"])
            deleted["users"] = _delete(User, users)
            deleted["admins"] = _delete(AdminAccount, admins)
            if registry_counts() != before:
                raise FixtureError("清册行数发生变化，已回滚")
    except ProtectedError as exc:
        raise FixtureError(f"存在引用 e2e 数据的非 e2e 行（PROTECT），已回滚：{exc}") from exc
    _remove_files(files)
    return {"executed": True, "deleted": deleted, "registry_counts": registry_counts()}


def _remove_files(paths: list[str]) -> None:
    from django.conf import settings

    for rel in paths:
        full = os.path.abspath(os.path.join(settings.MEDIA_ROOT, rel))
        if not full.startswith(os.path.abspath(settings.MEDIA_ROOT) + os.sep):
            continue
        try:
            os.remove(full)
        except OSError:
            pass
