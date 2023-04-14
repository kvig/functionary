import pytest

from core.models import (
    Function,
    Package,
    Task,
    TaskLog,
    Team,
    Variable,
    Workflow,
    WorkflowStep,
)
from core.utils.tasking import mark_error, publish_task, record_task_result, start_task


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def var1(environment):
    return Variable.objects.create(name="env_var1", environment=environment)


@pytest.fixture
def var2(environment):
    return Variable.objects.create(
        name="dont_hide", value="hi", environment=environment, protect=True
    )


@pytest.fixture
def var3(team):
    return Variable.objects.create(
        name="team_var1", team=team, value="hide me", protect=True
    )


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
        variables=["env_var1", "dont_hide", "team_var1"],
    )


@pytest.fixture
def task(function, environment, admin_user):
    return Task.objects.create(
        tasked_object=function,
        environment=environment,
        parameters={},
        creator=admin_user,
    )


@pytest.fixture
def workflow(environment, admin_user):
    return Workflow.objects.create(
        environment=environment, name="testworkflow", creator=admin_user
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


@pytest.fixture
def workflow_task(workflow, environment, admin_user):
    return Task.objects.create(
        tasked_object=workflow,
        environment=environment,
        parameters={},
        creator=admin_user,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("var1", "var2", "var3")
def test_output_masking(task):
    """Variables with protect set and greater than 4 characters should be masked in the
    task log. Masking is case sensitive."""
    output = "hi! Some people say hide me but others say hide or Hide me"
    task_result_message = {
        "task_id": task.id,
        "status": 0,
        "output": output,
        "result": "doesntmatter",
    }

    record_task_result(task_result_message)
    task_log = task.tasklog.log

    assert task_log.count("hi") == 2
    assert task_log.count("hide me") == 0
    assert task_log.count("Hide me") == 1


@pytest.mark.django_db
def test_publish_task_errors(mocker, task):
    """Verify that exceptions during publish_task result in a Task ERROR."""
    message = "An error occurred sending the message"

    def mock_send_message(param1, param2, param3, param4):
        """Mock the start_task function to return a failure"""
        raise ValueError(message)

    # Patch the imported send_message function
    mocker.patch("core.utils.tasking.send_message", mock_send_message)

    # Execute the first step, it should error
    with pytest.raises(ValueError):
        publish_task(task.id)

    # Make sure the task is marked as ERROR when it fails to be
    # sent to the runner
    workflow_task = Task.objects.filter(id=task.id).first()
    workflow_log = TaskLog.objects.filter(task=workflow_task).first()
    assert workflow_task is not None
    assert workflow_task.status == Task.ERROR
    assert workflow_log is not None
    assert message in workflow_log.log


@pytest.mark.django_db
def test_mark_error(mocker, task):
    """Test that calling mark_error changes the Tasks status and that
    calling it multiple times preserves existing messages."""
    message1 = "An error occurred sending the message"
    message2 = "There was a problem"
    error_message = "This is an error message"

    mark_error(task, message1)

    the_task = Task.objects.filter(id=task.id).first()
    the_log = TaskLog.objects.filter(task=the_task).first()

    assert the_task is not None
    assert the_task.status == Task.ERROR

    assert the_log is not None
    assert message1 in the_log.log
    assert error_message not in the_log.log

    # Call it again, with an error this time
    mark_error(task, message2, ValueError(error_message))

    the_task = Task.objects.filter(id=task.id).first()
    the_log = TaskLog.objects.filter(task=the_task).first()

    assert the_task is not None
    assert the_task.status == Task.ERROR

    assert the_log is not None
    assert message1 in the_log.log
    assert message2 in the_log.log
    assert error_message in the_log.log


@pytest.mark.django_db
def test_start_task_errors(mocker, workflow_task, workflow):
    """Test that an error executing a function results in a log being generated"""
    message = "An error occurred starting the task"

    def mock_start_workflow_task(_task):
        """Mock the _start_workflow_task function to return a failure"""
        raise ValueError(message)

    mocker.patch("core.utils.tasking._start_workflow_task", mock_start_workflow_task)

    start_task(workflow_task)

    task = Task.objects.get(tasked_id=workflow.id)
    task_log = TaskLog.objects.filter(task__id=task.id).first()
    assert task.status == Task.ERROR
    assert task_log is not None
    assert message in task_log.log


@pytest.mark.django_db
def test_step_failure_errors_workflow(mocker, environment, admin_user, workflow, step1):
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
        creator=admin_user,
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
