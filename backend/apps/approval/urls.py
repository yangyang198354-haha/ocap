from django.urls import path

from .views import (
    AdminFlowDetailView, AdminFlowListCreateView, FlowOptionListView, InstanceDecisionView, TaskListView,
)

urlpatterns = [
    path("admin/approval/flows", AdminFlowListCreateView.as_view()),
    path("admin/approval/flows/<int:flow_id>", AdminFlowDetailView.as_view()),
    path("approval/flows", FlowOptionListView.as_view()),
    path("approval/tasks", TaskListView.as_view()),
    path("approval/instances/<int:instance_id>/decision", InstanceDecisionView.as_view()),
]
