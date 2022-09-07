from django.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    Field,
    FloatField,
    Form,
    IntegerField,
    JSONField,
    TimeField,
)

field_mapping: dict[str, Field] = {
    "integer": IntegerField,
    "string": CharField,
    "float": FloatField,
    "double": DecimalField,
    "boolean": BooleanField,
    "date": DateField,  # TODO set input_formats= on constructor if needed
    "datetime": DateTimeField,  # TODO set input_formats= on constructor if needed
    "time": TimeField,  # TODO set input_formats= on constructor if needed
    "object": JSONField,
}


class FunctionForm(Form):
    template_name = "forms/function_detail.html"

    def __init__(self, function, data=None):
        super().__init__(data)

        for param, value in function.schema["properties"].items():
            req: bool = not value["default"]
            initial = value.get("default", None)
            kwargs = {
                "label": value["title"],
                "label_suffix": value["type"],
                "initial": initial,
                "required": req,
                "help_text": value.get("description", None),
            }
            field_class: Field = field_mapping.get(value["type"], None)

            if not field_class:
                raise ValueError(f"Unknown field type for {param}: {value['type']}")

            field = field_class(**kwargs)
            field.widget.attrs.update({"class": "input"})
            # setattr(field, 'field_type', value['type'])
            self.fields[param] = field
