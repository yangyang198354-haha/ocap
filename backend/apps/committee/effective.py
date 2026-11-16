# MOD-116 / implements IFC-311 / depends 仅 django.db.models.Q 与 datetime
"""席位"生效"判定的唯一定义（ADR-115）：状态 ACTIVE 且 term_start ≤ 今天 ≤ term_end。"""
from datetime import date

from django.db.models import Q


def effective_q(today: date) -> Q:
    return Q(status="ACTIVE", term_start__lte=today, term_end__gte=today)


def is_effective(seat, today: date) -> bool:
    return seat.status == "ACTIVE" and seat.term_start <= today <= seat.term_end
