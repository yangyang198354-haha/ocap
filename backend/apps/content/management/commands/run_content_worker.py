"""MOD-057：内容中心常驻 worker（IFC-189）。"""
import signal
import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.content.conf import ContentSettings
from apps.content.handlers import register_all_handlers
from apps.content.jobs import JobService
from apps.content.media import MediaService
from apps.core.models import JobRun

HEARTBEAT_INTERVAL_SECONDS = 60


class Command(BaseCommand):
    help = "运行内容中心任务 worker"

    def add_arguments(self, parser):
        # 1.1.0（ADR-063 第 5 条）：已移除 --concurrency，worker 固定单线程串行
        parser.add_argument("--poll-interval", type=float, default=2)
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--max-jobs", type=int, default=0)

    def handle(self, *args, **options):
        interval = options["poll_interval"]
        if not 1 <= interval <= 30:
            raise CommandError("--poll-interval 必须在 1~30 秒")
        register_all_handlers()
        stopping = {"flag": False}

        def stop(signum, frame):
            stopping["flag"] = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)

        def heartbeat(status: str) -> None:
            JobRun.objects.update_or_create(
                job_name="content_worker",
                defaults={"last_run_at": timezone.now(), "last_status": status, "last_error": ""})

        processed = 0
        last_housekeeping = 0.0
        heartbeat("RUNNING")   # 启动时写一次
        last_heartbeat = time.monotonic()
        while not stopping["flag"]:
            now = timezone.now()
            # 心跳至多每 60 秒写一次，用单调时钟判断，不得每个轮询周期写（ADR-063 第 6 条）
            if time.monotonic() - last_heartbeat >= HEARTBEAT_INTERVAL_SECONDS:
                heartbeat("RUNNING")
                last_heartbeat = time.monotonic()
            if time.time() - last_housekeeping > 600:
                JobService.requeue_expired(now)
                MediaService.housekeeping(now)
                JobService.purge(now)
                last_housekeeping = time.time()
            job = JobService.claim_next(
                now=now, lease_seconds=int(ContentSettings.get("content.job.lease_seconds")))
            if job is None:
                if options["once"]:
                    break
                time.sleep(interval)
                continue
            JobService.run_one(job.id)
            processed += 1
            if options["max_jobs"] and processed >= options["max_jobs"]:
                break
        heartbeat("STOPPED")   # 停止时写一次
