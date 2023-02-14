"""Extensions to the django generic views that add permission based access control and
filtering for the request session's active environment. These are intended for use on
model based views where the model is either directly or indirectly associated with an
environment. That is, the model has a foreign key to `Environment`, or has a foreign key
to another model that itself has a foreign key to `Environment`.

The following views are provided here:

- PermissionedCreateView
- PermissionedListView
- PermissionedDetailView
- PermissionedUpdateView
- PermissionedDeleteView

Each of these is an extension of their similarly named django.views.generic view class.
In addition to the normal generic view behavior, there are three key additional
capabilities:

- The requesting user's permissions are checked against the active environment for the
  session. The permission required to access the endpoint is based on the model for the
  view and the action for the request. For example, a PermissionedCreateView built on
  the Task model would require the TASK_CREATE permission when doing a POST.

- The queryset for the view is automatically filtered by the active environment for the
  session. For PermissionedListView, this means that only results for the active
  environment will be included in the result set. For views that operate on a single
  object (PermissionedDetailView, PermissionedUpdateView, PermissionedDeleteView),
  attempting to access the view for an object outside of the active environment will
  result in a 404 response.

- For views that are served via a nested route, the parent object is also used to filter
  the queryset. To take advantage of this, the nested route must be defined with the
  kwarg for the parent object named `<model>_pk`. For example, the path for a
  WorkflowStep view, which has a parent object of a Workflow would be defined as:

    workflow/<uuid:workflow_pk>/step/<uuid:pk>/edit

  This would result in the base queryset looking something like:

    WorkflowStep.objects.filter(workflow__pk=workflow_pk, pk=pk)

Classes inheriting from any of these base views can optionally define the following
properties:

- environment_through_field: If the view's model does not itself have an environment
    field, but is instead infers its environment through a related object, you can
    declare that here, via a string that will be used as a Queryset filter kwarg. Using
    WorkflowStep as an example again, we would set environment_through_field to
    "workflow".
- permissioned_model: This can be set so that the user's permission is checked against
    a model other than the one defined by the view's model. This is useful if access to
    an object is implied by access to some other model, generally a related model. For
    example, access to view an EnvironmentUserRole may be implied if a user has access
    to view the Environment. In this case, we can set permissioned_model to
    "Environment." Note that the value is a string rather than an actual model class.
    This is so that the model class isn't required to be imported just to use it as the
    permissioned_model. Additionally, setting this value changes the required permission
    from <MODEL>_<ACTION> to <MODEL>_UPDATE, as the operation being performed is treated
    as an update to the permissioned model, rather than a create, update, or delete to
    the view model. For example, deleting a WorkflowStep is treated as an UPDATE to the
    Workflow.
"""
import re
from functools import cache
from typing import Type

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_tables2 import SingleTableView

from core.auth import Operation, Permission
from core.models import Environment


class PermissionedViewMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for building generic (model based) views.

    This provides general utilities for handling the session environment and checking
    user permissions against the environment.
    """

    environment_through_field: str | None = None
    model: Type[models.Model] | None = None
    permissioned_model: str | None = None
    post_action: Operation | None = None

    def _get_permission_for_request(self) -> Permission | None:
        """Determine the required permission for the request based on the request
        method and model
        """
        model_name = (self.permissioned_model or self.model.__name__).upper()

        match self.request.method:
            case "GET":
                action = Operation.READ
            case "POST":
                action = (
                    Operation.UPDATE if self.permissioned_model else self.post_action
                )
            case "DELETE":
                action = (
                    Operation.UPDATE if self.permissioned_model else Operation.DELETE
                )
            case _:
                return None

        return getattr(Permission, f"{model_name}_{action.value}")

    def _get_parent_filter(self) -> dict:
        """For views hosted under a nested route, construct the filter parameters for
        the parent objects
        """
        parent_filter = {}

        for path_var, value in self.kwargs.items():
            if re.match(r"^\w+_pk$", path_var):
                parent_pk_field = path_var.replace("_pk", "__pk")
                parent_filter[parent_pk_field] = value

        return parent_filter

    @cache
    def get_environment(self) -> Environment | None:
        """Retrieve the Environment object for the session's active environment

        Returns:
            The Environment object corresponding to the session "environment_id". None
            is returned if no Environment is found.
        """
        environment_id = self.request.session.get("environment_id")

        try:
            return Environment.objects.get(id=environment_id)
        except Environment.DoesNotExist:
            return None

    def get_queryset(self):
        """Filters the queryset down to the appropriate objects based on the active
        environment for the request
        """

        if self.environment_through_field:
            environment_field = f"{self.environment_through_field}__environment"
        else:
            environment_field = "environment"

        filter_params = {environment_field: self.get_environment()}
        filter_params.update(self._get_parent_filter())

        return super().get_queryset().filter(**filter_params)

    def test_func(self):
        """Verify user access to the endpoint for the requested action"""
        required_permission = self._get_permission_for_request()

        if required_permission:
            return self.request.user.has_perm(
                required_permission, self.get_environment()
            )

        return False


class PermissionedCreateView(PermissionedViewMixin, CreateView):
    """Extended CreateView with active environment permissions checking and queryset
    filtering. See `ui.views.generic` for details."""

    post_action = Operation.CREATE


class PermissionedListView(PermissionedViewMixin, SingleTableView):
    """Extended ListView with active environment permissions checking and queryset
    filtering. See `ui.views.generic` for details."""

    paginate_by = 15
    template_name = "default_list.html"


class PermissionedDetailView(PermissionedViewMixin, DetailView):
    """Extended DetailView with active environment permissions checking and queryset
    filtering. See `ui.views.generic` for details."""

    pass


class PermissionedUpdateView(PermissionedViewMixin, UpdateView):
    """Extended UpdateView with active environment permissions checking and queryset
    filtering. See `ui.views.generic` for details."""

    post_action = Operation.UPDATE


class PermissionedDeleteView(PermissionedViewMixin, DeleteView):
    """Extended DeleteView with active environment permissions checking and queryset
    filtering. See `ui.views.generic` for details."""

    post_action = Operation.DELETE
