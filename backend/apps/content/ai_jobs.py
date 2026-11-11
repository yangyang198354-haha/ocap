"""MOD-052：AI 生成任务（IFC-184）。"""
import hashlib
from typing import Mapping, Sequence

from django.db import transaction
from django.utils import timezone

from apps.core.audit import AuditActor, AuditService
from apps.core.errors import ApiError, NotFound
from apps.core.ratelimit import RateLimiter
from apps.integrations.imagegen import ImageGenError, get_imagegen_client
from apps.integrations.llm import ChatMessage, LlmError, get_llm_client
from apps.integrations.videogen import VideoGenError, VideoScene, get_videogen_client

from .conf import ContentSettings
from .jobs import Done, Fail, JobContext, JobService, Wait
from .media import MediaFetchError, MediaService
from .models import ContentJob, MediaItem
from .posts import PostService
from .richtext import extract_paragraphs, render_text, text_to_doc
from .services_config import ServiceConfigService

MAX_TOKENS = {"SHORT": 1024, "MEDIUM": 2048, "LONG": 4096}
TONE_TEXT = {"FORMAL": "正式", "FRIENDLY": "亲切", "CONCISE": "简洁"}


def _limit(admin) -> None:
    decision = RateLimiter.hit(f"content_ai:{getattr(admin, 'id', 0)}",
                               limit=int(ContentSettings.get("content.ai.rate_limit_per_hour")),
                               window_seconds=3600)
    if not decision.allowed:
        raise ApiError("CODE_RATE_LIMITED", "操作过于频繁，请稍后再试", 429,
                       {"retry_after": decision.retry_after})


def _actor(admin):
    return AuditActor("ADMIN", getattr(admin, "id", None),
                      getattr(admin, "username", "") or "")


class AiGenerationService:
    @staticmethod
    def submit_text(*, prompt: str, service_type=None, template_id=None,
                    params: Mapping | None = None, admin) -> ContentJob:
        _limit(admin)
        text = str(prompt or "").strip()
        if not text:
            raise ApiError("PROMPT_EMPTY", "请输入提示词", 400)
        if len(text) > int(ContentSettings.get("content.ai.max_prompt_chars")):
            raise ApiError("INVALID_VALUE", "提示词过长", 400)
        if template_id is not None:
            from .models import PromptTemplate
            if not PromptTemplate.objects.filter(id=template_id).exists():
                raise NotFound("提示词模板不存在")
        resolved_type, model = ServiceConfigService.resolve_llm(service_type)
        clean_params = AiGenerationService._params(params)
        job = JobService.enqueue(
            kind="LLM_TEXT",
            payload={"prompt": text, "service_type": resolved_type, "model": model,
                     "params": clean_params},
            admin_id=getattr(admin, "id", 0),
            admin_label=getattr(admin, "username", "") or "",
        )
        return job

    @staticmethod
    def _params(params: Mapping | None) -> dict:
        clean: dict = {}
        params = params or {}
        if params.get("tone") in TONE_TEXT:
            clean["tone"] = params["tone"]
        if params.get("length") in MAX_TOKENS:
            clean["length"] = params["length"]
        if params.get("temperature") is not None:
            try:
                temperature = float(params["temperature"])
            except (TypeError, ValueError):
                raise ApiError("INVALID_VALUE", "temperature 不合法", 400)
            if not 0 <= temperature <= 1.5:
                raise ApiError("INVALID_VALUE", "temperature 不合法", 400)
            clean["temperature"] = temperature
        return clean

    @staticmethod
    def submit_image(*, prompt: str, n: int = 1, size: str | None = None, admin) -> ContentJob:
        _limit(admin)
        text = str(prompt or "").strip()
        if not text:
            raise ApiError("PROMPT_EMPTY", "请输入提示词", 400)
        if len(text) > 500:
            raise ApiError("INVALID_VALUE", "提示词过长", 400)
        try:
            count = int(n)
        except (TypeError, ValueError):
            raise ApiError("INVALID_VALUE", "生成张数不合法", 400)
        if not 1 <= count <= 4:
            raise ApiError("INVALID_VALUE", "生成张数不合法", 400)
        import re
        size_value = size or ContentSettings.get("content.image.default_size")
        if not isinstance(size_value, str) or not re.match(r"^\d{3,4}x\d{3,4}$", size_value):
            raise ApiError("INVALID_VALUE", "尺寸不合法", 400)
        rows = ServiceConfigService.list_all()
        config = next((row for row in rows if row["service_type"] == "IMAGE_ARK"
                       and row["configured"]), None)
        if config is None:
            raise ApiError("IMAGE_NOT_CONFIGURED", "请先配置图像生成服务", 409)
        return JobService.enqueue(
            kind="IMAGE_GEN",
            payload={"prompt": text, "n": count, "size": size_value,
                     "model": config["params"].get("model", "")},
            admin_id=getattr(admin, "id", 0),
            admin_label=getattr(admin, "username", "") or "",
            subject_type="content_image", subject_id="",
        )

    @staticmethod
    def submit_video(*, post_id: int, admin) -> ContentJob:
        _limit(admin)
        rows = ServiceConfigService.list_all()
        if not any(row["service_type"] == "VIDEO_JIMENG" and row["configured"] for row in rows):
            raise ApiError("VIDEO_NOT_CONFIGURED", "请先配置视频生成服务", 409)
        post = PostService.get(post_id)
        text = render_text(post.doc).strip()
        if not PostService.is_text_confirmed(post) or not text:
            AuditService.record(actor=_actor(admin), action="CONTENT_VIDEO_REQUESTED",
                                object_type="content_post", object_id=str(post.id),
                                result="DENIED", detail={"reason": "TEXT_NOT_CONFIRMED"})
            raise ApiError("TEXT_NOT_CONFIRMED", "请先确认文案", 409)
        if len(text) > int(ContentSettings.get("content.video.max_text_chars")):
            raise ApiError("INVALID_VALUE", "文案过长", 400)
        # 分镜按文档段落切分（ADR-063 第 8 条）；上面的文案校验与 text_sha256 仍用 render_text 口径
        scenes = AiGenerationService.build_scenes(
            extract_paragraphs(post.doc),
            max_scenes=int(ContentSettings.get("content.video.max_scenes")),
            scene_seconds=int(ContentSettings.get("content.video.scene_seconds")),
            transition=ContentSettings.get("content.video.transition"),
        )
        job = JobService.enqueue(
            kind="VIDEO_GEN",
            payload={"post_id": post.id,
                     "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                     "scenes": [scene.__dict__ for scene in scenes]},
            admin_id=getattr(admin, "id", 0),
            admin_label=getattr(admin, "username", "") or "",
            subject_type="content_post", subject_id=str(post.id), max_attempts=1,
        )
        AuditService.record(actor=_actor(admin), action="CONTENT_VIDEO_REQUESTED",
                            object_type="content_post", object_id=str(post.id),
                            result="SUCCESS", detail={"job_id": job.id, "scenes": len(scenes)})
        return job

    @staticmethod
    def build_scenes(paragraphs: Sequence[str], *, max_scenes: int, scene_seconds: int,
                     transition: str) -> list[VideoScene]:
        paragraphs = [str(part).strip() for part in paragraphs if str(part).strip()]
        if not paragraphs:
            raise ApiError("POST_INCOMPLETE", "没有可用于生成视频的文案段落", 400,
                           {"missing": ["body"]})
        while len(paragraphs) > max_scenes:
            shortest = min(range(len(paragraphs) - 1),
                           key=lambda i: len(paragraphs[i]) + len(paragraphs[i + 1]))
            paragraphs[shortest:shortest + 2] = [paragraphs[shortest] + "\n" + paragraphs[shortest + 1]]
        return [VideoScene(scene_index=i, scene_prompt=text, narration=text,
                           duration_sec=scene_seconds, transition=transition)
                for i, text in enumerate(paragraphs)]

    @staticmethod
    def compose_messages(prompt: str, params: Mapping) -> list[ChatMessage]:
        tone = TONE_TEXT.get((params or {}).get("tone", ""), "正式")
        length = (params or {}).get("length", "MEDIUM")
        system = (f"你是小区信息公开发布的文案助手，语气{tone}，篇幅{length}。"
                  "只输出可直接发布的正文，不要解释。")
        return [ChatMessage("system", system), ChatMessage("user", prompt)]


class TextJobHandler:
    kind = "LLM_TEXT"
    idempotent = True

    def run(self, ctx: JobContext):
        payload = ctx.job.payload
        try:
            secrets = ServiceConfigService.secrets_for(payload["service_type"])
        except ApiError as exc:
            return Fail(exc.code, exc.message)
        params = payload.get("params") or {}
        try:
            text = get_llm_client().generate(
                service_type=payload["service_type"], api_key=secrets.get("api_key", ""),
                model=payload["model"],
                messages=AiGenerationService.compose_messages(payload["prompt"], params),
                max_tokens=MAX_TOKENS.get(params.get("length"), 2048),
                temperature=float(params.get("temperature", 1.0)),
                timeout_seconds=int(ContentSettings.get("content.llm.timeout_seconds")),
            )
        except LlmError as exc:
            return Fail(exc.code, exc.message)
        return Done({"text": text, "doc": text_to_doc(text),
                     "service_type": payload["service_type"], "model": payload["model"]})

    def on_interrupted(self, job: ContentJob) -> None:
        return None


def _media_out(row) -> dict:
    from .media import sign_media_url
    return {"id": str(row.id), "media_type": row.media_type, "source": row.source,
            "state": row.state, "title": row.title, "original_name": row.original_name,
            "size": row.size, "content_type": row.content_type,
            "url": sign_media_url(row.id), "created_at": row.created_at,
            "in_use": bool(row.post_links.filter(post__status="PUBLISHED").exists())}


class ImageJobHandler:
    kind = "IMAGE_GEN"
    idempotent = True

    def run(self, ctx: JobContext):
        payload = ctx.job.payload
        try:
            secrets = ServiceConfigService.secrets_for("IMAGE_ARK")
        except ApiError as exc:
            return Fail(exc.code, exc.message)
        try:
            urls = get_imagegen_client().generate(
                api_key=secrets.get("api_key", ""), model=payload["model"],
                prompt=payload["prompt"], n=int(payload["n"]), size=payload["size"],
                timeout_seconds=int(ContentSettings.get("content.image.timeout_seconds")),
            )
        except ImageGenError as exc:
            return Fail(exc.code, exc.message)
        rows = []
        for index, url in enumerate(urls):
            try:
                stream = MediaService.fetch_remote(
                    url, max_bytes=int(ContentSettings.get("content.media.ai_image_max_bytes")),
                    timeout_seconds=int(ContentSettings.get("content.image.timeout_seconds")))
                row = MediaService.store_stream(
                    chunks=stream, media_type="IMAGE", source="AI_GENERATED",
                    state="CANDIDATE", title=f"AI 配图 {ctx.job.id}-{index + 1}",
                    original_name=f"ai_{ctx.job.id}_{index}.png",
                    max_bytes=int(ContentSettings.get("content.media.ai_image_max_bytes")),
                    ai_job_id=ctx.job.id, admin_id=ctx.job.created_by_admin_id)
            except (MediaFetchError, ApiError) as exc:
                return Fail(getattr(exc, "code", "UPSTREAM"), "生成结果下载失败")
            rows.append(row)
        return Done({"media_ids": [str(row.id) for row in rows],
                     "media": [_media_out(row) for row in rows]})

    def on_interrupted(self, job: ContentJob) -> None:
        return None


class VideoJobHandler:
    kind = "VIDEO_GEN"
    idempotent = False

    def run(self, ctx: JobContext):
        payload = ctx.job.payload
        state = dict(ctx.job.state or {})
        try:
            secrets = ServiceConfigService.secrets_for("VIDEO_JIMENG")
        except ApiError as exc:
            return Fail(exc.code, exc.message)
        client = get_videogen_client()
        phase = state.get("phase")
        if phase != "POLLING":
            state["phase"] = "SUBMITTING"
            ctx.save_state(state)
            scenes = [VideoScene(**scene) for scene in payload["scenes"]]
            try:
                task_id = client.submit(access_key=secrets.get("access_key", ""),
                                        secret_key=secrets.get("secret_key", ""),
                                        scenes=scenes)
            except VideoGenError as exc:
                return Fail(exc.code, exc.message)
            state = {"phase": "POLLING", "task_id": task_id,
                     "submitted_at": timezone.now().isoformat()}
            ctx.save_state(state)
            return Wait(timezone.now() + timezone.timedelta(
                seconds=int(ContentSettings.get("content.video.poll_interval_seconds"))),
                {"phase": "POLLING", "percent": 0})
        try:
            status = client.poll(access_key=secrets.get("access_key", ""),
                                 secret_key=secrets.get("secret_key", ""),
                                 task_id=state["task_id"])
        except VideoGenError as exc:
            return Fail(exc.code, exc.message)
        if status.status == "failed":
            return Fail("REMOTE_FAILED", status.error or "远端生成失败")
        if status.status != "completed":
            started = state.get("submitted_at")
            if started:
                elapsed = (timezone.now() - timezone.datetime.fromisoformat(started)).total_seconds()
                if elapsed > int(ContentSettings.get("content.video.max_wait_seconds")):
                    return Fail("TIMEOUT", "视频生成超时")
            return Wait(timezone.now() + timezone.timedelta(
                seconds=int(ContentSettings.get("content.video.poll_interval_seconds"))),
                {"phase": "POLLING", "percent": status.progress})
        # 下载口径（ADR-063 第 8 条）：先以 CANDIDATE 逐个入库，全部成功后统一转 SAVED；
        # 任一片段失败则回收本任务已入库的片段。clip_urls 与 task_id 保留在 state 中。
        clip_urls = list(status.clip_urls)
        state = {**state, "clip_urls": clip_urls}
        ctx.save_state(state)
        rows = []
        try:
            for index, url in enumerate(clip_urls):
                ctx.heartbeat()
                stream = MediaService.fetch_remote(
                    url, max_bytes=int(ContentSettings.get("content.media.ai_video_max_bytes")),
                    timeout_seconds=60)
                rows.append(MediaService.store_stream(
                    chunks=stream, media_type="VIDEO", source="AI_GENERATED",
                    state="CANDIDATE", title=f"AI 视频 {ctx.job.id}-{index + 1}",
                    original_name=f"ai_{ctx.job.id}_{index}.mp4",
                    max_bytes=int(ContentSettings.get("content.media.ai_video_max_bytes")),
                    ai_job_id=ctx.job.id, admin_id=ctx.job.created_by_admin_id))
        except Exception as exc:  # noqa: BLE001 - 任何失败都要回收已入库片段
            MediaService.discard(rows)
            if getattr(exc, "code", "") == "FILE_TYPE_NOT_ALLOWED":
                return Fail("DOWNLOAD_FAILED", "生成结果格式不支持")
            return Fail("DOWNLOAD_FAILED", "生成结果下载失败")
        with transaction.atomic():
            MediaItem.objects.filter(id__in=[row.id for row in rows]).update(state="SAVED")
        for row in rows:
            row.state = "SAVED"
        AuditService.record(
            actor=AuditActor("ADMIN", ctx.job.created_by_admin_id, ctx.job.created_by_label),
            action="CONTENT_VIDEO_COMPLETED", object_type="content_job",
            object_id=str(ctx.job.id), result="SUCCESS",
            detail={"media": len(rows), "post_id": payload.get("post_id")})
        return Done({"media_ids": [str(row.id) for row in rows],
                     "media": [_media_out(row) for row in rows]})

    def on_interrupted(self, job: ContentJob) -> None:
        return None
