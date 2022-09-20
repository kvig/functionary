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

_field_mapping = {
    "integer": (IntegerField, None),
    "string": (CharField, None),
    "text": (CharField, Textarea),
    "number": (FloatField, None),
    "boolean": (BooleanField, None),
    "date": (DateField, None),
    "date-time": (
        DateTimeField,
        None,
    ),
    "json": (JSONField, Textarea),
}

_transform_intitial_mapping = {"json": json.loads}


def get_param_type(param_dict):
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


class TaskParameterForm(Form):
    template_name = "forms/task_parameters.html"

    def __init__(self, function, data=None):
        super().__init__(data)

        for param, value in function.schema["properties"].items():
            req = not value["default"]
            initial = value.get("default", None)
            param_type = get_param_type(value)
            kwargs = {
                "label": value["title"],
                "label_suffix": param_type,
                "initial": initial,
                "required": req,
                "help_text": value.get("description", None),
            }

            field_class, widget = _field_mapping.get(param_type, (None, None))

            if not field_class:
                raise ValueError(f"Unknown field type for {param}: {param_type}")

            if widget:
                kwargs["widget"] = widget
            if param_type in _transform_intitial_mapping:
                kwargs["initial"] = _transform_intitial_mapping[param_type](initial)

            field = field_class(**kwargs)
            if param_type != "boolean":
                field.widget.attrs.update({"class": "input"})
            self.fields[param] = field
