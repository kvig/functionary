import pytest

from core.auth import Role
from core.models import EnvironmentUserRole, Team, TeamUserRole, User
from ui.views.environment.utils import get_members, get_user_role, get_user_roles


@pytest.fixture
def team():
    team = Team.objects.create(name="team")
    return team


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def environment_no_users():
    team = Team.objects.create(name="team_without_users")
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
def test_get_members_no_team(environment, user_with_env_role):
    """returns the environment role when set"""
    user_roles = get_members(environment)

    assert len(user_roles) == 1
    assert isinstance(user_roles[user_with_env_role][0], EnvironmentUserRole)
    assert isinstance(user_roles[user_with_env_role][1], EnvironmentUserRole)


@pytest.mark.django_db
def test_get_members_only_team(environment, user_with_team_role):
    """returns the team role if the user doesn't have an explicit environment role"""
    user_roles = get_members(environment)

    assert len(user_roles) == 1
    assert user_roles[user_with_team_role][0] is None
    assert isinstance(user_roles[user_with_team_role][1], TeamUserRole)


@pytest.mark.django_db
def test_get_members_both_roles(environment, user_with_both_roles):
    """user with two equivalent roles returns the environment role"""
    user_roles = get_members(environment)

    assert len(user_roles) == 1
    assert isinstance(user_roles[user_with_both_roles][0], EnvironmentUserRole)
    assert isinstance(user_roles[user_with_both_roles][1], EnvironmentUserRole)


@pytest.mark.django_db
def test_get_members_multiple_users(
    environment,
    user_with_team_role,
    user_with_env_role,
    user_with_both_roles,
    user_with_env_admin_and_team_role,
    user_with_team_admin_and_env_role,
):
    """returns the most permissive role value"""
    user_roles = get_members(environment)

    assert len(user_roles) == 5
    assert user_roles[user_with_both_roles][1].role == Role.DEVELOPER.name
    assert isinstance(
        user_roles[user_with_env_admin_and_team_role][0], EnvironmentUserRole
    )
    assert isinstance(
        user_roles[user_with_env_admin_and_team_role][1], EnvironmentUserRole
    )
    assert user_roles[user_with_env_admin_and_team_role][1].role == Role.ADMIN.name

    assert isinstance(
        user_roles[user_with_team_admin_and_env_role][0], EnvironmentUserRole
    )
    assert isinstance(user_roles[user_with_team_admin_and_env_role][1], TeamUserRole)
    assert user_roles[user_with_team_admin_and_env_role][1].role == Role.ADMIN.name
    assert user_roles[user_with_env_role][1].role == Role.DEVELOPER.name
    assert user_roles[user_with_team_role][1].role == Role.OPERATOR.name


@pytest.mark.django_db
def test_get_user_role_without_roles(
    environment_no_users,
    user_with_env_role,
    user_with_no_role,
):
    """None is returned for users without roles in an environment"""
    user_role = get_user_role(user_with_env_role, environment_no_users)
    assert user_role is None

    user_role = get_user_role(user_with_no_role, environment_no_users)
    assert user_role is None


@pytest.mark.django_db
def test_get_user_role_has_roles(
    environment,
    user_with_team_role,
    user_with_env_role,
):
    """returnes the expected single role for the user"""
    user_role = get_user_role(user_with_env_role, environment)
    assert user_role == Role.DEVELOPER.name

    user_role = get_user_role(user_with_team_role, environment)
    assert user_role == Role.OPERATOR.name


@pytest.mark.django_db
def test_get_user_role_user_has_multiple_roles(
    environment,
    user_with_env_admin_and_team_role,
    user_with_team_admin_and_env_role,
    user_with_both_roles,
):
    """get_user_role returns the highest permission a user has"""
    user_role = get_user_role(user_with_env_admin_and_team_role, environment)
    assert user_role == Role.ADMIN.name

    user_role = get_user_role(user_with_team_admin_and_env_role, environment)
    assert user_role == Role.ADMIN.name

    user_role = get_user_role(user_with_both_roles, environment)
    assert user_role == Role.DEVELOPER.name


@pytest.mark.django_db
def test_get_user_roles(
    environment,
    user_with_team_role,
    user_with_env_role,
    user_with_both_roles,
    user_with_env_admin_and_team_role,
    user_with_team_admin_and_env_role,
):
    """environment with users is ordered by username and returns the
    environment role when a team role is also present for a given user.
    Must also return the highest permissive role for a multi-role user."""
    user_roles = get_user_roles(environment)

    assert len(user_roles) == 5
    assert user_roles[0]["user"] == user_with_both_roles
    assert user_roles[0]["origin"] == environment.name
    assert user_roles[0]["environment_user_role_id"] is not None
    assert user_roles[1]["user"] == user_with_env_role
    assert user_roles[1]["environment_user_role_id"] is not None
    assert user_roles[2]["user"] == user_with_env_admin_and_team_role
    assert user_roles[2]["origin"] == environment.name
    assert user_roles[2]["environment_user_role_id"] is not None
    assert user_roles[2]["role"] == Role.ADMIN.name
    assert user_roles[3]["user"] == user_with_team_admin_and_env_role
    assert user_roles[3]["origin"] == environment.team.name
    assert user_roles[3]["environment_user_role_id"] is not None
    assert user_roles[3]["role"] == Role.ADMIN.name
    assert user_roles[4]["user"] == user_with_team_role
    assert user_roles[4]["environment_user_role_id"] is None


@pytest.mark.django_db
def test_get_user_roles_no_roles(environment_no_users):
    """an environment without roles has no user roles"""
    user_roles = get_user_roles(environment_no_users)
    assert len(user_roles) == 0
