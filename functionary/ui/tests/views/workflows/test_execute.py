import pytest

from core.auth import Role
from core.models import (
    EnvironmentUserRole,
    Function,
    Package,
    Task,
    TaskLog,
    Team,
    User,
    Workflow,
    WorkflowStep,
)
from core.utils.parameter import PARAMETER_TYPE
from core.utils.tasking import mark_error


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
def workflow(environment, user_with_access):
    return Workflow.objects.create(
        environment=environment, name="testworkflow", creator=user_with_access
    )


@pytest.fixture
def step2(workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="step2",
        function=function,
        parameter_template='{"prop1": 42}',
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
def test_step_failure_errors_workflow(
    mocker, environment, user_with_access, workflow, step1
):
    """Verify that the step and parent tasks are marked as ERROR and
    a log is generated when a workflow step fails to execute."""
    message = "An error occurred starting the workflow"

    def mock_start_task(_task):
        mark_error(_task, message)

    # Patch the imported start_task in the workflow_step file, not
    # in the file that its defined in
    mocker.patch("core.models.workflow_step.start_task", mock_start_task)

    workflow_task = Task(
        environment=environment,
        creator=user_with_access,
        tasked_object=workflow,
        parameters={},
        return_type=None,
    )
    workflow_task.status = Task.IN_PROGRESS
    workflow_task.save()
    assert workflow_task.status == Task.IN_PROGRESS

    # Execute the first step, it should error
    step1.execute(workflow_task)

    # Make sure the parent workflow is errored and has an associated log
    assert workflow_task.status == Task.ERROR
    workflow_task_log = TaskLog.objects.filter(task__id=workflow_task.id).first()
    assert workflow_task_log is not None
    assert step1.name in workflow_task_log.log

    step_task = Task.objects.get(tasked_id=step1.function_id)
    assert step_task is not None
    assert step_task.status == Task.ERROR

    step_task_log = TaskLog.objects.filter(task=step_task).first()
    assert step_task_log is not None
    assert message in step_task_log.log
