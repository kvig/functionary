from core.models.scheduled_task import ScheduledTask
from ui.tables.schedule_task import ScheduledTaskTable
from ui.views.generic import PermissionedListView


class ScheduledTaskListView(PermissionedListView):
    model = ScheduledTask
    table_class = ScheduledTaskTable
    template_name = "core/scheduledtask_list.html"
