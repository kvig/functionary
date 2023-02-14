import django_tables2 as tables
from django.urls import reverse

from ui.tables.meta import BaseMeta


class TeamTable(tables.Table):
    team = tables.Column(
        accessor="name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.id}),
    )

    class Meta(BaseMeta):
        pass
