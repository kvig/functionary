from core.auth import Role
from core.models import Environment, EnvironmentUserRole, TeamUserRole, User


def get_user_role(user: User, environment: Environment) -> str | None:
    """Get the effective role of the user with respect to the Environment and Team

    This function returns the effective UserRole the user has within an environment,
    which is the highest role that user is currently assigned between the environment
    and the team.

    If the user is not part of the environment, and they are not on the team,
    a None is returned.

    Args:
        user: User object for the user whose highest role you want to know
        environment: The target environment

    Returns:
        Return the string value of the Role or None
    """

    env_user_role = EnvironmentUserRole.objects.filter(
        user=user, environment=environment
    ).first()
    team_user_role = TeamUserRole.objects.filter(
        user=user, team=environment.team
    ).first()

    # Return None if neither exists
    if not env_user_role and not team_user_role:
        return None

    # Otherwise make sure that a role value exists for both. It doesn't matter which
    # role it comes from, just the greater value.
    env_role = env_user_role.role if env_user_role else team_user_role.role
    team_role = team_user_role.role if team_user_role else env_user_role.role

    return team_role if Role[team_role] > Role[env_role] else env_role


def get_user_roles(env: Environment) -> list[dict]:
    """Get list of roles for users who have access to the environment

    Get a list of users who have access to the environment. This includes
    the members of the team that the environment belongs to. The list will
    be sorted in decending order based on role.

    Args:
        env: The environment to get users from

    Returns:
        A list of dictionaries containing all the users who have access
        to the environment.
    """
    role_members: dict[User, EnvironmentUserRole | TeamUserRole] = get_members(env)

    users = []
    for user, role in role_members.items():
        is_env_role = isinstance(role, EnvironmentUserRole)
        user_elements = {}
        origin = role.environment if is_env_role else role.team
        user_elements["user"] = user
        user_elements["role"] = role.role
        user_elements["origin"] = origin.name
        user_elements["environment_user_role_id"] = role.id if is_env_role else None
        users.append(user_elements)

    # Sort users by their username in ascending order
    users.sort(key=lambda x: x["user"].username)
    return users


def get_members(env: Environment) -> dict[User, TeamUserRole | EnvironmentUserRole]:
    """Get a dict of all users with roles that have access to the environment

    Return a dict of all users with their role that have permission to access
    the environment either through a role on the team or environment.

    Args:
        env: The environment to get the users from

    Returns:
        A dict of all users with permission for the environment
    """
    roles = TeamUserRole.objects.filter(team=env.team).select_related("user", "team")
    members: dict[User, TeamUserRole | EnvironmentUserRole] = {
        role.user: role for role in roles
    }
    env_roles = EnvironmentUserRole.objects.filter(environment=env).select_related(
        "user", "environment"
    )
    members.update({role.user: role for role in env_roles.all()})
    return members
