"""GROUP_D（回流 1）：内容中心测试公共工具（日志捕获、审计断言、隔离的媒体目录）。"""
import json
import logging
import shutil
import tempfile
from contextlib import contextmanager

from django.test import override_settings

from apps.core.models import AuditLog
from tests.integration.test_content_api import ContentTestBase


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record):
        try:
            self.lines.append(self.format(record))
        except Exception:  # noqa: BLE001 - 捕获器自身不能影响被测代码
            self.lines.append(str(record.msg))


@contextmanager
def capture_logs():
    """捕获所有 logger（含不向上传播的）在 DEBUG 及以上输出的文本，用于"日志中出现 0 次"断言。"""
    handler = _ListHandler()
    touched = []
    loggers = [logging.getLogger()] + [
        item for item in logging.root.manager.loggerDict.values() if isinstance(item, logging.Logger)]
    for logger in loggers:
        touched.append((logger, logger.level))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    try:
        yield handler.lines
    finally:
        for logger, level in touched:
            logger.removeHandler(handler)
            logger.setLevel(level)


def audit_dump() -> str:
    """全部审计记录（含 detail）序列化成一个字符串，用于"审计中出现 0 次"断言。"""
    return json.dumps(list(AuditLog.objects.values()), ensure_ascii=False, default=str)


class ContentRoundBase(ContentTestBase):
    """隔离 MEDIA_ROOT 到临时目录，并提供审计断言助手。"""

    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp(prefix="ocap-test-media-")
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, True)

    # ---- 审计 ----
    def audit_rows(self, action, object_id=None):
        qs = AuditLog.objects.filter(action=action)
        if object_id is not None:
            qs = qs.filter(object_id=str(object_id))
        return list(qs.order_by("id"))

    def audit_count(self, action):
        return AuditLog.objects.filter(action=action).count()

    def assert_new_audit(self, action, before, *, object_type, object_id, result="SUCCESS"):
        """断言该动作相对 before 恰好新增 1 条，且含操作人、对象、时间、结果四项；返回该记录。"""
        rows = self.audit_rows(action)
        self.assertEqual(len(rows), before + 1, f"{action} 应新增 1 条，实际 {len(rows) - before}")
        row = rows[-1]
        self.assertEqual((row.actor_type, row.actor_id, row.actor_label),
                         ("ADMIN", self.admin.id, self.admin.username))
        self.assertEqual((row.object_type, row.object_id, row.result),
                         (object_type, str(object_id), result))
        self.assertIsNotNone(row.occurred_at)
        return row
