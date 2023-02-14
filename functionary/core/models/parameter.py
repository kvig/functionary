import uuid

from django.core.validators import RegexValidator
from django.db import models

from core.utils.parameter import PARAMETER_TYPE_CHOICES

VALID_PARAMETER_NAME = RegexValidator(
    regex=r"^\w+$",
    message=(
        "Invalid parameter name. Only numbers, letters, and underscore are allowed."
    ),
)


class Parameter(models.Model):
    """Base model for common components of FunctionParameter and WorkflowParameter"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, validators=[VALID_PARAMETER_NAME])
    description = models.TextField(blank=True, null=True)
    parameter_type = models.CharField(max_length=64, choices=PARAMETER_TYPE_CHOICES)
    default = models.CharField(max_length=128, blank=True, null=True)
    required = models.BooleanField(default=False)

    class Meta:
        abstract = True


class FunctionParameter(Parameter):
    """Input parameters for Functions

    Attributes:
        function: foreign key to the Function the parameter belongs to
        name: parameter name
        description: parameter description
        parameter_type: data type
        default: default value to display for the parameter
        required: whether or note the parameter is required
    """

    function = models.ForeignKey(to="Function", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["function", "name"], name="fp_function_name_unique"
            )
        ]


class WorkflowParameter(Parameter):
    """Input parameters for Workflows

    Attributes:
        workflow: foreign key to the Workflow the parameter belongs to
        name: parameter name
        description: parameter description
        parameter_type: data type
        default: default value to display for the parameter
        required: whether or note the parameter is required
    """

    workflow = models.ForeignKey(to="Workflow", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "name"], name="wp_workflow_name_unique"
            )
        ]
