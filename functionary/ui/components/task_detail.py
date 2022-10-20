from django_unicorn.components import PollUpdate, UnicornView

FINISHED_STATUS = ["COMPLETE", "ERROR"]


class TaskDetailView(UnicornView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["should_refresh"] = self.task.status not in FINISHED_STATUS
        return context

    def refresh_task(self):
        self.task.refresh_from_db()

        if self.task.status in FINISHED_STATUS:
            return PollUpdate(disable=True, method="refresh_task")
