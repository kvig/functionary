from django.shortcuts import get_object_or_404
from django.urls import reverse

from core.models import Environment, EnvironmentUserRole, User
from ui.forms.environments import EnvironmentUserRoleForm
from ui.views.environment.utils import get_user_role
from ui.views.generic import PermissionedCreateView


class EnvironmentUserRoleCreateView(PermissionedCreateView):
    model = EnvironmentUserRole
    permissioned_model = "Environment"
    form_class = EnvironmentUserRoleForm
    template_name = "forms/environment/environmentuserrole_create.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:environment-detail", kwargs={"pk": self.kwargs.get("environment_pk")}
        )

    def get_context_data(self, *args, **kwargs) -> dict:
        context = super().get_context_data(*args, **kwargs)
        user_id = self.request.GET.get("user_id")
        environment_id = self.kwargs.get("environment_pk")
        user = get_object_or_404(User, id=user_id) if user_id else None

        context["environment_id"] = environment_id
        context["user_id"] = user_id
        context["username"] = user.username if user_id else None
        return context

    def get_initial(self) -> dict:
        """Replace role in form with the user's effective role for the environment"""
        initial = super().get_initial()
        if not (user_id := self.request.GET.get("user_id")):
            return initial

        environment_id = self.kwargs.get("environment_pk")
        user = get_object_or_404(User, id=user_id)
        environment = get_object_or_404(Environment, id=environment_id)

        initial["role"] = get_user_role(user, environment)
        return initial
