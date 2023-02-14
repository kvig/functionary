import json
import re
from typing import TYPE_CHECKING, Optional, Tuple, Type, Union

from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    Field,
    FileInput,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    Textarea,
    TextInput,
)
from django.forms.widgets import DateInput, DateTimeInput, Widget

from core.utils.parameter import PARAMETER_TYPE

if TYPE_CHECKING:
    from django.http import QueryDict

    from core.models import Function


class HTMLDateInput(DateInput):
    input_type = "date"


class HTMLDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


_field_mapping = {
    PARAMETER_TYPE.INTEGER: (IntegerField, None),
    PARAMETER_TYPE.STRING: (CharField, None),
    PARAMETER_TYPE.TEXT: (CharField, Textarea),
    PARAMETER_TYPE.FLOAT: (FloatField, None),
    PARAMETER_TYPE.FILE: (CharField, FileInput),
    PARAMETER_TYPE.BOOLEAN: (BooleanField, None),
    PARAMETER_TYPE.DATE: (DateField, HTMLDateInput),
    PARAMETER_TYPE.DATETIME: (
        DateTimeField,
        HTMLDateTimeInput,
    ),
    PARAMETER_TYPE.JSON: (JSONField, Textarea),
}


def _transform_json(value: Union[str, dict]) -> Union[str, dict]:
    if type(value) is str:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    return value


_transform_initial_mapping = {PARAMETER_TYPE.JSON: _transform_json}


def _prepare_initial_value(param_type: str, initial: dict) -> Union[dict, None]:
    """Convert the initial value to the appropriate type.
    This function will massage the initial value as needed into the type
    required for the parameter field. Currently, JSON types need to be
    converted from a string into an object, otherwise display issues
    occur in the form.
    """
    if initial:
        if param_type in _transform_initial_mapping:
            return _transform_initial_mapping[param_type](initial)
        else:
            return initial
    return None


class TaskParameterForm(Form):
    """Form for providing task parameter input.

    Dynamically generates a form based on the provided Function. The schema for the
    Function is parsed and the appropriate fields are setup, including default values
    and correct input types to be used for validation.

    Attributes:
        function: Function instance for which to generate the form
        data: dict of data submitted to the form
        initial: dict of initial values that the form fields should be populated with
        prefix: Prefix to apply to the form field ids. Set this if the default value
                happens to cause conflicts with other fields when using multiple forms.
    """

    template_name = "forms/task_parameters.html"

    def __init__(
        self,
        function: "Function",
        data: dict | None = None,
        initial: dict | None = None,
        prefix: str = "task-parameter",
        **kwargs,
    ):
        super().__init__(data=data, prefix=prefix, **kwargs)

        if initial is None:
            initial = {}

        for parameter in function.parameters.all():
            param_name = parameter.name
            param_type = parameter.parameter_type
            initial_value = initial.get(param_name, None) or parameter.default
            input_value = data.get(f"{self.prefix}-{param_name}") if data else None

            field_class, widget = self.get_field_info(param_type, input_value)

            if not field_class:
                raise ValueError(f"Unknown field type for {param_name}: {param_type}")

            kwargs = {
                "label": param_name,
                "label_suffix": param_type,
                "initial": _prepare_initial_value(param_type, initial_value),
                "required": parameter.required,
                "help_text": parameter.description,
            }

            if widget:
                kwargs["widget"] = widget

            field = field_class(**kwargs)

            # Style all inputfields except the checkbox with the "input" class
            if param_type != PARAMETER_TYPE.BOOLEAN:
                field.widget.attrs.update({"class": "input"})

            self.fields[param_name] = field

    def get_field_info(
        self, parameter_type: str, input_value: str | None
    ) -> Tuple[Type[Field], Type[Widget]]:
        """Gets the appropriate field class and widget for the provided parameter type.
        The input_value is not used in this implementation, but is expected to be
        provided so that alternative implementations of this method can use it to derive
        the field class and widget based on the input data.
        """
        return _field_mapping.get(parameter_type, (None, None))


class TaskParameterTemplateForm(TaskParameterForm):
    """TaskParameterForm variant with template variable support

    This is a version of TaskParameterForm that allows template variables to be entered
    as values regardless of parameter type. That is, a field requiring an integer will
    allow either and integer value or a template variable such as {{step.result}}.
    Other than the exception for template variables, other validation rules still apply.
    """

    def _stringify_template_variables(self, parameter_template: str) -> str:
        """Converts the template variables in the parameter template to strings so
        that the template can be safely jsonified.
        """
        return re.sub(r"{{([\w\.]+)}}", r'"{{\1}}"', parameter_template)

    def _build_parameter_template(self, parameters: dict) -> str:
        """Undo the template variable stringification that was required to jsonify
        the template. The resulting string is one that can be rendered as a django
        template"""
        json_data = json.dumps(parameters)

        return re.sub(r'"{{([\w\.]*)}}"', r"{{\1}}", json_data)

    def __init__(
        self,
        function: "Function",
        data: Optional["QueryDict"] = None,
        initial: Optional[str] = None,
        **kwargs,
    ):
        """TaskParameterTemplateForm init

        Args:
            function: The Function that will be executed when the WorkflowStep runs
            data: Form submission data
            initial: Initial values to populate the form fields with on render
        """
        initial_data = (
            json.loads(self._stringify_template_variables(initial)) if initial else {}
        )

        super().__init__(function=function, data=data, initial=initial_data, **kwargs)

    def get_field_info(
        self, parameter_type: str, input_value: str | None
    ) -> Tuple[Type[Field], Type[Widget]]:
        """For fields that are allowed to provide template variables as input, alters
        the widget to be a TextInput. When input_value is provided, if the input is a
        template variable the field class is set to CharField, as validation against the
        original field class is no longer possible.
        """
        field_class, widget = super().get_field_info(parameter_type, input_value)

        if parameter_type in [
            PARAMETER_TYPE.INTEGER,
            PARAMETER_TYPE.FLOAT,
            PARAMETER_TYPE.JSON,
        ]:
            widget = TextInput

            if input_value and re.match(r"{{[\w\.]+}}", input_value):
                field_class = CharField

        return field_class, widget

    @property
    def parameter_template(self):
        """Returns the json-string parameter template for parameters form. This can
        only be access after validation via is_valid().
        """
        assert hasattr(self, "cleaned_data"), (
            "You cannot access parameter_template until cleaned_data is made available"
            "by calling is_valid()."
        )

        return self._build_parameter_template(self.cleaned_data)
