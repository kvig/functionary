import json
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.template import Context, Template

from core.models import Task, WorkflowRunStep
from core.utils.tasking import mark_error, start_task

VALID_STEP_NAME = RegexValidator(
    regex=r"^\w+$",
    message="Invalid step name. Only numbers, letters, and underscore are allowed.",
)


class WorkflowStep(models.Model):
    """A WorkflowStep is the definition of a Task that will be executed as part of a
    Workflow

    Attributes:
        id: unique identifier (UUID)
        workflow: the Workflow to which this step belongs
        next: The step that follows this one in the workflow. A value of None indicates
              that this is the final step.
        name: An internal name for the step which can be used as a reference for
              input into other steps of the Workflow.
        function: the function that the task will be an run of
        parameter_template: Stringified JSON representing the parameters that will be
                            passed to the function. May contain django template syntax
                            in place of values (e.g. {{step_name.result}})
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(to="Workflow", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, validators=[VALID_STEP_NAME])
    next = models.ForeignKey(
        to="WorkflowStep", blank=True, null=True, on_delete=models.PROTECT
    )
    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)
    parameter_template = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "name"],
                name="ws_workflow_name_unique_together",
            ),
        ]

    def _get_parameters(self, context: Context):
        """Uses a given Context to resolve the parameter_template into a parameters
        dict
        """
        resolved_parameters = Template(self.parameter_template or "{}").render(context)

        return json.loads(resolved_parameters)

    def _escape(self, value):
        """Escapes characters to prepare for use in json"""
        return value.replace('"', '\\"') if isinstance(value, str) else value

    def _get_json_safe_value(self, value):
        """Converts a value into something json safe for use in the context"""
        return json.dumps(value) if isinstance(value, dict) else self._escape(value)

    def _get_run_context(self, workflow_run: "Task") -> Context:
        """Generates a context for resolving tasking parameters.

        Args:
            workflow_run: a Task associated with a specific run of a workflow

        Returns:
            A Context containing data from all WorkflowRunSteps that have
            occurred for this workflow run
        """
        context = {"parameters": {}}

        parameters = workflow_run.parameters or {}

        for key, value in parameters.items():
            context["parameters"][key] = self._get_json_safe_value(value)

        for step in workflow_run.steps.all():
            name = step.workflow_step.name
            task = step.step_task

            context[name] = {}
            context[name]["result"] = self._get_json_safe_value(task.result)

        return Context(context, autoescape=False)

    def clean(self):
        if self.workflow.environment != self.function.package.environment:
            raise ValidationError("Function and workflow environments do not match")

    @property
    def previous(self):
        """Returns the step preceding this one in the workflow. For the first step in
        the workflow, returns None."""
        return self.workflowstep_set.filter(next=self).first()

    def execute(self, workflow_task: "Task") -> "Task":
        """Execute this workflow step as part of the supplied workflow task"""

        with transaction.atomic():
            run_context = self._get_run_context(workflow_task)

            task = Task.objects.create(
                creator=workflow_task.creator,
                environment=self.workflow.environment,
                tasked_object=self.function,
                parameters=self._get_parameters(run_context),
            )

            WorkflowRunStep.objects.create(
                workflow_step=self, step_task=task, workflow_task=workflow_task
            )

        start_task(task)
        if task.status == Task.ERROR:
            mark_error(workflow_task, f"Unable to start workflow step {self.name}")

        return task
