import pytest

from core.models import Team, Variable


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def env1(environment):
    return Variable.objects.create(name="env_var1", environment=environment)


@pytest.fixture
def env2(environment):
    return Variable.objects.create(name="var2", environment=environment)


@pytest.fixture
def var1(environment):
    return Variable.objects.create(name="var1", environment=environment)


@pytest.fixture
def team1(team):
    return Variable.objects.create(name="var1", team=team)


@pytest.fixture
def team2(team):
    return Variable.objects.create(name="team_var1", team=team)


@pytest.mark.django_db
def test_team(team, team1, team2):
    """List all team variables"""
    assert len(team.vars.all()) == 2


@pytest.mark.django_db
def test_env(environment, env1, env2, var1):
    """List all environment variables"""
    assert len(environment.vars.all()) == 3
