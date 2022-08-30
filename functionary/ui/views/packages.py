from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Function, Package, TeamUserRole


class PackageListView(ListView):
    model = Package


class PackageDetailView(DetailView):
    model = Package

    def get_context_data(self, **kwargs):
        teams = [t.team for t in TeamUserRole.objects.filter(user=self.request.user)]
        context = super().get_context_data(**kwargs)
        context["functions"] = Function.objects.filter(package=self.get_object())
        context["teams"] = teams
        return context
