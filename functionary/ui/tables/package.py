import django_tables2 as tables
from django.urls import reverse

from core.models import Package
from ui.tables.meta import BaseMeta


class PackageTable(tables.Table):
    name = tables.Column(
        linkify=lambda record: reverse("ui:package-detail", kwargs={"pk": record.id}),
    )

    class Meta(BaseMeta):
        model = Package
        fields = ("name", "summary")
