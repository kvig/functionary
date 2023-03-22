from core.models import Workflow
from ui.tables.workflow import WorkflowFilter, WorkflowTable
from ui.views.generic import PermissionedListView


class WorkflowListView(PermissionedListView):
    """List view for the Workflow model"""

    model = Workflow
    ordering = ["name"]
    table_class = WorkflowTable
    template_name = "core/workflow_list.html"
    filterset_class = WorkflowFilter
    queryset = Workflow.objects.select_related("environment", "creator")
