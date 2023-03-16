from django.urls import reverse

from core.models import EnvironmentUserRole
from ui.forms.environments import EnvironmentUserRoleForm
from ui.views.environment.utils import get_user_role
from ui.views.generic import PermissionedUpdateView


class EnvironmentUserRoleUpdateView(PermissionedUpdateView):
    model = EnvironmentUserRole
    permissioned_model = "Environment"
    form_class = EnvironmentUserRoleForm
    template_name = "forms/environment/environmentuserrole_update.html"

    def get_success_url(self) -> str:
        return reverse(
            "ui:environment-detail", kwargs={"pk": self.kwargs.get("environment_pk")}
        )

    def get_initial(self) -> dict:
        environment_user_role: EnvironmentUserRole = self.get_object()
        initial = super().get_initial()
        if role := get_user_role(
            environment_user_role.user, environment_user_role.environment
        ):
            initial["role"] = role
        return initial
