import json
import uuid
from typing import Optional

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.template import Context

from core.models import Task
from core.utils.parameter import validate_parameters


class WorkflowRun(models.Model):
    """A WorkflowRun represents an run of a Workflow. When a WorkflowRun
    is created a task will be created for each of its WorkflowSteps, in order of their
    sequence number.

    Attributes:
        id: unique identifier (UUID)
        workflow: the Workflow being executed
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        status: tasking status
        parameters: parameters that can be referenced by the steps in the WorkflowRun
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        to="Workflow", on_delete=models.CASCADE, related_name="runs"
    )
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=16, choices=Task.STATUS_CHOICES, default=Task.PENDING
    )
    parameters = models.JSONField(blank=True, null=True, encoder=DjangoJSONEncoder)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "status"], name="wr_environment_status"
            ),
            models.Index(
                fields=["environment", "creator"], name="wr_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"], name="wr_environment_created_at"
            ),
            models.Index(
                fields=["environment", "updated_at"], name="wr_environment_updated_at"
            ),
        ]

    def get_context(self) -> Context:
        """Generates a context for resolving tasking parameters.

        Returns:
            A Context containing data from all WorkflowRunSteps that have
            occurred for this WorkflowRun
        """
        context = {"parameters": {}}

        parameters = self.parameters or {}
        for key, value in parameters.items():
            context["parameters"][key] = json.dumps(value)

        for step in self.steps.all():
            name = step.workflow_step.name
            task = step.task

            context[name] = {}
            context[name]["result"] = task.result

        return Context(context)

    def _update_status(self, status: str) -> None:
        if self.status != status:
            self.status = status
            self.save()

    def clean(self):
        """Model validation"""
        validate_parameters(self.parameters, self.workflow)

    def complete(self) -> None:
        """Set the WorkflowRun status to COMPLETE"""
        self._update_status(Task.COMPLETE)

    def error(self) -> None:
        """Set the WorkflowRun status to ERROR"""
        self._update_status(Task.ERROR)

    def in_progress(self) -> None:
        """Set the WorkflowRun status to IN_PROGRESS"""
        self._update_status(Task.IN_PROGRESS)

    def execute(self) -> Optional[Task]:
        """Executes the first step in the Workflow

        Returns:
            The Task spawned for the next step in the Workflow. Returns None if there
            are no more remaining steps to be run.
        Raises:
            Exception: The WorkflowRun has already been started
        """
        if self.status != Task.PENDING:
            # TODO: Custom Exception
            raise Exception("WorkflowRun has already been started")

        self.in_progress()

        return self.workflow.first_step.execute(workflow_run=self)
