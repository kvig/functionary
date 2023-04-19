import django_filters
import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.urls import reverse
from django.utils.html import format_html

from core.models import Function, ScheduledTask, Workflow
from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta

FIELDS = ("name", "task", "last_run", "schedule", "status", "type")
FUNCTION = Function.__name__.lower()
WORKFLOW = Workflow.__name__.lower()
TYPE_CHOICES = (
    (FUNCTION, FUNCTION),
    (WORKFLOW, WORKFLOW),
)


class ScheduledTaskFilter(django_filters.FilterSet):
    name = django_filters.Filter(label="Name", lookup_expr="startswith")
    task = django_filters.Filter(method="filter_task", label="Task")
    type = django_filters.ChoiceFilter(
        field_name="tasked_type__model", label="Type", choices=TYPE_CHOICES
    )

    class Meta:
        model = ScheduledTask
        fields = FIELDS
        exclude = ("schedule", "last_run")

    def filter_task(self, queryset, task, value):
        """Generate queryset for filtering by tasked_object name"""
        function_ids = Function.objects.filter(name__startswith=value).values_list(
            "id", flat=True
        )
        workflow_ids = Workflow.objects.filter(name__startswith=value).values_list(
            "id", flat=True
        )
        function_ct = ContentType.objects.get_for_model(Function)
        workflow_ct = ContentType.objects.get_for_model(Workflow)

        function_filter = Q(tasked_type=function_ct, tasked_id__in=function_ids)
        workflow_filter = Q(tasked_type=workflow_ct, tasked_id__in=workflow_ids)

        return queryset.filter(function_filter | workflow_filter)


def generateLastRunUrl(record):
    if record.most_recent_task:
        return reverse("ui:task-detail", kwargs={"pk": record.most_recent_task})
    return None


class ScheduledTaskTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse(
            "ui:scheduledtask-detail", kwargs={"pk": record.id}
        ),
    )
    task = tables.Column(
        accessor="tasked_object__name",
        orderable=False,
    )
    last_run = tables.DateTimeColumn(
        accessor="most_recent_task__created_at",
        verbose_name="Last Run",
        linkify=lambda record: generateLastRunUrl(record),
        format=DATETIME_FORMAT,
    )
    schedule = tables.Column(
        accessor="periodic_task__crontab", verbose_name="Schedule", orderable=False
    )
    edit_button = tables.Column(
        accessor="id",
        orderable=False,
        verbose_name="",
    )

    class Meta(BaseMeta):
        model = ScheduledTask
        fields = FIELDS
        orderable = True
        exclude = ("type",)

    def render_task(self, value, record):
        icon = "cube" if isinstance(record.tasked_object, Function) else "diagram-next"
        return format_html(f"<i class='fa fa-{icon}'></i> {value}")

    def render_edit_button(self, value, record):
        return format_html(
            '<a class="fa fa-pencil-alt text-info" role="button" title="Edit Schedule" '
            f'href="{reverse("ui:scheduledtask-update", kwargs={"pk": record.id})}">'
            "</a>"
        )

    def render_schedule(self, value):
        crontab = " ".join(
            [
                value.minute,
                value.hour,
                value.day_of_month,
                value.month_of_year,
                value.day_of_week,
            ]
        )

        return format_html(
            "<span tabindex='0' data-bs-toggle='popover' data-bs-trigger='hover focus' "
            + "data-bs-content='{}'>{}<i class='fa fa-xs fa-fw fa-info-circle text-info"
            + " ms-2'></i><span class='visually-hidden'>{}</span></span>",
            value.human_readable,
            crontab,
            value.human_readable,
        )
