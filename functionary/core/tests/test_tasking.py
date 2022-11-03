import pytest

from core.models import Function, Package, Task, Team, Variable

from ..utils.tasking import _protect_output


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
    function_schema = {
        "title": "test",
        "type": "object",
        "variables": ["env_var1", "dont_hide", "team_var1"],
        "properties": {"prop1": {"type": "integer"}},
    }
    return Function.objects.create(
        name="testfunction",
        package=package,
        schema=function_schema,
        variables=["env_var1", "dont_hide", "team_var1"],
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
def test_output_masking(task):
    """Test that variables with protect set and greater than 4
    characters are masked. Masking is currently case sensitive."""
    output = "hi! Some people say hide me but others say hide or Hide me"
    protected = _protect_output(task, output)
    assert protected.count("hi") == 2
    assert protected.count("hide me") == 0
    assert protected.count("Hide me") == 1
