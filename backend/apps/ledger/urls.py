from django.urls import path

from .views import (AccountSummaryView, AdminAccountDetailView, AdminAccountListView,
                    LedgerReportDetailView, LedgerReportGenerateView, LedgerReportListView)

urlpatterns = [
    path("ledger/accounts/summary", AccountSummaryView.as_view()),
    path("ledger/reports", LedgerReportListView.as_view()),
    path("ledger/reports/generate", LedgerReportGenerateView.as_view()),
    path("ledger/reports/<int:report_id>", LedgerReportDetailView.as_view()),
    path("admin/ledger/accounts", AdminAccountListView.as_view()),
    path("admin/ledger/accounts/<int:account_id>", AdminAccountDetailView.as_view()),
]
