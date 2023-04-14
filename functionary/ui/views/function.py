from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.auth import Permission
from core.models import Environment, Function, Task, Workflow
from core.utils.minio import S3Error, handle_file_parameters
from core.utils.tasking import start_task
from ui.forms.tasks import TaskParameterForm, TaskParameterTemplateForm
from ui.tables.function import FunctionFilter, FunctionTable

from .generic import PermissionedDetailView, PermissionedListView


class FunctionListView(PermissionedListView):
    model = Function
    ordering = ["package__name", "name"]
    table_class = FunctionTable
    filterset_class = FunctionFilter
    queryset = Function.active_objects.select_related("package")
    extra_context = {"breadcrumb": "Functions"}


class FunctionDetailView(PermissionedDetailView):
    model = Function
    environment_through_field = "package"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "package", "package__environment", "package__environment__team"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        function = self.object
        env = function.environment

        missing_variables = []
        if function.variables:
            all_vars = list(env.variables.values_list("name", flat=True))
            missing_variables = [
                var for var in function.variables if var not in all_vars
            ]

        context["missing_variables"] = missing_variables

        if self.request.user.has_perm(Permission.TASK_CREATE, env):
            context["form"] = TaskParameterForm(function)

        return context


@require_POST
@login_required
def execute(request: HttpRequest) -> HttpResponse:
    status_code = None
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    data = request.POST

    if tasked_object_id := data.get("function_id"):
        tasked_object = get_object_or_404(
            Function, id=tasked_object_id, environment=env
        )
    elif tasked_object_id := data.get("workflow_id"):
        tasked_object = get_object_or_404(
            Workflow, id=tasked_object_id, environment=env
        )
    else:
        return HttpResponseBadRequest("function_id or workflow_id is required")

    form = TaskParameterForm(tasked_object, data, files=request.FILES)

    if form.is_valid():
        # Clean the task fields before saving the Task
        task = None
        try:
            # Create the new Task, the validated parameters are in form.cleaned_data
            task = Task(
                environment=env,
                creator=request.user,
                tasked_object=tasked_object,
                parameters=form.cleaned_data,
                return_type=getattr(tasked_object, "return_type", None),
            )
            task.clean()
            handle_file_parameters(task, request)
        except ValidationError:
            task = None
            status_code = 400
            form.add_error(
                None,
                ValidationError(
                    "The given parameters do not conform to function schema.",
                    code="invalid",
                ),
            )
        except S3Error:
            task = None
            status_code = 503
            form.add_error(
                None,
                (
                    "Unable to upload file; please try again. "
                    "If the problem persists, contact your system administrator."
                ),
            )

        if task:
            start_task(task)

            # Redirect to the newly created task:
            return HttpResponseRedirect(reverse("ui:task-detail", args=(task.id,)))

    context = {}
    context["form"] = form

    if isinstance(tasked_object, Function):
        context["function"] = tasked_object
        template = "core/function_detail.html"
    else:
        context["workflow"] = tasked_object
        template = "core/workflow_task.html"

    return render(request, template, context, status=status_code)


@require_GET
@login_required
def function_parameters(request: HttpRequest) -> HttpResponse:
    """Used to lazy load a function's parameters as a partial.

    Handles the following request parameters:
        function: The id of the function object whose parameters should be rendered
        allow_template_variables: When true, the fields of the generated form will
            accept django template variables syntax (e.g. {{somevariable}}) in addition
            to data of the parameters natural type.
    """
    env = Environment.objects.get(id=request.session.get("environment_id"))

    if not request.user.has_perm(Permission.TASK_CREATE, env):
        return HttpResponseForbidden()

    if request.GET.get("allow_template_variables") == "true":
        form_class = TaskParameterTemplateForm
    else:
        form_class = TaskParameterForm

    if (function_id := request.GET.get("function")) in ["", None]:
        return HttpResponse("No function selected.")

    function = get_object_or_404(Function, id=function_id, environment=env)

    form = form_class(tasked_object=function)
    return render(request, form.template_name, {"form": form})
