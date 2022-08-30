from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Environment, Team, TeamUserRole


class TeamListView(ListView):
    model = Team


class TeamDetailView(DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["environments"] = Environment.objects.filter(team=self.get_object())
        context["users"] = [
            x.user for x in TeamUserRole.objects.filter(team=self.get_object())
        ]
        return context
