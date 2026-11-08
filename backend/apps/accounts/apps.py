from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    verbose_name = "账号与登录"

    def ready(self) -> None:
        from apps.core.user_refs import register_user_reference

        from .models import AuthToken, LoginTicket, User, WeChatIdentity

        register_user_reference(WeChatIdentity, "user", on_conflict="move_all")
        register_user_reference(AuthToken, "user", on_conflict="delete_secondary")
        register_user_reference(LoginTicket, "user", on_conflict="delete_secondary")
        _ = User
