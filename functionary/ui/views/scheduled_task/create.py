from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from core.models import Environment, Function, ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.generic import PermissionedCreateView

from .utils import get_crontab_schedule


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
        return kwargs

    def get(self, *args, **kwargs):
        environment_id = self.request.session.get("environment_id")
        if not Function.active_objects.filter(environment=environment_id).exists():
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
        data["function"] = get_object_or_404(Function, id=data["function"])
        data["status"] = ScheduledTask.PENDING

        task_parameter_form = TaskParameterForm(data["function"], data)

        if not task_parameter_form.is_valid():
            scheduled_task_form = self.get_form()
        else:
            data["parameters"] = task_parameter_form.cleaned_data
            scheduled_task_form = ScheduledTaskForm(
                data=data,
                environment=data["environment"],
            )
            if scheduled_task_form.is_valid():
                scheduled_task = _create_scheduled_task(
                    request,
                    scheduled_task_form.cleaned_data,
                    task_parameter_form.cleaned_data,
                )
                return HttpResponseRedirect(
                    reverse("ui:scheduledtask-detail", kwargs={"pk": scheduled_task.id})
                )

        context = {
            "form": scheduled_task_form,
            "task_parameter_form": task_parameter_form,
        }
        return self.render_to_response(context)


def _create_scheduled_task(
    request: HttpRequest, schedule_form_data: dict, task_params: dict
) -> ScheduledTask:
    """Helper function for creating scheduled task"""
    with transaction.atomic():
        scheduled_task = ScheduledTask.objects.create(
            name=schedule_form_data["name"],
            environment=schedule_form_data["environment"],
            description=schedule_form_data["description"],
            function=schedule_form_data["function"],
            parameters=task_params,
            creator=request.user,
        )
        crontab_schedule = get_crontab_schedule(schedule_form_data)
        scheduled_task.set_schedule(crontab_schedule)
        scheduled_task.activate()
    return scheduled_task
