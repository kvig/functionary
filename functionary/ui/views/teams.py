from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.auth import Permission
from core.models import Team, TeamUserRole


class TeamListView(ListView):
    model = Team

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        if self.request.user.is_superuser:
            return super().get_queryset().order_by("name")
        else:
            teams = TeamUserRole.objects.filter(user=self.request.user).values(
                "team_id"
            )
            return Team.objects.filter(id__in=[team["team_id"] for team in teams])


class TeamDetailView(UserPassesTestMixin, DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        context["environments"] = team.environments.all()
        context["users"] = [user_role.user for user_role in team.user_roles.all()]
        return context

    def test_func(self):
        return self.request.user.has_perm(Permission.TEAM_READ, self.get_object())
