"""MOD-051：提示词模板（IFC-183）。"""
from apps.core.errors import ApiError, NotFound

from .conf import ContentSettings
from .models import PromptTemplate


def _out(row: PromptTemplate) -> dict:
    return {"id": row.id, "name": row.name, "prompt": row.prompt,
            "params": row.params, "updated_at": row.updated_at}


def _validate(name, prompt):
    if name is not None:
        clean_name = str(name).strip()
        if not 1 <= len(clean_name) <= 64:
            raise ApiError("INVALID_VALUE", "模板名称长度不合法", 400)
    if prompt is not None:
        text = str(prompt).strip()
        if not text:
            raise ApiError("PROMPT_EMPTY", "提示词不能为空", 400)
        if len(text) > int(ContentSettings.get("content.ai.max_prompt_chars")):
            raise ApiError("INVALID_VALUE", "提示词过长", 400)


class PromptTemplateService:
    @staticmethod
    def list_all() -> list[dict]:
        return [_out(row) for row in PromptTemplate.objects.order_by("id")]

    @staticmethod
    def create(*, name: str, prompt: str, params=None, admin_id: int) -> dict:
        clean_name = str(name or "").strip()
        _validate(clean_name, prompt)
        if PromptTemplate.objects.filter(name=clean_name).exists():
            raise ApiError("PROMPT_NAME_EXISTS", "模板名称已存在", 409)
        row = PromptTemplate.objects.create(name=clean_name, prompt=str(prompt).strip(),
                                            params=dict(params or {}),
                                            created_by_admin_id=admin_id)
        return _out(row)

    @staticmethod
    def update(template_id: int, *, name=None, prompt=None, params=None) -> dict:
        row = PromptTemplate.objects.filter(id=template_id).first()
        if row is None:
            raise NotFound("提示词模板不存在")
        _validate(name, prompt)
        if name is not None:
            clean_name = str(name).strip()
            if PromptTemplate.objects.exclude(id=row.id).filter(name=clean_name).exists():
                raise ApiError("PROMPT_NAME_EXISTS", "模板名称已存在", 409)
            row.name = clean_name
        if prompt is not None:
            row.prompt = str(prompt).strip()
        if params is not None:
            row.params = dict(params)
        row.save()
        return _out(row)

    @staticmethod
    def delete(template_id: int) -> None:
        deleted, _ = PromptTemplate.objects.filter(id=template_id).delete()
        if not deleted:
            raise NotFound("提示词模板不存在")
