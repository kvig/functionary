from core.models import Package
from ui.tables.package import PackageFilter, PackageTable

from .generic import PermissionedDetailView, PermissionedListView


class PackageListView(PermissionedListView):
    model = Package
    table_class = PackageTable
    filterset_class = PackageFilter
    extra_context = {"breadcrumb": "Package List"}
    queryset = Package.active_objects.all()


class PackageDetailView(PermissionedDetailView):
    model = Package

    def get_queryset(self):
        return super().get_queryset().select_related("environment")
