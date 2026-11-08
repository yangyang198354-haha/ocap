from django.urls import path

from .views import (
    ResolutionDetailView, ResolutionListCreateView, ResolutionResubmitView, ResolutionWithdrawView,
    VoteView,
)

urlpatterns = [
    path("resolutions", ResolutionListCreateView.as_view()),
    path("resolutions/<int:resolution_id>", ResolutionDetailView.as_view()),
    path("resolutions/<int:resolution_id>/withdraw", ResolutionWithdrawView.as_view()),
    path("resolutions/<int:resolution_id>/resubmit", ResolutionResubmitView.as_view()),
    path("resolutions/<int:resolution_id>/votes", VoteView.as_view()),
]
