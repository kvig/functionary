from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from .views import (
    builds,
    environments,
    functions,
    home,
    packages,
    scheduling,
    tasks,
    teams,
    variables,
)

app_name = "ui"

urlpatterns = [
    path("", home.home, name="home"),
    path(
        "create_schedule/",
        (scheduling.create_scheduled_task),
        name="create-schedule",
    ),
    path(
        "build_list/",
        (builds.BuildListView.as_view()),
        name="build-list",
    ),
    path(
        "build/<uuid:pk>",
        (builds.BuildDetailView.as_view()),
        name="build-detail",
    ),
    path(
        "environment_list/",
        (environments.EnvironmentListView.as_view()),
        name="environment-list",
    ),
    path(
        "environment/<uuid:pk>",
        (environments.EnvironmentDetailView.as_view()),
        name="environment-detail",
    ),
    path(
        "function_list/",
        (functions.FunctionListView.as_view()),
        name="function-list",
    ),
    path(
        "function/<uuid:pk>",
        (functions.FunctionDetailView.as_view()),
        name="function-detail",
    ),
    path("function_execute/", (functions.execute), name="function-execute"),
    path(
        "new_schedule/",
        (scheduling.ScheduledTaskCreateView.as_view()),
        name="new-schedule",
    ),
    path(
        "package_list/",
        (packages.PackageListView.as_view()),
        name="package-list",
    ),
    path(
        "package/<uuid:pk>",
        (packages.PackageDetailView.as_view()),
        name="package-detail",
    ),
    path(
        "schedule/<uuid:pk>",
        (scheduling.ScheduledTaskUpdateView.as_view()),
        name="schedule-detail",
    ),
    path(
        "schedule_list/",
        (scheduling.ScheduledTaskListView.as_view()),
        name="schedule-list",
    ),
    path("task_list/", (tasks.TaskListView.as_view()), name="task-list"),
    path(
        "task/<uuid:pk>",
        (tasks.TaskDetailView.as_view()),
        name="task-detail",
    ),
    path("team_list/", (teams.TeamListView.as_view()), name="team-list"),
    path(
        "team/<uuid:pk>",
        (teams.TeamDetailView.as_view()),
        name="team-detail",
    ),
    path(
        "update_schedule/<uuid:pk>",
        (scheduling.update_scheduled_task),
        name="update-schedule",
    ),
    re_path(
        r"^environment/set_environment/(?:(?P<pk>\w+)?$)",
        (environments.EnvironmentSelectView.as_view()),
        name="set-environment",
    ),
    path(
        "variables/<parent_id>",
        (variables.all_variables),
        name="all-variables",
    ),
    path(
        "add_variable/<parent_id>",
        (variables.VariableView.as_view()),
        name="add-variable",
    ),
    path(
        "update_variable/<pk>/<parent_id>",
        (variables.UpdateVariableView.as_view()),
        name="update-variable",
    ),
    path(
        "delete_variable/<pk>",
        (variables.delete_variable),
        name="delete-variable",
    ),
    path(
        "detail_variable/<pk>",
        (variables.VariableView.as_view()),
        name="detail-variable",
    ),
    path("", include("django.contrib.auth.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


htmx_urlpatterns = [
    path(
        "crontab_minute_param/",
        (scheduling.crontab_minute_param),
        name="scheduled-minute-param",
    ),
    path(
        "crontab_hour_param/",
        (scheduling.crontab_hour_param),
        name="scheduled-hour-param",
    ),
    path(
        "crontab_day_of_week_param/",
        (scheduling.crontab_day_of_week_param),
        name="scheduled-day-of-week-param",
    ),
    path(
        "crontab_day_of_month_param/",
        (scheduling.crontab_day_of_month_param),
        name="scheduled-day-of-month-param",
    ),
    path(
        "crontab_month_of_year_param/",
        (scheduling.crontab_month_of_year_param),
        name="scheduled-month-of-year-param",
    ),
    path(
        "function_parameters/",
        (scheduling.function_parameters),
        name="function-parameters",
    ),
]

urlpatterns += htmx_urlpatterns
