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
@pytest.mark.usefixtures("team_var1", "team_shared_var1", "env_var1")
def test_team_variables(team):
    """Team variables include only those explicitly assigned to the team"""
    assert team.vars.count() == 2


@pytest.mark.django_db
@pytest.mark.usefixtures("env_var1", "env_var2", "env_shared_var1", "team_var1")
def test_environment_variables(environment):
    """Environment variables include only those explicitly assigned to the env"""
    assert environment.vars.count() == 3
