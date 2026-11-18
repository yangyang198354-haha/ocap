from django.urls import path

from .views import (
    AdminCommitteeConfigView, AdminOwnerCandidatesView, AdminSeatDetailView, AdminSeatListCreateView,
)

urlpatterns = [
    path("admin/committee/seats", AdminSeatListCreateView.as_view()),
    path("admin/committee/seats/<int:seat_id>", AdminSeatDetailView.as_view()),
    path("admin/committee/owner-candidates", AdminOwnerCandidatesView.as_view()),
    path("admin/committee/config", AdminCommitteeConfigView.as_view()),
]
