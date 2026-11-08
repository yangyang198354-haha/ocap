from django.urls import path

from .views import (
    AdminAppealDecisionView, AdminAppealListView, AppealListCreateView, CertificationView,
    ResidentApplicationCreateView, ResidentApplicationDecisionView, ResidentApplicationMineView,
    ResidentApplicationToReviewView, ResidentRemoveView, UnitLeaveView,
)

urlpatterns = [
    path("certifications", CertificationView.as_view()),
    path("appeals", AppealListCreateView.as_view()),
    path("appeals/mine", AppealListCreateView.as_view()),
    path("admin/appeals", AdminAppealListView.as_view()),
    path("admin/appeals/<int:appeal_id>/decision", AdminAppealDecisionView.as_view()),
    path("resident-applications", ResidentApplicationCreateView.as_view()),
    path("resident-applications/mine", ResidentApplicationMineView.as_view()),
    path("resident-applications/to-review", ResidentApplicationToReviewView.as_view()),
    path("resident-applications/<int:application_id>/decision", ResidentApplicationDecisionView.as_view()),
    path("units/<int:unit_id>/residents/<int:user_id>", ResidentRemoveView.as_view()),
    path("units/<int:unit_id>/leave", UnitLeaveView.as_view()),
]
