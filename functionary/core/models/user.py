from typing import TYPE_CHECKING, Set

from django.apps import apps
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from core.auth import ROLE_PERMISSION_MAP

if TYPE_CHECKING:
    from core.models import Environment, Team


class User(AbstractBaseUser, PermissionsMixin):
    """User model override.

    TODO Overhaul Django's base authentication/authorization. The standard Django
    permissions model is unlikely to map well to our use case. We're using
    PermissionMixin for now, but will eventually need to move away from it.

    Attributes:
        username: unique identifying string for the user.
        password: possibly temporary until a better authentication method exists.
        email: user email address.
        is_active: whether this user is considered active. Defaults to True.
        last_login: when this user last logged in to their account.
        created_at: when the user was first added to the system. Defaults to now.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=64,
        db_index=True,
        unique=True,
        validators=[username_validator],
    )
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # TODO Possibly remove these fields after moving to our own permissions scheme
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def team_permissions(self, team: "Team") -> Set[str]:
        """Retrieves the set of permissions a user has for a given Team

        Args:
            team: Team object to check against

        Returns:
            A set of strings representing the user's permissions.
        """
        roles = self.teamuserroles.filter(team=team).values_list("role", flat=True)
        permissions = set()

        for role in roles:
            permissions.update(ROLE_PERMISSION_MAP[role])

        return permissions

    def environment_permissions(
        self, environment: "Environment", inherited: bool = False
    ) -> Set[str]:
        """Retrieves the set of permissions a user has for a given Envrionment

        Args:
            environment: Environment object to check against
            inherited: Whether or not to include permissions inherited from a role on
                       Environment's Team.

        Returns:
            A set of strings representing the user's permissions.
        """
        roles = self.environmentuserroles.filter(environment=environment).values_list(
            "role", flat=True
        )

        permissions = set()

        for role in roles:
            permissions.update(ROLE_PERMISSION_MAP[role])

        if inherited:
            permissions.update(self.team_permissions(environment.team))

        return permissions

    @property
    def environments(self):
        """Retrieves the Envrionments the user is permitted to access.

        Returns:
            A set of Environments from the Users Team roles combined with
            any Environment roles.
        """
        Environment = apps.get_model("core", "Environment")
        envs = Environment.objects.filter(
            models.Q(team__user_roles__user=self) | models.Q(user_roles__user=self)
        ).distinct()
        return envs
