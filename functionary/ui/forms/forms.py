import json

from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    Textarea,
)
from django.forms.widgets import DateInput, DateTimeInput


class HTMLDateInput(DateInput):
    input_type = "date"


class HTMLDateTimeInput(DateTimeInput):
    input_type = "datetime-local"


_field_mapping = {
    "integer": (IntegerField, None),
    "string": (CharField, None),
    "text": (CharField, Textarea),
    "number": (FloatField, None),
    "boolean": (BooleanField, None),
    "date": (DateField, HTMLDateInput),
    "date-time": (
        DateTimeField,
        HTMLDateTimeInput,
    ),
    "json": (JSONField, Textarea),
}

_transform_initial_mapping = {"json": json.loads}


def _get_param_type(param_dict):
    """Finds the type of the parameter from the definition in the schema.

    Pydantic maps to python types correctly, but we want to use the actual
    schema type for input purposes. If there is a format in the param_dict,
    the input field has a definition of what type it is. If there is an anyOf,
    inspect it and try find out what type it should be. Otherwise, return the
    value of 'type' in param_dict.
    """
    keys = param_dict.keys()

    # pydantic hides the date type in the format field
    if "format" in keys:
        return param_dict["format"]
    # json and text get mapped to TypeVars to preserve the distinction vs string
    elif "anyOf" in keys:
        return (
            "json"
            if any(
                param_types.get("format", None) == "json-string"
                for param_types in param_dict["anyOf"]
            )
            else "text"
        )
    else:
        return param_dict["type"]


def _prepare_initial_value(param_type, initial):
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
    template_name = "forms/task_parameters.html"

    def __init__(self, function, data=None):
        super().__init__(data)

        for param, value in function.schema["properties"].items():
            initial = value.get("default", None)
            req = initial is None
            param_type = _get_param_type(value)
            field_class, widget = _field_mapping.get(param_type, (None, None))

            if not field_class:
                raise ValueError(f"Unknown field type for {param}: {param_type}")

            kwargs = {
                "label": value["title"],
                "label_suffix": param_type,
                "initial": _prepare_initial_value(param_type, initial),
                "required": req,
                "help_text": value.get("description", None),
            }

            if widget:
                kwargs["widget"] = widget

            field = field_class(**kwargs)

            # Style all inputfields except the checkbox with the "input" class
            if param_type != "boolean":
                field.widget.attrs.update({"class": "input"})
            self.fields[param] = field
