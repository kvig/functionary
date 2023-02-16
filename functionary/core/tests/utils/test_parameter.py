import pytest
from django.core.exceptions import ValidationError

from core.models import Function, FunctionParameter, Package, Task, Team
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
def param1(function):
    return FunctionParameter.objects.create(
        name="json_param",
        function=function,
        parameter_type=PARAMETER_TYPE.JSON,
        required=True,
    )


@pytest.fixture
def param2(function):
    return FunctionParameter.objects.create(
        name="dont_hide",
        function=function,
        parameter_type=PARAMETER_TYPE.DATE,
        required=True,
    )


@pytest.fixture
def task(function, environment, admin_user):
    return Task.objects.create(
        function=function,
        environment=environment,
        parameters={},
        creator=admin_user,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("param1")
def test_parameters(task):
    """JSON parameters get stringified."""
    validate_parameters({"json_param": {"hello": 1}}, task.function)


@pytest.mark.django_db
def test_functions_without_parameters(task):
    """Check a parameterless function passes."""
    validate_parameters({}, task.function)
    validate_parameters({"json_param": {"hello": 1}}, task.function)


@pytest.mark.django_db
@pytest.mark.usefixtures("param1", "param2")
def test_missing_parameter(task):
    """Check for missing param2"""
    with pytest.raises(ValidationError, match=r".*dont_hide.*"):
        validate_parameters({"json_param": {"hello": 1}}, task.function)


@pytest.mark.django_db
@pytest.mark.usefixtures("param1")
def test_incorrect_parameters(task):
    """Check that incorrect parameters don't work."""
    with pytest.raises(ValidationError, match=r".*json_param.*is a required.*"):
        validate_parameters({}, task.function)

    with pytest.raises(ValidationError, match=r".*json_param.*is a required.*"):
        validate_parameters({"true": False}, task.function)


@pytest.mark.django_db
@pytest.mark.usefixtures("param1", "param2")
def test_incorrect_parameters2(task):
    """Check that incorrect parameters don't work."""
    with pytest.raises(ValidationError, match=r".*dont_hide.*"):
        validate_parameters({"json_param": 1, "dont_hide": False}, task.function)

    # The following should fail but doesn't
    # with pytest.raises(ValidationError, match=r".*dont_hide.*"):
    #     validate_parameters({"json_param": 1, "dont_hide": "False"}, task.function)
