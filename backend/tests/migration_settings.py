"""仅供 tests/integration/test_migration_residency_0002.py 的子进程使用：与 test_settings 相同，
但保留迁移（MIGRATION_MODULES 不置空），数据库为环境变量 OCAP_MIGRATION_DB 指向的临时 SQLite 文件。
不连接任何测试机/生产库。"""
import os

from config.test_settings import *  # noqa: F401,F403

MIGRATION_MODULES = {}
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ["OCAP_MIGRATION_DB"]}}
