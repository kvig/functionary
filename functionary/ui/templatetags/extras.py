import json

from django import template

register = template.Library()


@register.filter
def pretty_json(value):
    return json.dumps(value, indent=4)


@register.filter
def input_type(value):
    if value in ["integer", "float"]:
        return "number"
    return "text"
