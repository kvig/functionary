from core.models import Task

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class TaskListView(PermissionedEnvironmentListView):
    model = Task
    order_by_fields = ["-created_at"]


class TaskDetailView(PermissionedEnvironmentDetailView):
    model = Task
