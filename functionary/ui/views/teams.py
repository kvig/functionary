from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.auth import Permission
from core.models import Team, TeamUserRole, Variable


class TeamListView(LoginRequiredMixin, ListView):
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


class TeamDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        context["environments"] = team.environments.all()
        context["users"] = [user_role.user for user_role in team.user_roles.all()]
        context["var_create"] = self.request.user.has_perm(
            Permission.VARIABLE_CREATE, team
        )
        context["var_update"] = self.request.user.has_perm(
            Permission.VARIABLE_UPDATE, team
        )
        context["var_delete"] = self.request.user.has_perm(
            Permission.VARIABLE_DELETE, team
        )
        context["variables"] = (
            team.vars
            if self.request.user.has_perm(Permission.VARIABLE_READ, team)
            else Variable.objects.none()
        )
        return context

    def test_func(self):
        return self.request.user.has_perm(Permission.TEAM_READ, self.get_object())
