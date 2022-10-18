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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["should_refresh"] = context["task"].status not in [
            "COMPLETE",
            "ERROR",
        ]
        return context
