from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Environment, Package


class EnvironmentListView(ListView):
    model = Environment

    def get_queryset(self):
        """Sorts based on team name, then env name."""

        return super().get_queryset().order_by("team__name", "name")


class EnvironmentDetailView(DetailView):
    model = Environment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["packages"] = Package.objects.filter(environment=self.get_object())
        return context


@require_POST
def set_environment_id(request):
    request.session["environment_id"] = request.POST["environment_id"]
    next = request.GET.get("next")
    if not next:
        next = "/ui/"
    return redirect(next)
