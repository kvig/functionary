from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Function


class FunctionListView(ListView):
    model = Function

    def get_queryset(self):
        """Filters functions not in the environment then sorts based
        on package name, then function name."""

        env_id = self.request.session['environment_id']
        return super().get_queryset().filter(package__environment__id=env_id).order_by('package__name', 'name')


class FunctionDetailView(DetailView):
    model = Function
