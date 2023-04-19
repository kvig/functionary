from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.auth import Permission
from core.models import Environment, Function, Workflow
from ui.forms.tasks import TaskParameterForm, TaskParameterTemplateForm


@require_GET
@login_required
def object_parameters(request: HttpRequest) -> HttpResponse:
    """Used to lazy load a the tasked_object's parameters as a partial.

    Handles the following request parameters:
        function: The id of the function object whose parameters should be rendered
        allow_template_variables: When true, the fields of the generated form will
            accept django template variables syntax (e.g. {{somevariable}}) in addition
            to data of the parameters natural type.
    """
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.SCHEDULEDTASK_CREATE, env):
        return HttpResponseForbidden()

    if (
        allow_template_variables := request.GET.get("allow_template_variables")
    ) and allow_template_variables.lower() == "true":
        form_class = TaskParameterTemplateForm
    else:
        form_class = TaskParameterForm

    if (tasked_id := request.GET.get("tasked_object")) in ["", None]:
        return HttpResponse("Nothing selected to task.")

    tasked_object = Function.objects.filter(id=tasked_id, environment=env).first()
    if not tasked_object:
        tasked_object = get_object_or_404(Workflow, id=tasked_id, environment=env)

    form = form_class(tasked_object=tasked_object)
    return render(request, form.template_name, {"form": form})
