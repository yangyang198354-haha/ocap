from django.urls import path

from .views import (
    AdminRegistryImportView, AdminUnitDetailView, AdminUnitListView, AdminUnitPhonesView,
    UnitOptionsView,
)

urlpatterns = [
    path("units/options", UnitOptionsView.as_view()),
    path("admin/registry/units", AdminUnitListView.as_view()),
    path("admin/registry/units/<int:unit_id>", AdminUnitDetailView.as_view()),
    path("admin/registry/units/<int:unit_id>/phones", AdminUnitPhonesView.as_view()),
    path("admin/registry/import", AdminRegistryImportView.as_view()),
]
