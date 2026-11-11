"""MOD-057：任务处理器装配。"""
from .ai_jobs import ImageJobHandler, TextJobHandler, VideoJobHandler
from .drafts import DraftPushHandler
from .jobs import JobService


def register_all_handlers() -> None:
    for handler in (TextJobHandler(), ImageJobHandler(), VideoJobHandler(), DraftPushHandler()):
        JobService.register_handler(handler)
