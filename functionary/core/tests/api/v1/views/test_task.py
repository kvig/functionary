import json
from io import BytesIO

import pytest
from django.test.client import MULTIPART_CONTENT, Client
from django.urls import reverse
from rest_framework import status

from core.models import (
    Environment,
    Function,
    Package,
    Task,
    TaskResult,
    Team,
    Workflow,
    WorkflowParameter,
    WorkflowStep,
)
from core.models.package import PACKAGE_STATUS
from core.utils.minio import S3FileUploadError
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment() -> Environment:
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment: Environment) -> Package:
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def int_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_int",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def json_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_json",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(
        name="prop1", parameter_type=PARAMETER_TYPE.JSON, required=True
    )

    return _function


@pytest.fixture
def file_function(package: Package) -> Function:
    _function = Function.objects.create(
        name="testfunction_file",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(
        name="prop1", parameter_type=PARAMETER_TYPE.FILE, required=True
    )

    return _function


@pytest.fixture
def task(int_function, admin_user) -> Task:
    return Task.objects.create(
        tasked_object=int_function,
        environment=int_function.package.environment,
        parameters={"prop1": 1},
        creator=admin_user,
    )


@pytest.fixture
def request_headers(environment: Environment) -> dict:
    return {"HTTP_X_ENVIRONMENT_ID": str(environment.id)}


@pytest.fixture
def workflow(int_function: Function, admin_user) -> Workflow:
    _workflow = Workflow.objects.create(
        environment=int_function.environment, name="workflow", creator=admin_user
    )

    WorkflowParameter.objects.create(
        workflow=_workflow, name="param1", parameter_type=PARAMETER_TYPE.INTEGER
    )

    WorkflowStep.objects.create(
        workflow=_workflow,
        name="step1",
        next=None,
        function=int_function,
        parameter_template='{"param1": "{{parameters.param1}}"}',
    )

    return _workflow


def test_create_int_task(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Create a Task with integer parameters by Function ID"""
    url = reverse("task-list")

    task_input = {
        "function": str(int_function.id),
        "param.prop1": 5,
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_task_by_name(
    admin_client: Client,
    int_function: Function,
    package: Package,
    request_headers: dict,
):
    """Create a Task by Function name"""
    url = reverse("task-list")

    task_input = {
        "function_name": int_function.name,
        "package_name": package.name,
        "param.prop1": 5,
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_json_task(
    admin_client: Client,
    json_function: Function,
    request_headers: dict,
):
    """Create a Task with JSON parameters"""
    url = reverse("task-list")

    task_input = {
        "function": str(json_function.id),
        "param.prop1": json.dumps({"hello": "world"}),
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_file_task(
    mocker,
    admin_client: Client,
    file_function: Function,
    request_headers: dict,
):
    """Create a Task with file parameters"""

    def mock_file_upload(_task, _request):
        """Mock the method of uploading a file to S3"""
        return

    url = reverse("task-list")

    mocker.patch("core.api.v1.views.task.handle_file_parameters", mock_file_upload)

    example_file = BytesIO(b"Hello World!")
    task_input = {"function": str(file_function.id), "param.prop1": example_file}
    response = admin_client.post(
        url,
        data=task_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    task_id = response.data.get("id")

    assert response.status_code == 201
    assert task_id is not None
    assert Task.objects.filter(id=task_id).exists()


def test_create_returns_503_for_file_upload_error(
    mocker,
    admin_client: Client,
    file_function: Function,
    request_headers: dict,
):
    """A file upload error should return a 503 status"""
    url = reverse("task-list")

    def mock_file_upload(_task, _request):
        """Mock the method of uploading a file to S3"""
        raise S3FileUploadError("Failed to upload file")

    mocker.patch("core.api.v1.views.task.handle_file_parameters", mock_file_upload)

    example_file = BytesIO(b"Hello World!")
    task_input = {"function": str(file_function.id), "param.prop1": example_file}

    response = admin_client.post(
        url,
        data=task_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert not Task.objects.filter(tasked_id=file_function.id).exists()


def test_create_returns_415_for_invalid_content_type(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Test for valid content types"""
    url = reverse("task-list")

    task_input = {
        "function": str(int_function.id),
        "param.prop1": 5,
    }

    response = admin_client.post(
        url, data=task_input, content_type="application/json", **request_headers
    )
    assert response.status_code == 415


def test_create_returns_400_for_extra_parameters(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Return a 400 if additional, unexpected parameters are provided"""
    url = reverse("task-list")

    input_with_extra_parameters = {
        "function": str(int_function.id),
        "param.prop1": 5,
        "unexpected_param": 12,
    }

    response = admin_client.post(
        url,
        data=input_with_extra_parameters,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    assert response.status_code == 400
    assert "unexpected_param" in response.json()[0]
    assert not Task.objects.filter(tasked_id=int_function.id).exists()


def test_create_returns_400_for_invalid_int_parameters(
    admin_client: Client,
    int_function: Function,
    request_headers: dict,
):
    """Return a 400 for invalid int parameters"""
    url = reverse("task-list")

    invalid_int_function_input = {
        "function": str(int_function.id),
        "param.prop1": "not an integer",
    }

    response = admin_client.post(
        url,
        data=invalid_int_function_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    assert response.status_code == 400
    assert "param.prop1" in response.json()
    assert not Task.objects.filter(tasked_id=int_function.id).exists()


def test_create_returns_400_for_invalid_json_parameters(
    admin_client: Client,
    json_function: Function,
    request_headers: dict,
):
    """Return a 400 for invalid json parameters"""
    url = reverse("task-list")

    invalid_json_input = {
        "function": str(json_function.id),
        "param.prop1": '{"hello": "world"',
    }

    response = admin_client.post(
        url,
        data=invalid_json_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )
    assert response.status_code == 400
    assert "param.prop1" in response.json()
    assert not Task.objects.filter(tasked_id=json_function.id).exists()


def test_create_returns_400_for_invalid_function_name(
    admin_client: Client,
    package: Package,
    request_headers: dict,
):
    """Return a 400 for invalid function name"""
    url = reverse("task-list")

    task_input = {
        "function_name": "invalid_function_name",
        "package_name": package.name,
        "param.someparam": '{"some": "input"}',
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )

    assert response.status_code == 400
    assert "Invalid function" in response.json()[0]


def test_create_returns_400_for_invalid_function_id(
    admin_client: Client,
    request_headers: dict,
):
    """Return a 400 for invalid function id"""
    url = reverse("task-list")

    task_input = {
        "function": "not a uuid",
        "param.someparam": '{"some": "input"}',
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )
    assert response.status_code == 400
    assert "Invalid function" in response.json()[0]


def test_create_returns_400_for_missing_required_parameters(
    admin_client: Client,
    json_function: Function,
    request_headers: dict,
):
    """Return a 400 for missing required parameters"""
    url = reverse("task-list")

    task_input = {
        "function_name": json_function.name,
        "package_name": json_function.package.name,
    }

    response = admin_client.post(
        url, data=task_input, content_type=MULTIPART_CONTENT, **request_headers
    )

    missing_parameter = "param.prop1"

    assert response.status_code == 400
    assert missing_parameter in response.json()


def test_no_result_returns_404(admin_client: Client, task: Task, request_headers: dict):
    """The task result is returned as the correct type"""

    url = f"{reverse('task-list')}{task.id}/result/"
    response = admin_client.get(url, **request_headers)

    assert response.status_code == 404


def test_result_type_is_preserved(
    admin_client: Client, task: Task, request_headers: dict
):
    """The task result is returned as the correct type"""
    url = f"{reverse('task-list')}{task.id}/result/"

    str_result = json.dumps("1234")
    int_result = json.dumps(1234)
    list_result = json.dumps([1, 2, 3, 4])
    dict_result = json.dumps({"one": 1, "two": 2, "three": 3, "four": 4})
    bool_result = json.dumps(True)

    task_result = TaskResult.objects.create(task=task)

    task_result.result = str_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is str

    task_result.result = int_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is int

    task_result.result = list_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is list

    task_result.result = dict_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is dict

    task_result.result = bool_result
    task_result.save()
    response = admin_client.get(url, **request_headers)
    assert type(response.data["result"]) is bool


def test_workflow_task(admin_client: Client, request_headers: dict, workflow: Workflow):
    """Create a Task for a Workflow"""
    url = reverse("task-list")

    assert not workflow.tasks.exists()

    task_input = {
        "workflow": str(workflow.id),
        "param.param1": 5,
    }

    response = admin_client.post(
        url,
        data=task_input,
        content_type=MULTIPART_CONTENT,
        **request_headers,
    )

    assert response.status_code == 201
    assert workflow.tasks.exists()
