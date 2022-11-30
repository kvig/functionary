from builder.models import Build

from .tasks import FINISHED_STATUS
from .view_base import (
    PermissionedEnvironmentDetailView,
    PermissionedEnvironmentListView,
)


class BuildListView(PermissionedEnvironmentListView):
    model = Build
    order_by_fields = ["-created_at"]
    queryset = Build.objects.select_related("creator", "package").all()


class BuildDetailView(PermissionedEnvironmentDetailView):
    model = Build
    queryset = Build.objects.select_related("creator", "package").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        completed = self.object.status in FINISHED_STATUS

        context["completed"] = completed
        if hasattr(self.object, "buildlog"):
            context["build_log"] = self.object.buildlog

        return context
