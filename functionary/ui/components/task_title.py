from django_unicorn.components import PollUpdate, UnicornView

from core.models import Task


class TaskTitleView(UnicornView):
    polling_enabled = False
    status = "Unknown"

    def get_status(self):
        # Get the ID from the end of the referer URL, alternatively
        # you can parse the body each time and access data.task.pk
        task_id = self.request.headers["Referer"].split("/")[-1]
        self.status = Task.objects.values("status").get(id=task_id)["status"]
        if self.status in ["COMPLETE", "ERROR"]:
            return PollUpdate(disable=True, method="get_status")
