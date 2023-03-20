from core.models import Team, TeamUserRole


def get_user_roles(team: Team) -> list[dict]:
    """Get role data about all the users in the team.

    Get a list of metadata about the user roles that are currently
    assigned to the given team.

    Args:
        team: The team to get the users from

    Returns:
        A list of dictionaries containing all the users who have access
        to the team.
    """
    team_user_roles: list[TeamUserRole] = list(
        TeamUserRole.objects.filter(team=team).select_related("user", "team").all()
    )

    user_details = []
    for team_user_role in team_user_roles:
        user_element = {}
        user_element["user"] = team_user_role.user
        user_element["role"] = team_user_role.role
        user_element["team_user_role_id"] = team_user_role.id
        user_details.append(user_element)

    # Sort users by their username in ascending order
    user_details.sort(key=lambda x: x["user"].username)
    return user_details
