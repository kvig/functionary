""" Scheduled Task model """
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from core.models import ModelSaveHookMixin
from core.utils.parameter import validate_parameters


class ScheduledTask(ModelSaveHookMixin, models.Model):
    """A ScheduledTask is the scheduled execution of a task
    This model should always be queried with environment as one of the filter
    parameters. The indices are intentionally setup this way as all requests for task
    data happen in the context of a specific environment.
    Attributes:
        id: unique identifier (UUID)
        function: the function that this task is an execution of
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        parameters: JSON representing the parameters that will be passed to the function
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
        periodic_task: The celery-beat periodic-task associated with this scheduled task
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    ARCHIVED = "ARCHIVED"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (ERROR, "Error"),
        (ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
    function = models.ForeignKey(
        to="Function", on_delete=models.CASCADE, related_name="scheduled_tasks"
    )
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    parameters = models.JSONField(encoder=DjangoJSONEncoder, blank=True, default=dict)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    most_recent_task = models.ForeignKey(
        to="Task", blank=True, null=True, on_delete=models.SET_NULL
    )
    periodic_task = models.ForeignKey(
        to=PeriodicTask, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "function"], name="s_task_environment_function"
            ),
            models.Index(
                fields=["environment", "creator"], name="s_task_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"],
                name="s_task_environment_created_at",
            ),
            models.Index(
                fields=["environment", "updated_at"],
                name="s_task_environment_updated_at",
            ),
        ]

    def __str__(self):
        return str(self.id)

    def _clean_environment(self):
        """Ensures that the environment is correctly set to that of the function"""
        if self.environment is None:
            self.environment = self.function.package.environment
        elif self.environment != self.function.package.environment:
            raise ValidationError(
                "Function does not belong to the provided environment"
            )

    def _clean_parameters(self):
        """Validate that the parameters conform to the function's schema"""
        if self.parameters is None:
            self.parameters = {}
        validate_parameters(self.parameters, self.function)

    def clean(self):
        """Model instance validation and attribute cleanup"""
        self._clean_environment()
        self._clean_parameters()

    def activate(self) -> None:
        self._enable_periodic_task()
        if self.status in [self.PAUSED, self.PENDING]:
            self._update_status(self.ACTIVE)

    def pause(self) -> None:
        self._disable_periodic_task()
        if self.status == self.ACTIVE:
            self._update_status(self.PAUSED)

    def error(self) -> None:
        self._disable_periodic_task()
        self._update_status(self.ERROR)

    def archive(self) -> None:
        self._disable_periodic_task()
        self._update_status(self.ARCHIVED)

    def update_most_recent_task(self, task) -> None:
        self.most_recent_task = task
        self.save(update_fields=["most_recent_task"])

    def _enable_periodic_task(self) -> None:
        if self.periodic_task is None:
            return
        self.periodic_task.enabled = True
        self.periodic_task.save()

    def _disable_periodic_task(self) -> None:
        if self.periodic_task is None:
            return
        self.periodic_task.enabled = False
        self.periodic_task.save()

    def _update_status(self, status: str) -> None:
        if self.periodic_task is None:
            return
        self.status = status
        self.save(update_fields=["status"])

    def set_schedule(self, crontab_schedule: CrontabSchedule) -> None:
        """Set the schedule of when the ScheduledTask will run. The ScheduledTask and
        its corresponding PeriodicTask are automatically saved.

        Args:
            crontab_schedule: CrontabSchedule object representing the run schedule

        Returns:
            None
        """
        if self.periodic_task is None:
            self.periodic_task = PeriodicTask.objects.create(
                name=self.id,
                description=self.description or self.name,
                crontab=crontab_schedule,
                task="core.utils.tasking.run_scheduled_task",
                args=f'["{self.id}"]',
                enabled=False,
            )
            self.save()
        else:
            self.periodic_task.crontab = crontab_schedule
            self.periodic_task.save()

    def set_status(self, status: str) -> None:
        """Given a new status string, update the given scheduled task's status
        to the new status, and perform that status's operation on the scheduled task.

        Args:
            status: A string that should be equivalent to any of the statuses defined
                in the ScheduledTask model

        Returns:
            None

        Raises:
            ValueError: If the given status is not a valid status, raises a ValueError.
        """
        match status:
            case ScheduledTask.ACTIVE:
                self.activate()
            case ScheduledTask.PAUSED:
                self.pause()
            case ScheduledTask.ARCHIVED:
                self.archive()
            case ScheduledTask.ERROR:
                self.error()
            case _:
                raise ValueError("Unknown status given.")
