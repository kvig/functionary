from django.forms import CharField, ModelChoiceField, ModelForm
from django.urls import reverse
from django_celery_beat.validators import (
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)

from core.models import Environment, Function, ScheduledTask


class ScheduledTaskForm(ModelForm):
    scheduled_minute = CharField(
        max_length=60 * 4, label="Minute", initial="*", validators=[minute_validator]
    )
    scheduled_hour = CharField(
        max_length=24 * 4, label="Hour", initial="*", validators=[hour_validator]
    )
    scheduled_day_of_week = CharField(
        max_length=64,
        label="Day of Week",
        initial="*",
        validators=[day_of_week_validator],
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
    function = ModelChoiceField(queryset=Function.active_objects.all(), required=True)

    class Meta:
        model = ScheduledTask

        # NOTE: The order of the fields matters. The clean_<field> methods run based on
        # the order they are defined in the 'fields =' attribute
        fields = [
            "name",
            "environment",
            "description",
            "status",
            "function",
            "parameters",
        ]

    def __init__(
        self,
        environment: Environment = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._setup_field_choices(kwargs.get("instance") is not None)
        self._update_function_queryset(environment)
        self._setup_field_classes()

    def _update_function_queryset(self, environment: Environment):
        if environment:
            function_field = self.fields["function"]
            function_field.queryset = function_field.queryset.filter(
                environment=environment, active=True
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

    def _setup_field_choices(self, is_update: bool) -> None:
        if is_update:
            self.fields["status"].choices = self._get_update_status_choices()
        else:
            self.fields["status"].choices = self._get_create_status_choices()

    def _setup_field_classes(self) -> None:
        for field in self.fields:
            if field not in ["status", "function"]:
                self.fields[field].widget.attrs.update({"class": "form-control"})
            else:
                self.fields[field].widget.attrs.update(
                    {"class": "form-select-control", "role": "menu"}
                )

        self.fields["function"].widget.attrs.update(
            {
                "hx-get": reverse("ui:function-parameters"),
                "hx-target": "#function-parameters",
            }
        )

        self._setup_crontab_fields()

    def _setup_crontab_fields(self):
        """Ugly method to attach htmx properties to the crontab components"""

        crontab_fields = [
            "scheduled_minute",
            "scheduled_hour",
            "scheduled_day_of_week",
            "scheduled_day_of_month",
            "scheduled_month_of_year",
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
