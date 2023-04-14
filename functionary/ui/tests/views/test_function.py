"""Tests function views"""

from io import BytesIO

import pytest
from django.test.client import Client
from django.urls import reverse

from core.models import Function, FunctionParameter, Package, Task, Team
from core.models.package import PACKAGE_STATUS
from core.utils.minio import S3FileUploadError
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )


@pytest.fixture
def file_function(package):
    return Function.objects.create(
        name="testfunction_file",
        package=package,
        environment=package.environment,
    )


@pytest.fixture
def file_parameter(file_function: Function):
    return file_function.parameters.create(
        name="required_file", parameter_type=PARAMETER_TYPE.FILE, required=True
    )


@pytest.fixture
def integer_parameter(function: Function):
    return function.parameters.create(
        name="optional_integer", parameter_type=PARAMETER_TYPE.INTEGER, required=False
    )


@pytest.fixture
def string_parameter(function):
    return function.parameters.create(
        name="optional_string", parameter_type=PARAMETER_TYPE.STRING, required=False
    )


@pytest.fixture
def text_parameter(function):
    return function.parameters.create(
        name="optional_text", parameter_type=PARAMETER_TYPE.TEXT, required=False
    )


@pytest.mark.django_db
def test_execute_handles_optional_parameters(
    admin_client, function, integer_parameter, string_parameter, text_parameter
):
    """Optional parameters that are empty when the form is submitted should be excluded
    from the Task parameters"""
    session = admin_client.session
    session["environment_id"] = str(function.environment.id)
    session.save()

    url = reverse("ui:function-execute")
    data = {
        "function_id": str(function.id),
        f"task-parameter-{integer_parameter.name}": "",
        f"task-parameter-{string_parameter.name}": "",
        f"task-parameter-{text_parameter.name}": "should be included",
    }

    admin_client.post(url, data)
    task = Task.objects.get(tasked_id=function.id)

    # Parameters that were not set should not be present
    assert integer_parameter.name not in task.parameters
    assert string_parameter.name not in task.parameters

    # The parameter that was set should be present
    assert text_parameter.name in task.parameters


def test_fail_file_upload(
    mocker,
    admin_client: Client,
    file_function: Function,
    file_parameter: FunctionParameter,
):
    def mock_file_upload(_task, _request):
        """Mock the method of uploading a file to S3"""
        raise S3FileUploadError("Failed to upload file")

    mocker.patch("ui.views.function.handle_file_parameters", mock_file_upload)

    session = admin_client.session
    session["environment_id"] = str(file_function.environment.id)
    session.save()

    url = reverse("ui:function-execute")

    example_file = BytesIO(b"Hello World!")
    data = {
        "function_id": str(file_function.id),
        f"task-parameter-{file_parameter.name}": example_file,
    }

    response = admin_client.post(url, data)
    assert response.status_code == 503
    assert not Task.objects.filter(tasked_id=file_function.id).exists()
