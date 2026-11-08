"""ocap Django 设置（生产默认值；测试见 test_settings.py）。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
# CR-024：不再使用固定默认密钥。缺失时仅在 DEBUG 或显式允许（测试设置）下生成进程内随机值，否则拒绝启动。
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG or os.environ.get("DJANGO_ALLOW_EPHEMERAL_SECRET") == "1":
        import secrets as _secrets

        SECRET_KEY = _secrets.token_urlsafe(50)
    else:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("必须通过环境变量 DJANGO_SECRET_KEY 提供密钥")
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
                 if h.strip()]

INSTALLED_APPS = [
    "rest_framework",
    "apps.core",
    "apps.integrations",
    "apps.accounts",
    "apps.registry",
    "apps.residency",
    "apps.committee",
    "apps.identity",
    "apps.approval",
    "apps.resolutions",
    "apps.claims",
    "apps.income",
    "apps.ledger",
    "apps.polls",
    "apps.jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

# 生产默认 MySQL；测试用 SQLite 内存库（test_settings.py）
if os.environ.get("DB_ENGINE", "sqlite") == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "ocap"),
            "USER": os.environ.get("DB_USER", "ocap"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4", **({"ssl": {"ssl-mode": "DISABLED"}}
                        if os.environ.get("DB_SSL_DISABLED", "0") == "1" else {})},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
MEDIA_ROOT = BASE_DIR / "var" / "attachments"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.TokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "apps.core.errors.exception_handler",
}

# ---- 业务配置（SystemConfig 覆写；凭据只读环境变量）----
TRUSTED_PROXY_ADDRS = {
    a.strip() for a in os.environ.get("TRUSTED_PROXY_ADDRS", "127.0.0.1,::1").split(",") if a.strip()
}
WECHAT_MINIAPP_APPID = os.environ.get("WECHAT_MINIAPP_APPID", "")
WECHAT_MINIAPP_SECRET = os.environ.get("WECHAT_MINIAPP_SECRET", "")
WECHAT_WEB_APPID = os.environ.get("WECHAT_WEB_APPID", "")
WECHAT_WEB_SECRET = os.environ.get("WECHAT_WEB_SECRET", "")
WECHAT_WEB_REDIRECT_URI = os.environ.get("WECHAT_WEB_REDIRECT_URI", "")
WECHAT_WEB_FRONTEND_URL = os.environ.get("WECHAT_WEB_FRONTEND_URL", "/login/wechat")
WECHAT_API_TIMEOUT = 5

ALIYUN_ACCESS_KEY_ID = os.environ.get("ALIYUN_ACCESS_KEY_ID", "")
ALIYUN_ACCESS_KEY_SECRET = os.environ.get("ALIYUN_ACCESS_KEY_SECRET", "")
ALIYUN_SMS_SIGN_NAME = os.environ.get("ALIYUN_SMS_SIGN_NAME", "")
ALIYUN_SMS_TEMPLATE_CODE = os.environ.get("ALIYUN_SMS_TEMPLATE_CODE", "")
ALIYUN_SMS_TEMPLATE_TTL_MINUTES = int(os.environ.get("ALIYUN_SMS_TEMPLATE_TTL_MINUTES", "5"))
SMS_GATEWAY_BACKEND = os.environ.get("SMS_GATEWAY_BACKEND", "console")

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "0") == "1"
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@ocap.local")
