from core.models import Workflow
from ui.tables.workflow import WorkflowTable
from ui.views.generic import PermissionedListView


class WorkflowListView(PermissionedListView):
    """List view for the Workflow model"""

    model = Workflow
    ordering = ["name"]
    table_class = WorkflowTable
    template_name = "core/workflow_list.html"
