import django_tables2 as tables
from django.urls import reverse

from core.models import Workflow
from ui.tables.meta import BaseMeta


class WorkflowTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:workflow-detail", kwargs={"pk": record.id}),
    )

    class Meta(BaseMeta):
        model = Workflow
        fields = ("name", "description", "creator")
