from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Task


class TaskListView(ListView):
    model = Task

    def get_queryset(self):
        """Sorts the objects on creation time."""

        return (super().get_queryset().order_by('-created_at'))


class TaskDetailView(DetailView):
    model = Task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["environments"] = [self.get_object().environment]
        return context
