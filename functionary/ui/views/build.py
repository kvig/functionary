from builder.models import Build
from ui.tables.build import BuildTable

from .generic import PermissionedDetailView, PermissionedListView
from .task import FINISHED_STATUS


class BuildListView(PermissionedListView):
    model = Build
    permissioned_model = "Package"
    ordering = ["-created_at"]
    table_class = BuildTable


class BuildDetailView(PermissionedDetailView):
    model = Build
    permissioned_model = "Package"
    queryset = Build.objects.select_related("creator", "package").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        completed = self.object.status in FINISHED_STATUS

        context["completed"] = completed
        if hasattr(self.object, "buildlog"):
            context["build_log"] = self.object.buildlog

        return context
