from django.urls import path

from .views import (
    AdminAppealDecisionView, AdminAppealListView, AppealListCreateView, AppealWithdrawView,
    CertificationView, MyHousingView, RegistryMatchesConfirmView, RegistryMatchesDismissView,
    RegistryMatchesView, ResidentApplicationCreateView, ResidentApplicationDecisionView,
    ResidentApplicationMineView, ResidentApplicationToReviewView, ResidentApplicationWithdrawView,
    ResidentRemoveView, UnitLeaveView,
)

urlpatterns = [
    path("me/housing", MyHousingView.as_view()),
    path("me/registry-matches", RegistryMatchesView.as_view()),
    path("me/registry-matches/confirm", RegistryMatchesConfirmView.as_view()),
    path("me/registry-matches/dismiss", RegistryMatchesDismissView.as_view()),
    path("certifications", CertificationView.as_view()),
    path("appeals", AppealListCreateView.as_view()),
    path("appeals/mine", AppealListCreateView.as_view()),
    path("appeals/<int:appeal_id>/withdraw", AppealWithdrawView.as_view()),
    path("admin/appeals", AdminAppealListView.as_view()),
    path("admin/appeals/<int:appeal_id>/decision", AdminAppealDecisionView.as_view()),
    path("resident-applications", ResidentApplicationCreateView.as_view()),
    path("resident-applications/mine", ResidentApplicationMineView.as_view()),
    path("resident-applications/<int:application_id>/withdraw", ResidentApplicationWithdrawView.as_view()),
    path("resident-applications/to-review", ResidentApplicationToReviewView.as_view()),
    path("resident-applications/<int:application_id>/decision", ResidentApplicationDecisionView.as_view()),
    path("units/<int:unit_id>/residents/<int:user_id>", ResidentRemoveView.as_view()),
    path("units/<int:unit_id>/leave", UnitLeaveView.as_view()),
]
