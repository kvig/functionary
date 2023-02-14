import django_tables2 as tables
from django.urls import reverse

from builder.models import Build
from ui.tables import DATETIME_FORMAT
from ui.tables.meta import BaseMeta


class BuildTable(tables.Table):
    package__name = tables.Column(
        linkify=lambda record: reverse("ui:build-detail", kwargs={"pk": record.id}),
    )
    created_at = tables.DateTimeColumn(
        format=DATETIME_FORMAT,
    )

    class Meta(BaseMeta):
        model = Build
        fields = ("package__name", "status", "created_at", "creator")
