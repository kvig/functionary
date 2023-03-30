""" Package model """
import uuid

from django.conf import settings
from django.db import models
from django.db.models import QuerySet

from core.models import Environment

# Pending status represents the package is being built
# Complete status represents the package has been successfully built at least once
# Enabled status represents that the package is can be used by users
# Disabled status represents that the package cannot be used by users
PENDING = "PENDING"
COMPLETE = "COMPLETE"
ENABLED = "ENABLED"
DISABLED = "DISABLED"


class ActivePackageManager(models.Manager):
    """Manager for filtering out disabled packages."""

    def get_queryset(self):
        return super().get_queryset().filter(status=ENABLED)


class Package(models.Model):
    """A Package is a grouping of functions made available for tasking

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this package belongs to
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: summary of the package
        description: more details about the package
        language: the language the functions in the package are written in
        status: represents the status of the package
        image_name: the docker image name for the package
    """

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETE, "Complete"),
        (ENABLED, "Enabled"),
        (DISABLED, "Disabled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to=Environment, on_delete=models.CASCADE)

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=128, null=True)
    description = models.TextField(null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)

    # TODO: Restrict to list of choices?
    language = models.CharField(max_length=64)

    image_name = models.CharField(max_length=256)

    objects = models.Manager()
    active_objects = ActivePackageManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"], name="environment_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name

    def update_image_name(self, image_name: str) -> None:
        """Update the package's image name with the given image name"""
        self.image_name = image_name
        self.save()

    def complete(self) -> None:
        """Mark package as completed if it was previously in `PENDING` status"""
        # NOTE: This is to prevent overwriting the enabled/disabled status set by users
        if self.status == PENDING:
            self._update_status(COMPLETE)

    def enable(self) -> None:
        """Enable package as it's associated functions"""
        # Prevent the user from manually enabling a package that hasn't
        # yet successfully finished being built.
        if self.status in [COMPLETE, DISABLED]:
            self._update_status(ENABLED)

    def disable(self) -> None:
        """Disable package and it's associated functions"""
        # Prevent the user from manually disabling a package that hasn't
        # yet successfully finished being built.
        if self.status == ENABLED:
            self._update_status(DISABLED)

            for function in self.active_functions.all():
                function.update_scheduled_tasks(enable=False)

    def _update_status(self, status: str) -> None:
        """Update status of the package"""
        if status != self.status:
            self.status = status
            self.save()

    @property
    def render_name(self) -> str:
        """Returns the template-renderable name of the package"""
        return self.display_name if self.display_name else self.name

    @property
    def full_image_name(self) -> str:
        """Returns the package's image name prepended with the registry info"""
        return f"{settings.REGISTRY}/{self.image_name}"

    @property
    def active_functions(self) -> QuerySet:
        """Returns a QuerySet of all active functions in the package"""
        return self.functions.filter(active=True)

    @property
    def enabled(self) -> bool:
        """Returns true if the package is enabled"""
        return self.status == ENABLED
