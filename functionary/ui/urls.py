from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from .views import environments, functions, home, packages, tasks, teams

app_name = "ui"

urlpatterns = [
    path("", login_required(home.home), name="home"),
    path(
        "environment_list/",
        login_required(environments.EnvironmentListView.as_view()),
        name="environment-list",
    ),
    path(
        "environment/<uuid:pk>",
        login_required(environments.EnvironmentDetailView.as_view()),
        name="environment-detail",
    ),
    path(
        "function_list/",
        login_required(functions.FunctionListView.as_view()),
        name="function-list",
    ),
    path(
        "function/<uuid:pk>",
        login_required(functions.FunctionDetailView.as_view()),
        name="function-detail",
    ),
    path(
        "function_execute/", login_required(functions.execute), name="function-execute"
    ),
    path(
        "package_list/",
        login_required(packages.PackageListView.as_view()),
        name="package-list",
    ),
    path(
        "package/<uuid:pk>",
        login_required(packages.PackageDetailView.as_view()),
        name="package-detail",
    ),
    path("task_list/", login_required(tasks.TaskListView.as_view()), name="task-list"),
    path(
        "task/<uuid:pk>",
        login_required(tasks.TaskDetailView.as_view()),
        name="task-detail",
    ),
    path("team_list/", login_required(teams.TeamListView.as_view()), name="team-list"),
    path(
        "team/<uuid:pk>",
        login_required(teams.TeamDetailView.as_view()),
        name="team-detail",
    ),
    path(
        "environment/set_environment_id",
        login_required(environments.set_environment_id),
        name="set-environment",
    ),
    path("", include("django.contrib.auth.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
