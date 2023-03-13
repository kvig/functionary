from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (
    account,
    build,
    environment,
    environment_select,
    function,
    home,
    package,
    scheduled_task,
    task,
    team,
    variable,
    workflow,
)

app_name = "ui"

"""
URL naming convention:

Sort the url patterns alphabetically.

For action based URLs, use <model>-<verb> with the following verbs:
    - create
    - delete
    - list
    - detail
    - update

"""


urlpatterns = [
    path("", home.home, name="home"),
    path(
        "build_list/",
        (build.BuildListView.as_view()),
        name="build-list",
    ),
    path(
        "build/<uuid:pk>",
        (build.BuildDetailView.as_view()),
        name="build-detail",
    ),
    path(
        "function_list/",
        (function.FunctionListView.as_view()),
        name="function-list",
    ),
    path(
        "function/<uuid:pk>",
        (function.FunctionDetailView.as_view()),
        name="function-detail",
    ),
    path("function_execute/", (function.execute), name="function-execute"),
    path(
        "function_parameters/",
        (function.function_parameters),
        name="function-parameters",
    ),
    path(
        "package_list/",
        (package.PackageListView.as_view()),
        name="package-list",
    ),
    path(
        "package/<uuid:pk>",
        (package.PackageDetailView.as_view()),
        name="package-detail",
    ),
    path("task_list/", (task.TaskListView.as_view()), name="task-list"),
    path(
        "task/<uuid:pk>",
        (task.TaskDetailView.as_view()),
        name="task-detail",
    ),
    path("task/<pk>/log", (task.get_task_log), name="task-log"),
    path(
        "task/<uuid:pk>/results",
        (task.TaskResultsView.as_view()),
        name="task-results",
    ),
    path(
        "variables/<parent_id>",
        (variable.all_variables),
        name="all-variables",
    ),
    path(
        "add_variable/<parent_id>",
        (variable.VariableView.as_view()),
        name="variable-create",
    ),
    path(
        "update_variable/<pk>/<parent_id>",
        (variable.UpdateVariableView.as_view()),
        name="variable-update",
    ),
    path(
        "delete_variable/<pk>",
        (variable.delete_variable),
        name="variable-delete",
    ),
    path(
        "detail_variable/<pk>",
        (variable.VariableView.as_view()),
        name="variable-detail",
    ),
    path(
        "environment_select/",
        (environment_select.EnvironmentSelectView.as_view()),
        name="set-environment",
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

account_urlpatterns = [
    path("account/details", account.details, name="account-detail"),
    path(
        "account/disconnect_social",
        account.disconnect_social,
        name="account-disconnect-social",
    ),
    path("account/token/refresh", account.refresh_token, name="token-refresh"),
]

environment_urlpatterns = [
    path(
        "environment/<uuid:pk>",
        (environment.EnvironmentDetailView.as_view()),
        name="environment-detail",
    ),
    path(
        "environment_list/",
        (environment.EnvironmentListView.as_view()),
        name="environment-list",
    ),
    path(
        "environment/<uuid:environment_pk>/user_role/create",
        (environment.EnvironmentUserRoleCreateView.as_view()),
        name="environmentuserrole-create",
    ),
    path(
        "environment/<uuid:environment_pk>/user_role/<int:pk>/delete",
        (environment.EnvironmentUserRoleDeleteView.as_view()),
        name="environmentuserrole-delete",
    ),
    path(
        "environment/<uuid:environment_pk>/user_role/<int:pk>/update",
        (environment.EnvironmentUserRoleUpdateView.as_view()),
        name="environmentuserrole-update",
    ),
]

scheduling_urlpatterns = [
    path(
        "create_schedule/",
        (scheduled_task.ScheduledTaskCreateView.as_view()),
        name="scheduledtask-create",
    ),
    path(
        "schedule/<uuid:pk>",
        (scheduled_task.ScheduledTaskDetailView.as_view()),
        name="scheduledtask-detail",
    ),
    path(
        "schedule/<uuid:pk>/update",
        (scheduled_task.ScheduledTaskUpdateView.as_view()),
        name="scheduledtask-update",
    ),
    path(
        "schedule_list/",
        (scheduled_task.ScheduledTaskListView.as_view()),
        name="scheduledtask-list",
    ),
    path(
        "crontab_minute_param/",
        (scheduled_task.crontab_minute_param),
        name="scheduled-minute-param",
    ),
    path(
        "crontab_hour_param/",
        (scheduled_task.crontab_hour_param),
        name="scheduled-hour-param",
    ),
    path(
        "crontab_day_of_week_param/",
        (scheduled_task.crontab_day_of_week_param),
        name="scheduled-day-of-week-param",
    ),
    path(
        "crontab_day_of_month_param/",
        (scheduled_task.crontab_day_of_month_param),
        name="scheduled-day-of-month-param",
    ),
    path(
        "crontab_month_of_year_param/",
        (scheduled_task.crontab_month_of_year_param),
        name="scheduled-month-of-year-param",
    ),
]

team_urlpatterns = [
    path("team_list/", (team.TeamListView.as_view()), name="team-list"),
    path(
        "team/<uuid:pk>",
        (team.TeamDetailView.as_view()),
        name="team-detail",
    ),
    path(
        "team/<uuid:team_pk>/create",
        (team.TeamUserRoleCreateView.as_view()),
        name="teamuserrole-create",
    ),
    path(
        "team/<uuid:team_pk>/delete/<pk>",
        (team.TeamUserRoleDeleteView.as_view()),
        name="teamuserrole-delete",
    ),
    path(
        "team/<uuid:team_pk>/update/<pk>",
        (team.TeamUserRoleUpdateView.as_view()),
        name="teamuserrole-update",
    ),
    path("users/", (team.get_users), name="get-users"),
]

workflows_urlpatterns = [
    path(
        "workflow_list/",
        (workflow.WorkflowListView.as_view()),
        name="workflow-list",
    ),
    path(
        "workflow/create",
        (workflow.WorkflowCreateView.as_view()),
        name="workflow-create",
    ),
    path(
        "workflow/<uuid:pk>",
        (workflow.WorkflowDetailView.as_view()),
        name="workflow-detail",
    ),
    path(
        "workflow/<uuid:pk>/edit",
        (workflow.WorkflowUpdateView.as_view()),
        name="workflow-update",
    ),
    path(
        "workflow/<uuid:pk>/delete",
        (workflow.WorkflowDeleteView.as_view()),
        name="workflow-delete",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/create",
        (workflow.WorkflowParameterCreateView.as_view()),
        name="workflowparameter-create",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/<uuid:pk>/delete",
        (workflow.WorkflowParameterDeleteView.as_view()),
        name="workflowparameter-delete",
    ),
    path(
        "workflow/<uuid:workflow_pk>/parameter/<uuid:pk>/edit",
        (workflow.WorkflowParameterUpdateView.as_view()),
        name="workflowparameter-edit",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/create",
        (workflow.WorkflowStepCreateView.as_view()),
        name="workflowstep-create",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/delete",
        (workflow.WorkflowStepDeleteView.as_view()),
        name="workflowstep-delete",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/edit",
        (workflow.WorkflowStepUpdateView.as_view()),
        name="workflowstep-edit",
    ),
    path(
        "workflow/<uuid:workflow_pk>/step/<uuid:pk>/move",
        (workflow.move_workflow_step),
        name="workflowstep-move",
    ),
]


"""
Append App URL patterns to a main urlpatterns list.

URL patterns should be grouped by the django app they represent.

For example, there should be a list for all the URLs related to
teams, environments, schedules, tasks, etc.

"""
urlpatterns += account_urlpatterns
urlpatterns += environment_urlpatterns
urlpatterns += scheduling_urlpatterns
urlpatterns += team_urlpatterns
urlpatterns += workflows_urlpatterns
