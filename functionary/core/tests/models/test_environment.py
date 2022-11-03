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
def test_list(team, environment, env1, env2, var1, team1, team2):
    """List all variables visible in the environment"""
    assert len(environment.vars.all()) == 3
    assert len(team.vars.all()) == 2

    # Make sure the team variable "var1" only occurs once
    # and is the environment version, not the team one
    env_vars = environment.variables.all()
    assert len(env_vars) == 4
    v1 = environment.variables.filter(name="var1").all()
    assert len(v1) == 1
    assert v1[0].team is None
    assert v1[0].environment == environment
