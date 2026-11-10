from django.urls import path

from .views import (
    AdminRegistryImportView, AdminRegistrySpecView, AdminRegistryTemplateView,
    AdminUnitDetailView, AdminUnitListView, AdminUnitOwnersView, UnitOptionsView,
)

urlpatterns = [
    path("units/options", UnitOptionsView.as_view()),
    path("admin/registry/units", AdminUnitListView.as_view()),
    path("admin/registry/units/<int:unit_id>", AdminUnitDetailView.as_view()),
    path("admin/registry/units/<int:unit_id>/owners", AdminUnitOwnersView.as_view()),
    path("admin/registry/import", AdminRegistryImportView.as_view()),
    path("admin/registry/import/template", AdminRegistryTemplateView.as_view()),
    path("admin/registry/import/spec", AdminRegistrySpecView.as_view()),
]
