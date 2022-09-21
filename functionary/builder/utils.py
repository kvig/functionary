import datetime
import io
import logging
import os
import shutil
import tarfile
from typing import TypeVar
from uuid import UUID

import docker
import yaml
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.template.loader import get_template
from pydantic import Field, Json, create_model

from core.models import Environment, Function, Package, User

from .celery import app
from .exceptions import InvalidPackage
from .models import Build, BuildResource

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def extract_package_definition(package_contents: bytes) -> dict:
    """Extracts the package.yaml from a package tarball

    Args:
        package_contents: gzipped tarball of a package

    Returns:
        The package definition yaml loaded as a dict
    """
    package_contents_io = io.BytesIO(package_contents)

    try:
        tarball = tarfile.open(fileobj=package_contents_io, mode="r")
    except tarfile.ReadError:
        raise InvalidPackage(
            "Could not untar package file. Make sure it is a valid gzipped tarball."
        )

    def close_files():
        package_contents_io.close()
        tarball.close()

    try:
        package_definition_io = tarball.extractfile("package.yaml")
    except KeyError:
        close_files()
        raise InvalidPackage("package.yaml not found")

    if package_definition_io is None:
        close_files()
        raise InvalidPackage("package.yaml found, but is not a regular file")

    package_definition = yaml.safe_load(package_definition_io.read())
    close_files()

    return package_definition


def initiate_build(
    creator: User,
    environment: Environment,
    package_contents: bytes,
    package_definition: dict,
    package_definition_version: str,
) -> Build:
    """Creates the Build and BuildResource instances necessary to initiate a build and
    then creates the task for the worker that will perform the build.

    Args:
        creator: The User initiating the build
        environment: The environment that the package should be published under
        package_contents: A gzipped file containing the package to be built
        package_definition: dict containing the package definition
    """
    with transaction.atomic():
        build = Build.objects.create(creator=creator, environment=environment)

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id)

    return build


@app.task
def build_package(build_id: UUID):
    """Retrieve the resources for Build and use them to build and push the package
    docker image

    Args:
        build_id: ID of the build being executed
    """
    docker_client = docker.from_env()

    # TODO: Catch exceptions and record failures. Also, what happens to the image we
    #       pushed? Should it be deleted?
    logger.info(f"Starting build {build_id}")

    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build_id}"
    os.makedirs(workdir)

    build = Build.objects.select_related("environment").get(id=build_id)
    environment = build.environment
    package_contents = build.resources.package_contents
    package_definition = build.resources.package_definition

    # TODO: This sort of direct access of package_definition should be discouraged, as
    #       it results in package schema parsing being spread throughout the code. It
    #       should live in one place and we should call helpers in places like this.
    name = package_definition["name"]
    language = package_definition["language"]
    dockerfile = f"builder/docker/{language}.Dockerfile"
    image_name = f"{environment.id}/{name}:{build_id}"
    full_image_name = f"{settings.REGISTRY}/{image_name}"

    _extract_package_contents(package_contents, workdir)
    _load_dockerfile_template(dockerfile, workdir)

    image, build_log = docker_client.images.build(
        path=workdir,
        pull=True,
        forcerm=True,
        tag=full_image_name,
    )

    docker_client.images.push(full_image_name)

    logger.debug(f"Cleaning up remnants of build {build_id}")
    docker_client.images.remove(image.id)
    shutil.rmtree(workdir)

    with transaction.atomic():
        package = _create_package_from_definition(
            package_definition, environment, image_name
        )
        build.status = Build.COMPLETE
        build.package = package
        build.save()

        # TODO: The Build model should just clean its own resources with post_save hook
        build.resources.delete()

    logger.info(f"Build {build_id} COMPLETE")


def _extract_package_contents(package_contents: bytes, workdir: str) -> None:
    """Extract the package tarball"""
    package_contents_io = io.BytesIO(package_contents)
    tarball = tarfile.open(fileobj=package_contents_io, mode="r")
    tarball.extractall(workdir)
    tarball.close()
    package_contents_io.close()


def _load_dockerfile_template(dockerfile_template: str, workdir: str) -> None:
    """Render the dockfile template and write it to the working directory"""
    template = get_template(dockerfile_template)
    context = {"registry": settings.REGISTRY}

    with open(f"{workdir}/Dockerfile", "w") as dockerfile:
        dockerfile.write(template.render(context=context))


def _create_package_from_definition(
    package_definition: dict, environment: Environment, image_name: str
) -> Package:
    """Create a package and functions from definition file"""
    # TODO: Manually parsing for now, but this should be codified somewhere, with
    #       the parsing informed by package_definition_version.
    name = package_definition.get("name")

    try:
        package_obj = Package.objects.get(environment=environment, name=name)
    except Package.DoesNotExist:
        package_obj = Package(
            environment=environment,
            name=name,
        )

    package_obj.display_name = package_definition.get("display_name")
    package_obj.summary = package_definition.get("summary")
    package_obj.description = package_definition.get("description")
    package_obj.language = package_definition.get("language")
    package_obj.image_name = image_name

    _create_functions_from_definition(package_definition.get("functions"), package_obj)
    package_obj.save()

    return package_obj


def _create_functions_from_definition(definitions, package: Package):
    """Creates the functions in the package from the definition file"""
    for function_def in definitions:
        name = function_def.get("name")
        try:
            function_obj = Function.objects.get(package=package, name=name)
        except Function.DoesNotExist:
            function_obj = Function(package=package, name=name)

        function_obj.display_name = function_def.get("display_name")
        function_obj.summary = function_def.get("summary")
        function_obj.description = function_def.get("description")
        function_obj.schema = _generate_function_schema(
            name, function_def.get("parameters")
        )
        function_obj.save()


def _generate_function_schema(name: str, parameters) -> str:
    """Creates a pydantic model from the parameter definitions and returns the schema
    as a JSON string"""
    type_map = {
        "integer": int,
        "string": str,
        "text": TypeVar("text", str, bytes),
        "float": float,
        "boolean": bool,
        "date": datetime.date,
        "datetime": datetime.datetime,
        "json": TypeVar("json", Json, str),
    }
    params_dict = {}

    for parameter in parameters:
        field = Field()
        field.alias = parameter.get("name")
        field.title = parameter.get("display_name", field.alias)
        field.description = parameter.get("description")
        field.default = parameter.get("default", ...)
        type_ = type_map[parameter["type"]]

        params_dict[field.alias] = (type_, field)

    model = create_model(name, **params_dict)

    return model.schema()
