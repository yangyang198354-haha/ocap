from django.urls import path

from .views import (
    AdminClaimListView, AdvanceCreateView, ClaimDetailView, ClaimListView, ClaimResubmitView,
    ClaimWithdrawView, ReimbursementCreateView, SettlementCreateView,
)

urlpatterns = [
    path("claims/reimbursements", ReimbursementCreateView.as_view()),
    path("claims/advances", AdvanceCreateView.as_view()),
    path("claims/settlements", SettlementCreateView.as_view()),
    path("claims", ClaimListView.as_view()),
    path("claims/<int:claim_id>", ClaimDetailView.as_view()),
    path("claims/<int:claim_id>/withdraw", ClaimWithdrawView.as_view()),
    path("claims/<int:claim_id>/resubmit", ClaimResubmitView.as_view()),
    path("admin/claims", AdminClaimListView.as_view()),
]
