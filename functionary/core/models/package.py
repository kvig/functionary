""" Package model """
import uuid

from django.conf import settings
from django.db import models

from core.models import Environment


class Package(models.Model):
    """A Package is a grouping of functions made available for tasking

    Attributes:
        id: unique identifier (UUID)
        environment: the environment that this package belongs to
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: summary of the package
        description: more details about the package
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    environment = models.ForeignKey(to=Environment, on_delete=models.CASCADE)

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)

    # TODO: Restrict to list of choices?
    language = models.CharField(max_length=64)

    image_name = models.CharField(max_length=256)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "name"], name="environment_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name

    @property
    def full_image_name(self):
        return f"{settings.REGISTRY}/{self.image_name}"
