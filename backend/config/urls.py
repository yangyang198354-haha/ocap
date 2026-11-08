from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.registry.urls")),
    path("api/v1/", include("apps.residency.urls")),
    path("api/v1/", include("apps.committee.urls")),
    path("api/v1/", include("apps.identity.urls")),
    path("api/v1/", include("apps.approval.urls")),
    path("api/v1/", include("apps.resolutions.urls")),
    path("api/v1/", include("apps.claims.urls")),
    path("api/v1/", include("apps.income.urls")),
    path("api/v1/", include("apps.ledger.urls")),
    path("api/v1/", include("apps.jobs.urls")),
    path("api/v1/", include("apps.polls.urls")),
]
