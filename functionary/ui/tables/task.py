import django_tables2 as tables
from django.urls import reverse

from core.models import Task
from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta


class TaskListTable(tables.Table):
    function = tables.Column(
        linkify=lambda record: reverse("ui:task-detail", kwargs={"pk": record.id}),
    )

    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT,
    )

    class Meta(BaseMeta):
        model = Task
        fields = ("function", "status", "creator", "created_at")
