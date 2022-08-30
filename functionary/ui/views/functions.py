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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        env = self.get_object().package.environment

        context["teams"] = [env.team]
        context["environments"] = [env]

        return context
