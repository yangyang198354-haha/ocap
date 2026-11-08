"""DRF 权限类（权限矩阵实现，ADR-006）。"""
from rest_framework.permissions import BasePermission

from .errors import ApiError


def _is_admin(user) -> bool:
    from apps.accounts.models import AdminAccount

    return isinstance(user, AdminAccount) and user.is_active


def _is_member(user) -> bool:
    from apps.accounts.models import User

    return isinstance(user, User) and user.status == "ACTIVE"


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_admin(request.user):
            raise ApiError("FORBIDDEN", "需要管理员权限", 403)
        return True


class IsMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            if _is_admin(request.user):
                raise ApiError("FORBIDDEN", "需要普通用户权限", 403)
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        return True


class IsCommitteeMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        from apps.committee.services import CommitteeQuery

        if not CommitteeQuery.is_member(request.user.id):
            raise ApiError("FORBIDDEN", "需要业委会成员身份", 403)
        return True


class IsChairOrVice(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        from apps.committee.services import CommitteeQuery

        if not CommitteeQuery.is_chair_or_vice(request.user.id):
            raise ApiError("FORBIDDEN", "需要主任或副主任身份", 403)
        return True


class IsRepresentative(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        from apps.committee.services import CommitteeQuery

        if not CommitteeQuery.is_representative(request.user.id):
            raise ApiError("FORBIDDEN", "需要业主代表身份", 403)
        return True


class IsOwnerOfUnit(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        from apps.residency.services import MembershipService

        unit_id = view.kwargs.get("unit_id") or request.data.get("unit_id")
        if unit_id is None:
            raise ApiError("INVALID_QUERY", "缺少专有部分")
        if not MembershipService.is_owner_of(request.user.id, int(unit_id)):
            raise ApiError("FORBIDDEN", "仅该专有部分产权业主可操作", 403)
        return True


class IsIncomeMember(BasePermission):
    """收入记账/台账：现任业委会成员（主任、副主任、委员）。"""

    def has_permission(self, request, view) -> bool:
        if not _is_member(request.user):
            raise ApiError("UNAUTHORIZED", "请先登录", 401)
        from apps.committee.services import CommitteeQuery

        if not CommitteeQuery.is_member(request.user.id):
            raise ApiError("FORBIDDEN", "需要业委会成员身份", 403)
        return True
