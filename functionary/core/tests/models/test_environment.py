import pytest

from core.models import Team, Variable


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def env_var1(environment):
    return Variable.objects.create(name="env_var1", environment=environment)


@pytest.fixture
def env_var2(environment):
    return Variable.objects.create(name="var2", environment=environment)


@pytest.fixture
def env_shared_var1(environment):
    return Variable.objects.create(name="var1", environment=environment, value="env")


@pytest.fixture
def team_shared_var1(team):
    return Variable.objects.create(name="var1", team=team, value="team")


@pytest.fixture
def team_var1(team):
    return Variable.objects.create(name="team_var1", team=team)


@pytest.mark.django_db
@pytest.mark.usefixtures("env_var1", "env_var2", "env_shared_var1", "team_shared_var1")
def test_variable_inheritence(environment, team_var1):
    """Environments inherit variables from their team"""
    assert environment.variables.count() == 4
    assert environment.variables.filter(name=team_var1.name).exists()


@pytest.mark.django_db
def test_variable_override_inherited(environment, env_shared_var1, team_shared_var1):
    """Environment variables override inherited team variables"""
    shared_var = environment.variables.get(name=team_shared_var1.name)
    assert shared_var.value == env_shared_var1.value
