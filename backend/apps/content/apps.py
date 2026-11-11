from django.apps import AppConfig
from django.core.checks import Warning, register


class ContentConfig(AppConfig):
    name = "apps.content"
    verbose_name = "内容中心"

    def ready(self):
        from django.conf import settings

        def check_key(app_configs, **kwargs):
            if not getattr(settings, "CONTENT_CRED_ENC_KEY", ""):
                return [Warning("未配置 CONTENT_CRED_ENC_KEY，内容中心凭据保存将返回 503",
                                id="content.W001")]
            return []

        register(check_key)
