""" Task model """
import uuid
from json import JSONDecodeError
from typing import TYPE_CHECKING, Optional, Union

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.utils.parameter import validate_parameters

if TYPE_CHECKING:
    from core.models import Function, Workflow


class Task(models.Model):
    """A Task is an individual execution of a function or workflow

    This model should always be queried with environment as one of the filter
    parameters. The indices are intentionally setup this way as all requests for task
    data happen in the context of a specific environment.

    Attributes:
        id: unique identifier (UUID)
        tasked_type: the ContentType (model) of the object being tasked
        tasked_id: the UUID of the object being tasked
        tasked_object: foreign key to the object being tasked, built from tasked_type
                        and tasked_id.
        environment: the environment that this task belongs to. All queryset filtering
                     should include an environment.
        parameters: JSON representing the parameters that will be passed to the function
                    or workflow
        status: tasking status
        creator: the user that initiated the task
        created_at: task creation timestamp
        updated_at: task updated timestamp
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETE, "Complete"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tasked_type = models.ForeignKey(to=ContentType, on_delete=models.PROTECT)
    tasked_id = models.UUIDField()
    tasked_object = GenericForeignKey("tasked_type", "tasked_id")
    environment = models.ForeignKey(to="Environment", on_delete=models.CASCADE)
    parameters = models.JSONField(encoder=DjangoJSONEncoder)
    return_type = models.CharField(max_length=64, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    scheduled_task = models.ForeignKey(
        to="ScheduledTask", null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["environment", "tasked_type", "tasked_id"],
                name="task_contenttype",
            ),
            models.Index(
                fields=["environment", "status"], name="task_environment_status"
            ),
            models.Index(
                fields=["environment", "creator"], name="task_environment_creator"
            ),
            models.Index(
                fields=["environment", "created_at"], name="task_environment_created_at"
            ),
            models.Index(
                fields=["environment", "updated_at"], name="task_environment_updated_at"
            ),
        ]

    def __str__(self):
        return str(self.id)

    def _clean_environment(self):
        """Ensures that the environment is correctly set to that of the function or
        workflow
        """
        if self.environment is None:
            self.environment = self.tasked_object.environment
        elif self.environment != self.tasked_object.environment:
            raise ValidationError(
                "Function or Workflow being tasked does not belong to the provided "
                "environment"
            )

    def _clean_parameters(self):
        """Validate that the parameters conform to the schema of the function or
        workflow
        """
        validate_parameters(self.parameters, self.tasked_object)

    def _clean_tasked_object(self):
        """Validate tasked_object is active for newly created tasks"""
        if self._state.adding and not self.tasked_object.is_active:
            raise ValidationError("This function or workflow is not active")

    def clean(self):
        """Model instance validation and attribute cleanup"""
        self._clean_environment()
        self._clean_parameters()
        self._clean_tasked_object()

    # TODO: Sort out what to do with this since it does not apply to workflows.
    @property
    def raw_result(self) -> Optional[str]:
        """Convenience property for accessing the result output"""
        try:
            return self.taskresult.result
        except ObjectDoesNotExist:
            return None

    # TODO: Sort out what to do with this since it does not apply to workflows.
    @property
    def result(self) -> Optional[Union[bool, dict, float, int, list, str]]:
        """Convenience property for accessing the result output loaded as JSON"""
        try:
            return self.taskresult.json
        except ObjectDoesNotExist:
            return None
        except JSONDecodeError:
            return self.taskresult.result

    # TODO: Sort out what to do with this since it does not apply to workflows.
    @property
    def log(self) -> Optional[str]:
        """Convenience property for accessing the log output"""
        try:
            return self.tasklog.log
        except ObjectDoesNotExist:
            return None

    @property
    def variables(self):
        """Returns the variables required by the function or workflow being tasked."""
        return self.environment.variables.filter(name__in=self.tasked_object.variables)

    @property
    def function(self) -> "Function":
        """Alias for tasked_object, mostly for type hinting purposes

        Raises:
            ObjectDoesNotExist: The tasked_object for this task is not a Function
        """
        Function = apps.get_model("core", "Function")

        if type(self.tasked_object) == Function:
            return self.tasked_object
        else:
            raise ObjectDoesNotExist("task_object is not a Function")

    @property
    def workflow(self) -> "Workflow":
        """Alias for tasked_object, mostly for type hinting purposes

        Raises:
            ObjectDoesNotExist: The tasked_object for this task is not a Workflow
        """
        Workflow = apps.get_model("core", "Workflow")

        if type(self.tasked_object) == Workflow:
            return self.tasked_object
        else:
            raise ObjectDoesNotExist("task_object is not a Workflow")
