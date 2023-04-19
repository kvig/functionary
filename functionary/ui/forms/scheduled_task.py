from django.contrib.contenttypes.models import ContentType
from django.db.models import Value
from django.forms import CharField, ModelChoiceField, ModelForm
from django.urls import reverse
from django_celery_beat.validators import (
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)

from core.models import Environment, Function, ScheduledTask, Workflow


class ScheduledTaskForm(ModelForm):
    scheduled_minute = CharField(
        max_length=60 * 4, label="Minute", initial="*", validators=[minute_validator]
    )
    scheduled_hour = CharField(
        max_length=24 * 4, label="Hour", initial="*", validators=[hour_validator]
    )
    scheduled_day_of_month = CharField(
        max_length=31 * 4,
        label="Day of Month",
        initial="*",
        validators=[day_of_month_validator],
    )
    scheduled_month_of_year = CharField(
        max_length=64,
        label="Month of Year",
        initial="*",
        validators=[month_of_year_validator],
    )
    scheduled_day_of_week = CharField(
        max_length=64,
        label="Day of Week",
        initial="*",
        validators=[day_of_week_validator],
    )
    tasked_object = ModelChoiceField(
        queryset=Function.active_objects.all(),
        required=True,
    )

    class Meta:
        model = ScheduledTask

        # NOTE: The order of the fields matters. The clean_<field> methods run based on
        # the order they are defined in the 'fields =' attribute
        fields = [
            "name",
            "environment",
            "description",
            "status",
            "tasked_object",
            "tasked_type",
            "tasked_id",
            "parameters",
        ]

    def __init__(
        self,
        environment: Environment = None,
        tasked_type: str = None,
        *args,
        **kwargs,
    ):
        self._update_tasked_object_queryset(environment, tasked_type)
        super().__init__(*args, **kwargs)
        self._setup_field_choices(kwargs.get("instance") is not None)
        self._setup_field_classes()

    def _update_tasked_object_queryset(
        self, environment: Environment, tasked_type: str
    ):
        if tasked_type:
            if tasked_type not in ["function", "workflow"]:
                raise ValueError("Incorrect tasked type")
            object_manager = (
                Function.active_objects
                if tasked_type == "function"
                else Workflow.active_objects
            )
            self.declared_fields["tasked_object"].queryset = object_manager.filter(
                environment=environment
            )
            return

        if self.instance:
            object_manager = (
                Function.active_objects
                if isinstance(self.instance.tasked_object, Function)
                else Workflow.active_objects
            )
            self.fields["tasked_object"].queryset = object_manager.filter(
                environment=environment
            )
            return

        if environment:
            tasked_object = self.instance.tasked_object
            tasked_object_field = self.fields["tasked_object"]
            if tasked_object:
                tasked_type = tasked_type.__class__
            tasked_object_field.queryset = (
                Workflow.active_objects.filter(environment=environment)
                if tasked_type == "workflow"
                else Function.active_objects.filter(environment=environment)
            )

    def _get_create_status_choices(self) -> list:
        """Don't want user to set status to Error"""
        choices = [
            choice
            for choice in ScheduledTask.STATUS_CHOICES
            if choice[0] != ScheduledTask.ERROR
        ]
        return choices

    def _get_update_status_choices(self) -> list:
        """Don't want user to set status to Error or Pending"""
        choices = [
            choice
            for choice in ScheduledTask.STATUS_CHOICES
            if choice[0] not in [ScheduledTask.ERROR, ScheduledTask.PENDING]
        ]
        return choices

    def _get_tasked_object_choices(self) -> list:
        choices = list(Function.active_objects.all()) + list(
            Workflow.active_objects.all()
        )
        return [(choice.pk, choice) for choice in choices]

    def _setup_field_choices(self, is_update: bool) -> None:
        if is_update:
            self.fields["status"].choices = self._get_update_status_choices()
            self.fields["tasked_object"].choices = [
                (self.instance.tasked_object.id, self.instance.tasked_object)
            ]
        else:
            self.fields["status"].choices = self._get_create_status_choices()

    def _setup_field_classes(self) -> None:
        for field in self.fields:
            if field not in ["status", "tasked_obj"]:
                self.fields[field].widget.attrs.update({"class": "form-control"})
            else:
                self.fields[field].widget.attrs.update(
                    {"class": "form-select-control", "role": "menu"}
                )

        # self.fields["tasked_object"].widget.attrs.update(
        #     {
        #         "hx-get": reverse("ui:scheduledtask-object-parameters"),
        #         "hx-target": "#tasked_object-parameters",
        #     }
        # )

        self._setup_crontab_fields()

    def _setup_crontab_fields(self):
        """Ugly method to attach htmx properties to the crontab components"""

        crontab_fields = [
            "scheduled_minute",
            "scheduled_hour",
            "scheduled_day_of_month",
            "scheduled_month_of_year",
            "scheduled_day_of_week",
        ]

        for field in crontab_fields:
            field_id = f"id_{field}"
            field_url = field.replace("_", "-")
            self.fields[field].widget.attrs.update(
                {
                    "hx-post": reverse(f"ui:{field_url}-param"),
                    "hx-trigger": "keyup delay:500ms",
                    "hx-target": f"#{field_id}_errors",
                }
            )

    def clean_tasked_object(self):
        tasked_object = (
            self.cleaned_data["tasked_object"] or self.instance.tasked_object
        )

        tasked_type = ContentType.objects.get_for_model(type(tasked_object))
        self.cleaned_data["tasked_id"] = tasked_object.id
        self.cleaned_data["tasked_object"] = tasked_object
        self.cleaned_data["tasked_type"] = tasked_type
        return self.cleaned_data["tasked_object"]

    def clean_tasked_type(self):
        tasked_object = (
            self.cleaned_data["tasked_object"] or self.instance.tasked_object
        )

        tasked_type = ContentType.objects.get_for_model(tasked_object)
        return tasked_type

    def clean_tasked_id(self):
        tasked_object = (
            self.cleaned_data["tasked_object"] or self.instance.tasked_object
        )

        return tasked_object.id
