""" Build model """
import uuid

from django.conf import settings
from django.db import models

from core.models import Environment, Package
from core.models.mixins import ModelSaveHookMixin


class Build(ModelSaveHookMixin, models.Model):
    """Tracks the package build status and history

    Attributes:
        created_at: time that the build was created
        updated_at: time of the most recent status update
        status: current status of the build
        package: reference to the Package created by a build
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETE, "Complete"),
        (ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    creator = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    environment = models.ForeignKey(to=Environment, on_delete=models.CASCADE)
    package = models.ForeignKey(
        to=Package, on_delete=models.CASCADE, blank=False, null=False
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"], name="build_status_created_at"
            ),
            models.Index(
                fields=["status", "updated_at"], name="build_status_updated_at"
            ),
        ]

    def __str__(self):
        return f"{self.id}"

    def error(self):
        """Saves status as `ERROR`"""
        self._update_status(self.ERROR)

    def pending(self):
        """Saves status as `PENDING`"""
        self._update_status(self.PENDING)

    def complete(self):
        """Saves status as `COMPLETE`"""
        self._update_status(self.COMPLETE)
        self.package.complete()
        # Two steps to ensure proper state transitions for packages.
        self.package.activate()

    def in_progress(self):
        """Saves status as `IN_PROGRESS`"""
        self._update_status(self.IN_PROGRESS)

    def _update_status(self, status: str) -> None:
        """Update status of the build"""
        if status != self.status:
            self.status = status
            self.save()

    def post_save(self):
        if self.status in [Build.COMPLETE, Build.ERROR]:
            self.resources.delete()


class BuildResource(models.Model):
    """Houses resources needed to perform a package build

    Attributes:
        package_contents: gzipped tarball containing package files
        package_definition: defines the package and its functions
        package_definition_version: the schema version used by package_definition
        build: the build with which these resources are associated
    """

    package_contents = models.BinaryField()
    package_definition = models.JSONField()
    package_definition_version = models.CharField(max_length=16)
    build = models.OneToOneField(
        to=Build, on_delete=models.CASCADE, related_name="resources"
    )

    @property
    def image_details(self):
        # This isn't a version independent way of accessing the definition,
        # but I don't see name or language moving out of the top level unless
        # we were to support multiple languages in a single package.
        name = self.package_definition["name"]
        language = self.package_definition["language"]
        dockerfile = f"builder/docker/{language}.Dockerfile"
        image_name = f"{self.build.environment.id}/{name}:{self.build.id}"

        return (image_name, dockerfile)
