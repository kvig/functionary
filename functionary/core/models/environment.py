""" Environment model """
import uuid

from django.db import models


class Environment(models.Model):
    """Second tier of a namespacing under Team. Environments act as the primary point
    of association for packages, tasks, etc.

    Attributes:
        id: unique identifier (UUID)
        name: the name of the environment
        team: the Team that this environment belongs to
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    team = models.ForeignKey(
        to="Team", related_name="environments", on_delete=models.CASCADE, db_index=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "name"], name="team_name_unique_together"
            ),
        ]

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    def variables(self, variable_names=None):
        """Retrieve the variables visible in this environment.

        This will by default return all variables associated with this
        Environment and add in any variables associated with the Team
        that haven't been overridden.

        Optionally pass in a list of strings of variable names to filter
        the returned values by.

        Parameters:
            variable_names: Optional list of strings of variable names to return
        """
        if variable_names:
            env_vars = list(self.vars.filter(variable_name__in=variable_names))
            env_var_names = [v.variable_name for v in env_vars]
            missing_variables = [
                name for name in variable_names if name not in env_var_names
            ]

            env_vars.extend(
                list(self.team.vars.filter(variable_name__in=missing_variables))
            )
        else:
            env_vars = list(self.vars.all())
            env_var_names = [v.variable_name for v in env_vars]
            env_vars.extend(
                list(self.team.vars.exclude(variable_name__in=env_var_names))
            )

        return env_vars
