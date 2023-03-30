from typing import TYPE_CHECKING, Union

from django import forms
from django.urls import reverse

from core.models import Function, WorkflowStep
from core.models.workflow_step import VALID_STEP_NAME

if TYPE_CHECKING:
    from uuid import UUID

    from core.models import Environment


class WorkflowStepCreateForm(forms.ModelForm):
    """Form for WorkflowStep creation"""

    template_name = "forms/workflow/step_edit.html"

    class Meta:
        model = WorkflowStep
        fields = ["workflow", "name", "function", "next"]
        widgets = {"workflow": forms.HiddenInput(), "next": forms.HiddenInput()}

    def __init__(
        self,
        environment: Union["Environment", "UUID", str, None] = None,
        *args,
        **kwargs
    ):
        """WorkflowStepForm init

        Args:
            environment: Environment instance or id. When provided, the queryset of the
                function field will be filtered to only the functions for the
                environment.
        """
        super().__init__(*args, **kwargs)

        # Add htmx attributes to the function widget
        self.fields["function"].widget.attrs.update(
            {
                "class": "form-control",
                "hx-get": reverse("ui:function-parameters"),
                "hx-vals": '{"allow_template_variables": "true"}',
                "hx-target": "#function-parameters",
                "hx-swap": "innerHTML",
            }
        )
        self.fields["name"].widget.attrs.update(
            {
                "pattern": VALID_STEP_NAME.regex.pattern,
                "title": VALID_STEP_NAME.message,
            }
        )

        # Narrow the available function list down to just those
        # active in the environment
        if environment:
            function_field = self.fields["function"]
            function_field.queryset = Function.active_objects.filter(
                environment=environment
            )


class WorkflowStepUpdateForm(WorkflowStepCreateForm):
    """Form for WorkflowStep updates"""

    class Meta:
        model = WorkflowStep
        fields = ["name", "function"]
