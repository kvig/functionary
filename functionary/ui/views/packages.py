from core.models import Package

from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class PackageListView(PermissionedEnvironmentListView):
    model = Package


class PackageDetailView(PermissionedEnvironmentDetailView):
    model = Package

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["functions"] = self.get_object().functions.all()
        return context
