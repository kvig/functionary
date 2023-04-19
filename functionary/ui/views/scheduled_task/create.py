from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django_htmx.http import HttpResponseClientRedirect

from core.auth import Permission
from core.models import Environment, Function, ScheduledTask, Workflow
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.generic import PermissionedCreateView, PermissionedViewMixin

from .utils import get_crontab_schedule


def _get_tasked_object(data):
    tasked_id = data["tasked_object"]
    tasked_type = data["tasked_type"]
    tasked_obj = None

    if tasked_type == "function" or not tasked_type:
        try:
            tasked_obj = (
                Function.objects.get(id=tasked_id)
                if not tasked_type
                else get_object_or_404(Function, id=tasked_id)
            )
            tasked_type = ContentType.objects.get_for_model(tasked_obj)
        except Exception:
            pass
    if tasked_type == "workflow" or not tasked_type:
        tasked_obj = get_object_or_404(Workflow, id=tasked_id)
        tasked_type = ContentType.objects.get_for_model(tasked_obj)

    return (tasked_obj, tasked_id, tasked_type)


class ScheduledTaskCreateView(PermissionedCreateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/scheduled_task/scheduled_task_edit.html"

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        kwargs["environment"] = environment
        kwargs["tasked_type"] = self.data["tasked_type"]
        return kwargs

    def get(self, *args, **kwargs):
        environment_id = self.request.session.get("environment_id")
        if (
            not Function.active_objects.filter(environment=environment_id).exists()
            and not Workflow.active_objects.filter(environment=environment_id).exists()
        ):
            messages.warning(
                self.request,
                "No available functions to schedule in current environment.",
            )
            return redirect("ui:scheduledtask-list")
        return super().get(*args, **kwargs)

    def post(self, request: HttpRequest) -> HttpResponse:
        data = request.POST.copy()
        data["environment"] = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        tasked_obj, tasked_id, tasked_type = _get_tasked_object(data)
        data["tasked_object"] = tasked_obj
        data["tasked_id"] = tasked_id
        data["tasked_type"] = tasked_type

        data["status"] = ScheduledTask.PENDING

        task_parameter_form = TaskParameterForm(tasked_obj, data)
        if "initial" not in data and task_parameter_form.is_valid():
            data["parameters"] = task_parameter_form.cleaned_data

        scheduled_task_form = ScheduledTaskForm(
            data["environment"],
            tasked_type.name,
            data=data,
        )
        if "initial" not in data:
            if scheduled_task_form.is_valid():
                scheduled_task = _create_scheduled_task(
                    request,
                    scheduled_task_form.cleaned_data,
                    task_parameter_form.cleaned_data,
                )
                return HttpResponseRedirect(
                    reverse(
                        "ui:scheduledtask-detail",
                        kwargs={
                            "pk": scheduled_task.id,
                        },
                    )
                )

        context = {
            "form": scheduled_task_form,
            "task_parameter_form": task_parameter_form,
        }
        return self.render_to_response(context, status=200)


def _create_scheduled_task(
    request: HttpRequest, schedule_form_data: dict, task_params: dict
) -> ScheduledTask:
    """Helper function for creating scheduled task"""
    with transaction.atomic():
        scheduled_task = ScheduledTask.objects.create(
            name=schedule_form_data["name"],
            environment=schedule_form_data["environment"],
            description=schedule_form_data["description"],
            tasked_object=schedule_form_data["tasked_object"],
            parameters=task_params,
            creator=request.user,
        )
        crontab_schedule = get_crontab_schedule(schedule_form_data)
        scheduled_task.set_schedule(crontab_schedule)
        scheduled_task.activate()
    return scheduled_task


class ScheduleCreateView(PermissionedCreateView):
    """Create view for the ScheduledTask model"""

    model = ScheduledTask
    template_name = "forms/scheduled_task/scheduled_task_create.html"
    fields = ["name", "description", "environment"]

    def get_context_data(self, **kwargs):
        """Custom context which includes the Workflow"""
        context = super().get_context_data(**kwargs)
        objects = (
            Workflow.active_objects.all()
            if kwargs.get("tasked_type", "Function") == "Workflow"
            else Function.active_objects.all()
        )
        context["tasked_objects"] = objects.filter(environment=self.get_environment())
        context["tasked_type"] = kwargs.get("tasked_type", "function")

        return context

    def form_valid(self, form):
        """Valid form handler"""
        form.instance.creator = self.request.user
        form.save()

        success_url = reverse(
            "ui:schedulted-task-detail", kwargs={"pk": form.instance.pk}
        )

        return HttpResponseClientRedirect(success_url)

    def test_func(self):
        # On GET, the session environment is checked.
        # On POST, the actual environment value from the form is checked.
        environment_id = self.request.POST.get(
            "environment"
        ) or self.request.session.get("environment_id")
        environment = Environment.objects.get(id=environment_id)

        return self.request.user.has_perm(Permission.SCHEDULEDTASK_CREATE, environment)


class TaskedObjectsView(PermissionedViewMixin, TemplateView):
    """Mixin for shared logic related to creation and update of the Scheduled Tasked Object"""

    model = ScheduledTask
    permissioned_model = "ScheduledTask"
    required_permission = Permission.SCHEDULEDTASK_CREATE
    template_name = "partials/scheduled_task/tasked_object_chooser.html"

    def get_context_data(self, **kwargs):
        """Custom context which includes the Workflow"""
        environment_id = self.request.session.get("environment_id")
        if (
            not Function.active_objects.filter(environment=environment_id).exists()
            and not Workflow.active_objects.filter(environment=environment_id).exists()
        ):
            messages.warning(
                self.request,
                "No available functions to schedule in current environment.",
            )

        context = super().get_context_data(**kwargs)
        objects = (
            Workflow.active_objects.all()
            if kwargs["tasked_type"] == "workflow"
            else Function.active_objects.all()
        )
        context["tasked_objects"] = objects.filter(environment=self.get_environment())
        context["tasked_type"] = kwargs["tasked_type"] or "function"

        return context
