"""用户引用注册表（IFC-008；REQ-FUNC-067）。"""
from typing import Callable

from django.apps import apps
from django.db.models import Model

_REFERENCES: dict[tuple[str, str], dict] = {}


def register_user_reference(model: type[Model], field: str, *, on_conflict: str,
                            handler: Callable | None = None) -> None:
    _REFERENCES[(model._meta.label_lower, field)] = {
        "on_conflict": on_conflict,
        "handler": handler,
        "model": model,
        "field": field,
    }


def references() -> list[dict]:
    return list(_REFERENCES.values())


def assert_all_user_fks_registered() -> None:
    """遍历所有指向 accounts.User 的外键，未登记即报错（Django check）。"""
    from apps import accounts

    user_model = accounts.models.User
    missing = []
    for model in apps.get_models():
        if model is user_model:
            continue
        for field in model._meta.get_fields():
            if not getattr(field, "is_relation", False) or field.auto_created:
                continue
            remote = getattr(field, "remote_field", None)
            if remote is None or remote.model is not user_model:
                continue
            key = (model._meta.label_lower, field.name)
            if key not in _REFERENCES:
                missing.append(f"{model._meta.label}.{field.name}")
    if missing:
        raise AssertionError("未登记的用户外键引用：" + ", ".join(sorted(missing)))
