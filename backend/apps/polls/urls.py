from django.urls import path

from .views import PollDetailView, PollListCreateView, PollResponseView, PollResultView

urlpatterns = [
    path("polls", PollListCreateView.as_view()),
    path("polls/<int:poll_id>", PollDetailView.as_view()),
    path("polls/<int:poll_id>/responses", PollResponseView.as_view()),
    path("polls/<int:poll_id>/result", PollResultView.as_view()),
]
