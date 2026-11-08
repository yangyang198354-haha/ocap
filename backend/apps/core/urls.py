from django.urls import path

from .views import AttachmentDownloadView, AttachmentUploadView, AuditLogListView, SystemConfigView

urlpatterns = [
    path("admin/audit-logs", AuditLogListView.as_view()),
    path("admin/system-config", SystemConfigView.as_view()),
    path("admin/system-config/<str:key>", SystemConfigView.as_view()),
    path("attachments", AttachmentUploadView.as_view()),
    path("attachments/<uuid:attachment_id>/download", AttachmentDownloadView.as_view()),
]
