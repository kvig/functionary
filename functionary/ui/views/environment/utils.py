from core.auth import Role
from core.models import Environment, EnvironmentUserRole, TeamUserRole, User


def _get_effective_role(
    role_1: EnvironmentUserRole | TeamUserRole | None,
    role_2: EnvironmentUserRole | TeamUserRole | None,
) -> EnvironmentUserRole | TeamUserRole | None:
    """Compares two roles and returns the more permissive of the two.

    This checks the role permissions on the passed in UserRoles, returning the
    higher of the two. If they are equal, role_1 will be returned."""

    if not role_1:
        return role_2
    elif not role_2:
        return role_1

    return role_2 if Role[role_2.role] > Role[role_1.role] else role_1


def get_user_role(user: User, environment: Environment) -> str | None:
    """Get the effective role of the user with respect to the Environment and Team

    This function returns the string of the effective role the user has within
    an environment, which is the highest permission role that user is currently
    assigned between the environment and the team.

    If the user is not part of the environment and they are not on the team,
    a None is returned.

    Args:
        user: The user whose highest role you want to know
        environment: The target environment

    Returns:
        The string value of the Role or None
    """

    env_user_role = EnvironmentUserRole.objects.filter(
        user=user, environment=environment
    ).first()
    team_user_role = TeamUserRole.objects.filter(
        user=user, team=environment.team
    ).first()

    effective = _get_effective_role(env_user_role, team_user_role)
    return effective.role if effective else None


def get_user_roles(env: Environment) -> list[dict]:
    """Get list of roles for users who have access to the environment

    Get a list of users who have access to the environment. This includes
    the members of the team that the environment belongs to. The list will
    be sorted by user name.

    Args:
        env: The environment to get users from

    Returns:
        A list of dictionaries containing all the users who have access
        to the environment.
    """
    role_members: dict[
        User,
        tuple[EnvironmentUserRole | None, EnvironmentUserRole | TeamUserRole],
    ] = get_members(env)

    users = []
    for user, (env_role, effective_role) in role_members.items():
        effective_is_env = isinstance(effective_role, EnvironmentUserRole)
        user_elements = {}
        origin = effective_role.environment if effective_is_env else effective_role.team
        user_elements["user"] = user
        user_elements["role"] = effective_role.role
        user_elements["origin"] = origin.name
        user_elements["environment_user_role_id"] = env_role.id if env_role else None
        users.append(user_elements)

    # Sort users by their username in ascending order
    users.sort(key=lambda x: x["user"].username)
    return users


def get_members(
    env: Environment,
) -> dict[User, tuple[EnvironmentUserRole | None, EnvironmentUserRole | TeamUserRole]]:
    """Get a dict of all users with roles that have access to the environment.

    Return a dict of all users with their roles that have permission to access
    the environment either through a role on the team or environment.

    Args:
        env: The environment to get the users from

    Returns:
        A dict mapping each user with permission for the environment to a tuple
        of their corresponding EnvironmentUserRole(if any) and their effective
        user role.
    """
    team_roles = TeamUserRole.objects.filter(team=env.team).select_related(
        "user", "team"
    )
    members: dict[
        User,
        tuple[EnvironmentUserRole | None, EnvironmentUserRole | TeamUserRole],
    ] = {role.user: (None, role) for role in team_roles}

    env_roles = EnvironmentUserRole.objects.filter(environment=env).select_related(
        "user", "environment"
    )
    for role in env_roles:
        existing_role = members.get(role.user, (None, None))
        effective_role = _get_effective_role(role, existing_role[1])
        members[role.user] = (role, effective_role)

    return members
