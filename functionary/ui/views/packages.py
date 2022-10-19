from core.models import Package

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class PackageListView(PermissionedEnvironmentListView):
    model = Package


class PackageDetailView(PermissionedEnvironmentDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")
