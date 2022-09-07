from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Task


class TaskListView(ListView):
    model = Task

    def get_queryset(self):
        """Filters tasks not in the environment then sorts the
        objects on creation time."""

        env_id = self.request.session["environment_id"]
        return (
            super()
            .get_queryset()
            .filter(environment__id=env_id)
            .order_by("-created_at")
        )


class TaskDetailView(DetailView):
    model = Task
