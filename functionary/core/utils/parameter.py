import datetime
import json
from copy import deepcopy
from typing import TYPE_CHECKING, Type, TypeVar, Union

import jsonschema
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import BaseModel, Field, FileUrl, Json, ValidationError, create_model

if TYPE_CHECKING:
    from core.models import Function, Workflow


class PARAMETER_TYPE:
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    FILE = "file"
    FLOAT = "float"
    INTEGER = "integer"
    JSON = "json"
    STRING = "string"
    TEXT = "text"


_PARAMETER_TYPE_MAP = {
    PARAMETER_TYPE.BOOLEAN: bool,
    PARAMETER_TYPE.DATE: datetime.date,
    PARAMETER_TYPE.DATETIME: datetime.datetime,
    PARAMETER_TYPE.FILE: TypeVar("file", FileUrl, bytes),
    PARAMETER_TYPE.FLOAT: float,
    PARAMETER_TYPE.INTEGER: int,
    PARAMETER_TYPE.JSON: TypeVar("json", Json, str),
    PARAMETER_TYPE.STRING: str,
    PARAMETER_TYPE.TEXT: TypeVar("text", str, bytes),
}

PARAMETER_TYPE_CHOICES = [(_type, _type) for _type in _PARAMETER_TYPE_MAP.keys()]


def _get_pydantic_model(instance: Union["Function", "Workflow"]) -> Type[BaseModel]:
    """Get a pydantic model describing the parameters of the provided instance"""
    params_dict = {}

    for parameter in instance.parameters.all():
        field = Field()
        field.alias = parameter.name
        field.title = parameter.name
        field.description = parameter.description

        field.default = ... if parameter.required else parameter.default
        type_ = _PARAMETER_TYPE_MAP[parameter.parameter_type]

        params_dict[field.alias] = (type_, field)

    model_name = f"{type(instance).__name__}ParameterModel"

    return create_model(model_name, **params_dict)


def _serialize_json_parameters(
    parameters: dict, instance: Union["Function", "Workflow"]
) -> dict:
    """Serializes json type parameters for use in validation"""
    parameters_copy = deepcopy(parameters)

    for parameter_obj in instance.parameters.filter(
        name__in=parameters.keys(), parameter_type=PARAMETER_TYPE.JSON
    ):
        name = parameter_obj.name
        parameters_copy[name] = json.dumps(parameters_copy[name])

    return parameters_copy


def get_schema(instance: Union["Function", "Workflow"]) -> dict:
    """Creates a pydantic model from the parameter definitions and returns the schema
    as a JSON string

    Args:
        instance: A Function or Workflow instance to generate a schema for

    Returns:
        An OpenAPI / JSON Schema compatible schema dictionary
    """
    return _get_pydantic_model(instance).schema()


def validate_parameters(parameters: dict, instance: Union["Function", "Workflow"]):
    """Validate the provided input parameters against the instance's parameter
    definitions

    Args:
        parameters: dict containing the parameters as key / value pairs
        instance: Function or Workflow instance to validate the parameters against

    Raises:
        ValidationError: The parameters are invalid for the provided instance
    """
    try:
        pydantic_model = _get_pydantic_model(instance)
        serialized_parameters = _serialize_json_parameters(parameters, instance)
        jsonschema.validate(
            serialized_parameters, pydantic_model(**serialized_parameters).schema()
        )
    except (
        ValidationError,
        jsonschema.exceptions.ValidationError,
        json.JSONDecodeError,
    ) as exc:
        raise DjangoValidationError(exc)
