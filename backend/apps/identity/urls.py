from django.urls import path

from .views import (
    AdminMembershipListView, AdminMembershipRevokeView, CancelAccountView,
    MeView, PhoneBindView, PhoneChangeView,
)

urlpatterns = [
    path("me", MeView.as_view()),
    path("me/phone/bind", PhoneBindView.as_view()),
    path("me/phone/change", PhoneChangeView.as_view()),
    path("me/cancel", CancelAccountView.as_view()),
    path("admin/memberships", AdminMembershipListView.as_view()),
    path("admin/memberships/revoke", AdminMembershipRevokeView.as_view()),
]
