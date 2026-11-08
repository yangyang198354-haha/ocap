from django.urls import path

from .views import LedgerReportDetailView, LedgerReportGenerateView, LedgerReportListView

urlpatterns = [
    path("ledger/reports", LedgerReportListView.as_view()),
    path("ledger/reports/generate", LedgerReportGenerateView.as_view()),
    path("ledger/reports/<int:report_id>", LedgerReportDetailView.as_view()),
]
