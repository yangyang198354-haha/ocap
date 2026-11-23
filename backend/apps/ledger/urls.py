from django.urls import path

from .views import (
    HistoricalExpenseBatchDetailView, HistoricalExpenseBatchListView, HistoricalExpenseBatchVoidView,
    HistoricalExpenseImportView, HistoricalExpenseTemplateView, LedgerReportDetailView,
    LedgerReportGenerateView, LedgerReportListView,
)

urlpatterns = [
    path("ledger/reports", LedgerReportListView.as_view()),
    path("ledger/reports/generate", LedgerReportGenerateView.as_view()),
    path("admin/ledger/historical-expenses/template", HistoricalExpenseTemplateView.as_view()),
    path("admin/ledger/historical-expenses/import", HistoricalExpenseImportView.as_view()),
    path("admin/ledger/historical-expenses/batches", HistoricalExpenseBatchListView.as_view()),
    path("admin/ledger/historical-expenses/batches/<int:batch_id>", HistoricalExpenseBatchDetailView.as_view()),
    path("admin/ledger/historical-expenses/batches/<int:batch_id>/void", HistoricalExpenseBatchVoidView.as_view()),
    path("ledger/reports/<int:report_id>", LedgerReportDetailView.as_view()),
]
