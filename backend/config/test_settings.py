"""测试设置：SQLite 内存库；外部服务一律内存替身；禁连生产。"""
import os

os.environ.setdefault("DJANGO_ALLOW_EPHEMERAL_SECRET", "1")  # 测试无需提供真实密钥

from .settings import *  # noqa: F401,F403,E402

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SMS_GATEWAY_BACKEND = "memory"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
MIGRATION_MODULES = {app.split(".")[-1]: None for app in INSTALLED_APPS if app.startswith("apps.")}  # noqa: F405
DEBUG = False
