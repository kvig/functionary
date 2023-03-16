from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView

from core.auth import Permission
from core.models import Environment, Package, Variable

from .utils import get_user_roles


class EnvironmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Environment
    queryset = Environment.objects.select_related("team").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        env = self.get_object()

        context["packages"] = Package.objects.filter(environment=env)
        context["user_details"] = get_user_roles(env)
        context["environment_id"] = str(env.id)
        context["variables"] = (
            env.vars
            if self.request.user.has_perm(Permission.VARIABLE_READ, env)
            else Variable.objects.none()
        )
        return context

    def test_func(self):
        return self.request.user.has_perm(
            Permission.ENVIRONMENT_READ, self.get_object()
        )
