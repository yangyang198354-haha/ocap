from django.apps import AppConfig


class PollsConfig(AppConfig):
    name = "apps.polls"
    verbose_name = "业主投票"

    def ready(self) -> None:
        from apps.core.user_refs import register_user_reference

        from .models import Participant, Poll, PollResponse

        register_user_reference(Poll, "creator", on_conflict="move_all")
        from .services import merge_participants, merge_responses

        register_user_reference(Participant, "user", on_conflict="custom", handler=merge_participants)
        register_user_reference(PollResponse, "user", on_conflict="custom", handler=merge_responses)
