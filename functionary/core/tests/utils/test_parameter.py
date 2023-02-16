import pytest
from django.core.exceptions import ValidationError

from core.models import Function, FunctionParameter, Package, Team
from core.utils.parameter import PARAMETER_TYPE, validate_parameters


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )


@pytest.fixture
def json_param(function):
    return FunctionParameter.objects.create(
        name="json_param",
        function=function,
        parameter_type=PARAMETER_TYPE.JSON,
        required=True,
    )


@pytest.fixture
def date_param(function):
    return FunctionParameter.objects.create(
        name="date_param",
        function=function,
        parameter_type=PARAMETER_TYPE.DATE,
        required=True,
    )


@pytest.mark.django_db
def test_parameters(function, json_param):
    """JSON parameters get stringified."""
    validate_parameters({json_param.name: {"hello": 1}}, function)


@pytest.mark.django_db
def test_functions_without_parameters(function):
    """Check a parameterless function passes."""
    validate_parameters({}, function)
    validate_parameters({"json_param": {"hello": 1}}, function)


@pytest.mark.django_db
def test_missing_parameter(function, json_param, date_param):
    """Check for missing param2"""
    with pytest.raises(ValidationError, match=r".*date_param.*"):
        validate_parameters({json_param.name: {"hello": 1}}, function)


@pytest.mark.django_db
def test_incorrect_parameters(function, json_param):
    """Check that incorrect parameters don't work."""
    with pytest.raises(ValidationError, match=r".*json_param.*required.*"):
        validate_parameters({}, function)

    with pytest.raises(ValidationError, match=r".*json_param.*required.*"):
        validate_parameters({"true": False}, function)


@pytest.mark.django_db
def test_incorrect_parameter_type(function, json_param, date_param):
    """Check that parameters with an incorrect type don't work."""
    with pytest.raises(ValidationError, match=r".*date_param.*"):
        validate_parameters({json_param.name: 1, date_param.name: False}, function)

    with pytest.raises(ValidationError, match=r".*date_param.*"):
        validate_parameters({json_param.name: 1, date_param.name: "False"}, function)
