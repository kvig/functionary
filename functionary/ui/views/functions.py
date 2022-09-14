from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.auth import Permission
from core.models import Environment, Function, Task

from ..forms.forms import TaskParameterForm
from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class FunctionListView(PermissionedEnvironmentListView):
    model = Function
    environment_through_field = "package"
    order_by_fields = ["package__name", "name"]


class FunctionDetailView(PermissionedEnvironmentDetailView):
    model = Function
    environment_through_field = "package"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        env = Environment.objects.get(id=self.request.session.get("environment_id"))
        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            form = TaskParameterForm(self.get_object())

            context["form"] = form.render("forms/task_parameters.html")
        return context


@require_POST
@login_required
def execute(request) -> HttpResponse:
    func = None
    form = None

    env = Environment.objects.get(id=request.session.get("environment_id"))
    if request.user.has_perm(Permission.TASK_CREATE, env):
        func = Function.objects.get(id=request.POST["function_id"])
        form = TaskParameterForm(func, request.POST)

        if form.is_valid():
            # Create the new Task, the validated parameters are in form.cleaned_data
            Task.objects.create(
                environment=env,
                creator=request.user,
                function=func,
                parameters=form.cleaned_data,
            )

            # redirect to a new URL:
            return HttpResponseRedirect(reverse("ui:task-list"))

    return HttpResponseForbidden()
