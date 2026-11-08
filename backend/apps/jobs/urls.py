from django.urls import path

from .views import (
    ApproveResolutionsView, AuditCleanupView, AuthCleanupView, ClosePollsView,
    ExpireCommitteeSeatsView, ExpireMembershipsView, LedgerGenerateDueView,
)

urlpatterns = [
    path("jobs/approve-resolutions", ApproveResolutionsView.as_view()),
    path("jobs/close-polls", ClosePollsView.as_view()),
    path("jobs/expire-memberships", ExpireMembershipsView.as_view()),
    path("jobs/expire-committee-seats", ExpireCommitteeSeatsView.as_view()),
    path("jobs/ledger/generate-due", LedgerGenerateDueView.as_view()),
    path("jobs/auth/cleanup", AuthCleanupView.as_view()),
    path("jobs/audit/cleanup", AuditCleanupView.as_view()),
]
