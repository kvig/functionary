from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.models import Team


class TeamListView(ListView):
    model = Team


class TeamDetailView(DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        context["environments"] = team.environments.all()
        context["users"] = [user_role.user for user_role in team.user_roles.all()]
        return context
