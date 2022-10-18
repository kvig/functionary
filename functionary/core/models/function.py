""" Function model """
import uuid

from django.db import models


class Function(models.Model):
    """Function is a unit of work that can be tasked

    Attributes:
        id: unique identifier (UUID)
        package: the package that the function is a part of
        name: internal name that published package definition keys off of
        display_name: optional display name
        summary: short description of the function
        description: more details about the function
        schema: the function's OpenAPI definition
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    package = models.ForeignKey(
        to="Package", on_delete=models.CASCADE, related_name="functions"
    )

    # TODO: This shouldn't be changeable after creation
    name = models.CharField(max_length=64, blank=False)

    display_name = models.CharField(max_length=64, null=True)
    summary = models.CharField(max_length=128, null=True)
    description = models.TextField(null=True)
    return_type = models.CharField(max_length=64, null=True)
    output_format = models.CharField(max_length=64, null=True)
    schema = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["package", "name"], name="package_name_unique_together"
            )
        ]

    def __str__(self):
        return self.name
