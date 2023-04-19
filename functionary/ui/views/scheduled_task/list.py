from core.models.scheduled_task import ScheduledTask
from ui.tables.schedule_task import ScheduledTaskFilter, ScheduledTaskTable
from ui.views.generic import PermissionedListView


class ScheduledTaskListView(PermissionedListView):
    """List view for the ScheduledTask model"""

    model = ScheduledTask
    ordering = ["name"]
    table_class = ScheduledTaskTable
    template_name = "core/scheduledtask_list.html"
    filterset_class = ScheduledTaskFilter
    queryset = ScheduledTask.objects.select_related(
        "environment",
        "creator",
        "most_recent_task",
        "periodic_task",
        "tasked_type",
    ).prefetch_related("tasked_object")
