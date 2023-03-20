import pytest

from core.auth import Role
from core.models import EnvironmentUserRole, Team, TeamUserRole, User
from ui.views.team.utils import get_user_roles


@pytest.fixture
def team():
    team = Team.objects.create(name="team")
    return team


@pytest.fixture
def team_no_users():
    team = Team.objects.create(name="team_without_users")
    return team


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def user_with_no_role():
    user_obj = User.objects.create(username="no_role")

    return user_obj


@pytest.fixture
def user_with_team_role(team):
    user_obj = User.objects.create(username="with_team_role")

    TeamUserRole.objects.create(user=user_obj, role=Role.OPERATOR.name, team=team)

    return user_obj


@pytest.fixture
def user_with_env_role(environment):
    user_obj = User.objects.create(username="with_env_role")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.DEVELOPER.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_with_env_admin_and_team_role(team, environment):
    user_obj = User.objects.create(username="with_higher_env_role")

    TeamUserRole.objects.create(user=user_obj, role=Role.READ_ONLY.name, team=team)
    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.ADMIN.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_with_team_admin_and_env_role(team, environment):
    user_obj = User.objects.create(username="with_higher_team_role")

    TeamUserRole.objects.create(user=user_obj, role=Role.ADMIN.name, team=team)
    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.DEVELOPER.name, environment=environment
    )

    return user_obj


@pytest.fixture
def user_with_both_roles(team, environment):
    user_obj = User.objects.create(username="with_both_roles")

    TeamUserRole.objects.create(user=user_obj, role=Role.DEVELOPER.name, team=team)
    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.DEVELOPER.name, environment=environment
    )

    return user_obj


@pytest.mark.django_db
def test_get_user_roles(
    team,
    user_with_no_role,
    user_with_team_role,
    user_with_env_role,
    user_with_both_roles,
    user_with_env_admin_and_team_role,
    user_with_team_admin_and_env_role,
):
    """team with users is ordered by username and returns only the
    team role for a given user"""
    user_roles = get_user_roles(team)

    assert len(user_roles) == 4
    assert user_roles[0]["user"] == user_with_both_roles
    assert user_roles[1]["user"] == user_with_env_admin_and_team_role
    assert user_roles[1]["role"] == Role.READ_ONLY.name
    assert user_roles[2]["user"] == user_with_team_admin_and_env_role
    assert user_roles[2]["role"] == Role.ADMIN.name
    assert user_roles[3]["user"] == user_with_team_role


@pytest.mark.django_db
def test_get_user_roles_no_roles(team_no_users):
    """a team without roles has no user roles"""
    user_roles = get_user_roles(team_no_users)
    assert len(user_roles) == 0
