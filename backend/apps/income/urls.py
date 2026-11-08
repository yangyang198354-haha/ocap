from django.urls import path

from .views import (
    AdminSheetDetailView, AdminSheetListView, IncomeImportView, IncomeSheetDetailView,
    IncomeSheetListView, SheetResubmitView, SheetSubmitView, SheetVoidView, SheetWithdrawView,
)

urlpatterns = [
    path("admin/income/sheets", AdminSheetListView.as_view()),
    path("admin/income/sheets/import", IncomeImportView.as_view()),
    path("admin/income/sheets/<int:sheet_id>", AdminSheetDetailView.as_view()),
    path("admin/income/sheets/<int:sheet_id>/submit", SheetSubmitView.as_view()),
    path("admin/income/sheets/<int:sheet_id>/resubmit", SheetResubmitView.as_view()),
    path("admin/income/sheets/<int:sheet_id>/withdraw", SheetWithdrawView.as_view()),
    path("admin/income/sheets/<int:sheet_id>/void", SheetVoidView.as_view()),
    path("income/sheets", IncomeSheetListView.as_view()),
    path("income/sheets/<int:sheet_id>", IncomeSheetDetailView.as_view()),
]
