import pytest
from django.core.exceptions import ValidationError

from core.models import Function, Package, Task, Team, Variable


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
    return Variable.objects.create(name="env_var2", environment=environment)


@pytest.fixture
def var3(team):
    return Variable.objects.create(name="team_var1", team=team)


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        environment=package.environment,
        package=package,
        variables=["env_var1"],
        active=True,
    )


@pytest.fixture
def inactive_function(package):
    return Function.objects.create(
        name="inactivefunction",
        environment=package.environment,
        package=package,
        variables=["env_var1"],
        active=False,
    )


@pytest.fixture
def task(function, var1, var2, var3, environment, admin_user):
    return Task.objects.create(
        function=function,
        environment=environment,
        parameters={"prop1": "value1"},
        creator=admin_user,
    )


@pytest.mark.django_db
def test_list(task):
    """List all teams"""
    task_vars = task.variables.all()
    assert len(task_vars) == 1
    assert len(task.environment.variables) > 1


@pytest.mark.django_db
def test_task_function_must_be_active(inactive_function, environment, admin_user):
    with pytest.raises(ValidationError):
        task = Task(
            function=inactive_function,
            environment=environment,
            parameters={"prop1": "value1"},
            creator=admin_user,
        )
        task.clean()
