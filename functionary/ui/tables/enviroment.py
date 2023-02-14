import django_tables2 as tables
from django.urls import reverse

from ui.tables.meta import BaseMeta


class EnvironmentTable(tables.Table):
    environment = tables.Column(
        accessor="name",
        linkify=lambda record: reverse(
            "ui:environment-detail", kwargs={"pk": record.id}
        ),
    )
    team = tables.Column(
        accessor="team__name",
        linkify=lambda record: reverse("ui:team-detail", kwargs={"pk": record.team.id}),
    )

    class Meta(BaseMeta):
        pass
