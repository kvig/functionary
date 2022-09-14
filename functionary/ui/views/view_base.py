from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.auth import Permission
from core.models import Environment


class PermissionedEnvironmentListView(LoginRequiredMixin, ListView):
    model_field = "environment"
    environment_through_field = None
    order_by_fields = ["name"]

    def get_queryset(self):
        """Filters out object not in the environment then sorts based
        on the value of order_by_fields."""

        env_id = self.request.session["environment_id"]
        env_is_selected = len(env_id) > 2
        env = Environment.objects.get(id=env_id) if env_is_selected else None
        if env:
            if self.request.user.has_perm(Permission.ENVIRONMENT_READ, env):
                prefix = (
                    f"{self.environment_through_field}__"
                    if self.environment_through_field
                    else ""
                )
                filter_param_dict = {f"{prefix}environment": env}
                return (
                    super()
                    .get_queryset()
                    .filter(**filter_param_dict)
                    .order_by(*self.order_by_fields)
                )
        return super().get_queryset().none()


class PermissionedEnvironmentDetailView(
    LoginRequiredMixin, UserPassesTestMixin, DetailView
):
    environment_through_field = None

    def test_func(self):
        env = None
        if self.environment_through_field:
            env = getattr(self.get_object(), self.environment_through_field).environment
        else:
            env = self.get_object().environment

        return self.request.user.has_perm(Permission.ENVIRONMENT_READ, env)
