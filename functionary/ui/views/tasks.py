from core.models import Task

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class TaskListView(PermissionedEnvironmentListView):
    model = Task
    order_by_fields = ["-created_at"]
    queryset = Task.objects.select_related("environment", "function", "creator").all()


class TaskDetailView(PermissionedEnvironmentDetailView):
    model = Task

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "environment", "creator", "function", "taskresult", "environment__team"
            )
        )
