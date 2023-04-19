from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import get_object_or_404
from django.urls import reverse

from core.models import Environment, ScheduledTask
from ui.forms import ScheduledTaskForm, TaskParameterForm
from ui.views.generic import PermissionedUpdateView
from ui.views.scheduled_task.utils import get_crontab_schedule


class ScheduledTaskUpdateView(PermissionedUpdateView):
    model = ScheduledTask
    form_class = ScheduledTaskForm
    template_name = "forms/scheduled_task/scheduled_task_edit.html"

    def get_success_url(self) -> str:
        scheduled_task: ScheduledTask = self.get_object()
        return reverse("ui:scheduledtask-detail", kwargs={"pk": scheduled_task.id})

    def get_initial(self) -> dict:
        initial = super().get_initial()
        scheduled_task: ScheduledTask = self.get_object()
        crontab = scheduled_task.periodic_task.crontab
        initial["scheduled_minute"] = crontab.minute
        initial["scheduled_hour"] = crontab.hour
        initial["scheduled_day_of_month"] = crontab.day_of_month
        initial["scheduled_month_of_year"] = crontab.month_of_year
        initial["scheduled_day_of_week"] = crontab.day_of_week
        return initial

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        scheduled_task: ScheduledTask = context["scheduledtask"]
        context["update"] = True
        context["task_parameter_form"] = TaskParameterForm(
            tasked_object=scheduled_task.tasked_object,
            initial=scheduled_task.parameters,
        )
        return context

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        environment = get_object_or_404(
            Environment, id=self.request.session.get("environment_id")
        )
        kwargs["environment"] = environment
        kwargs["tasked_type"] = kwargs["instance"].tasked_type.name
        return kwargs

    def post(self, request: HttpRequest, **kwargs) -> HttpResponse:
        scheduled_task: ScheduledTask = self.get_object()
        data: QueryDict = request.POST.copy()
        data["environment"] = scheduled_task.environment
        data["tasked_object"] = scheduled_task.tasked_object
        data["tasked_id"] = scheduled_task.tasked_object.id
        data["tasked_type"] = ContentType.objects.get_for_model(
            scheduled_task.tasked_object
        )
        task_parameter_form = TaskParameterForm(data["tasked_object"], data)

        if not task_parameter_form.is_valid():
            form = self.get_form()
        else:
            data["parameters"] = task_parameter_form.cleaned_data
            form = ScheduledTaskForm(
                data=data,
                environment=scheduled_task.environment,
                tasked_type=data["tasked_type"].name,
                instance=scheduled_task,
            )
            if form.is_valid():
                form.save()
                scheduled_task.set_status(form.cleaned_data["status"])
                crontab_schedule = get_crontab_schedule(form.cleaned_data)
                scheduled_task.set_schedule(crontab_schedule)

                return HttpResponseRedirect(self.get_success_url())

        context = {
            "scheduledtask": scheduled_task,
            "update": True,
            "form": form,
            "task_parameter_form": task_parameter_form,
        }
        return self.render_to_response(context)
