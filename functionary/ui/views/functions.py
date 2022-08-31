from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Function


class FunctionListView(ListView):
    model = Function

    def get_queryset(self):
        """Sorts based on package name, then function name."""

        return (super().get_queryset().order_by('package__name', 'name'))


class FunctionDetailView(DetailView):
    model = Function
