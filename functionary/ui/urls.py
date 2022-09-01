from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import dashboard, environments, functions, packages, tasks, teams

app_name = "ui"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path(
        "environment_list/",
        environments.EnvironmentListView.as_view(),
        name="environment-list",
    ),
    path(
        "environment/<uuid:pk>",
        environments.EnvironmentDetailView.as_view(),
        name="environment-detail",
    ),
    path("function_list/", functions.FunctionListView.as_view(), name="function-list"),
    path(
        "function/<uuid:pk>",
        functions.FunctionDetailView.as_view(),
        name="function-detail",
    ),
    path("package_list/", packages.PackageListView.as_view(), name="package-list"),
    path(
        "package/<uuid:pk>", packages.PackageDetailView.as_view(), name="package-detail"
    ),
    path("task_list/", tasks.TaskListView.as_view(), name="task-list"),
    path("task/<uuid:pk>", tasks.TaskDetailView.as_view(), name="task-detail"),
    path("team_list/", teams.TeamListView.as_view(), name="team-list"),
    path("team/<uuid:pk>", teams.TeamDetailView.as_view(), name="team-detail"),
    path("environment/set_environment_id", environments.set_environment_id, name="set-environment"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
