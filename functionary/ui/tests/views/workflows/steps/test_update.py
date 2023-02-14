from uuid import uuid4

import pytest
from django.urls import reverse

from core.auth import Role
from core.models import (
    EnvironmentUserRole,
    Function,
    Package,
    Team,
    User,
    Workflow,
    WorkflowStep,
)
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def user_with_access(environment):
    user_obj = User.objects.create(username="hasaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.ADMIN.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_without_access():
    return User.objects.create(username="noaccess")


@pytest.fixture
def workflow(environment, user_with_access):
    return Workflow.objects.create(
        environment=environment, name="testworkflow", creator=user_with_access
    )


@pytest.fixture
def step3(workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step3",
        function=function,
        parameter_template='{"prop1": 42}',
    )


@pytest.fixture
def step2(step3, workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step2",
        function=function,
        parameter_template='{"prop1": 42}',
        next=step3,
    )


@pytest.fixture
def step1(step2, workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step1",
        function=function,
        parameter_template='{"prop1": 42}',
        next=step2,
    )


@pytest.mark.django_db
def test_move_workflow_step(client, user_with_access, workflow, step1, step2, step3):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": step3.pk})

    assert response.status_code == 200

    # New order should be step2, step1, step3
    steps = workflow.ordered_steps
    assert steps[0] == step2
    assert steps[1] == step1
    assert steps[2] == step3


@pytest.mark.django_db
def test_move_workflow_step_returns_400_for_invalid_next_value(
    client, user_with_access, workflow, step1
):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": uuid4()})

    assert response.status_code == 400


@pytest.mark.django_db
def test_move_workflow_step_returns_403_for_no_access(
    client, user_without_access, workflow, step1, step3
):
    client.force_login(user_without_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": workflow.pk, "pk": step1.pk}
    )
    response = client.post(url, {"next": step3.pk})

    assert response.status_code == 403


@pytest.mark.django_db
def test_move_workflow_step_returns_404_when_not_found(client, user_with_access):
    client.force_login(user_with_access)

    url = reverse(
        "ui:workflowstep-move", kwargs={"workflow_pk": uuid4(), "pk": uuid4()}
    )
    response = client.post(url, {"next": uuid4()})

    assert response.status_code == 404
