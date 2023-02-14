import pytest

from core.models import Function, Package, Task, Team, Variable
from core.utils.tasking import record_task_result


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
        function=function,
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
