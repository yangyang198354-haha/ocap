from django.urls import path

from .views import (
    AdminAccountListCreateView, AdminLoginView, AdminPasswordResetView, AdminUserListView,
    AvatarUploadView, CodeRequestView, EmailVerifyView, LoginByCodeView, LoginByEmailView,
    LoginByPasswordView, LogoutView, MeCodeRequestView, MiniappLoginView, PasswordUpdateView,
    ProfileView, RegisterView, ThemePreferenceView, WebWechatCallbackView, WebWechatExchangeView, WebWechatParamsView,
)

urlpatterns = [
    path("auth/codes", CodeRequestView.as_view()),
    path("me/codes", MeCodeRequestView.as_view()),
    path("auth/register", RegisterView.as_view()),
    path("auth/login/code", LoginByCodeView.as_view()),
    path("auth/login/password", LoginByPasswordView.as_view()),
    path("auth/login/email", LoginByEmailView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/wechat/miniapp", MiniappLoginView.as_view()),
    path("auth/wechat/web/params", WebWechatParamsView.as_view()),
    path("auth/wechat/web/callback", WebWechatCallbackView.as_view()),
    path("auth/wechat/web/exchange", WebWechatExchangeView.as_view()),
    path("me/password", PasswordUpdateView.as_view()),
    path("me/profile", ProfileView.as_view()),
    path("me/theme", ThemePreferenceView.as_view()),
    path("me/avatar", AvatarUploadView.as_view()),
    path("me/email/verify", EmailVerifyView.as_view()),
    path("admin/auth/login", AdminLoginView.as_view()),
    path("admin/admins", AdminAccountListCreateView.as_view()),
    path("admin/admins/<int:admin_id>/reset-password", AdminPasswordResetView.as_view()),
    path("admin/users", AdminUserListView.as_view()),
]
