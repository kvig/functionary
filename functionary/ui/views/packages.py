from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Function, Package


class PackageListView(ListView):
    model = Package

    def get_queryset(self):
        """Filter packages not in the specified environment."""

        env_id = self.request.session["environment_id"]
        return super().get_queryset().filter(environment__id=env_id)


class PackageDetailView(DetailView):
    model = Package

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["functions"] = Function.objects.filter(package=self.get_object())
        return context
