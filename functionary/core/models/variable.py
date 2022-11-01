""" Package model """
import uuid

from django.core.validators import RegexValidator
from django.db import models

VALID_ENV_NAME = RegexValidator(
    regex="[A-Z_][A-Z0-9_]*",
    message="Invalid environment variable name. Must be in [A-Z0-9_]",
)


class Variable(models.Model):
    """An Environment Variable is set in the system and set in
    the runtime environment for tasks as required by the function
    in the package.yaml.

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this variable belongs to
        team: the team that this variable belongs to
        variable_name: name of the environment variable to set
        description: more details about the package
        value: value of the environment variable
        protect: True to protect the value of this variable
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(
        "Environment",
        on_delete=models.CASCADE,
        related_name="vars",
        blank=True,
        null=True,
    )
    team = models.ForeignKey(
        "Team", on_delete=models.CASCADE, related_name="vars", blank=True, null=True
    )

    name = models.CharField(max_length=255, validators=[VALID_ENV_NAME], blank=False)
    description = models.TextField(null=True)
    value = models.TextField(max_length=32767, blank=False)
    protect = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"],
                name="environment_variable_name_unique_together",
            ),
            models.UniqueConstraint(
                fields=["team", "name"],
                name="team_variable_name_unique_together",
            ),
            models.CheckConstraint(
                name="variable_only_one_team_or_environment",
                check=(
                    models.Q(team__isnull=True, environment__isnull=False)
                    | models.Q(team__isnull=False, environment__isnull=True)
                ),
            ),
        ]

    @property
    def parent(self):
        return self.team if self.team is not None else self.environment

    def __str__(self):
        return f"{self.name} - {self.parent.name}"
