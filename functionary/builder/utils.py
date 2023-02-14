import io
import json
import logging
import os
import shutil
import tarfile
from typing import List
from uuid import UUID

import docker
import yaml
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.template.loader import get_template
from docker.errors import APIError, BuildError, DockerException

from core.models import Environment, Function, FunctionParameter, Package, User

from .celery import app
from .exceptions import InvalidPackage
from .models import Build, BuildLog, BuildResource

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
        package_obj = None

        try:
            package_obj = Package.objects.get(
                environment=environment, name=package_definition.get("name")
            )
        except Package.DoesNotExist:
            pass

        build = Build.objects.create(
            creator=creator, environment=environment, package=package_obj
        )

        BuildResource(
            build=build,
            package_contents=package_contents,
            package_definition=package_definition,
            package_definition_version=package_definition_version,
        ).save()

    build_package.delay(build_id=build.id)

    return build


def _format_build_results(build_results):
    """
    Helper function for build_package to format build results
    as a more readable string

    Args:
        build_results: iterator returned from docker build
    Returns:
        string representation of build log

    """
    log = ""

    for line in build_results:
        line_str = ""

        for value in line.values():
            line_str += str(value)

        log += line_str

    return log


def _format_push_results(push_results):
    """
    Helper function for build_package to format push results
    as a more readable string

    Args:
        push_results: generator object created from docker push
    Returns:
        string representation of the push log
    """
    log = ""

    for line in push_results:
        dict_line = json.loads(line.decode("utf-8"))
        if status := dict_line.get("status"):
            if id := dict_line.get("id"):
                line_str = f"{id}: {status}"
            else:
                line_str = status

            log += line_str + "\n"

    return log


@app.task
def build_package(build_id: UUID):
    """Retrieve the resources for Build and use them to build and push the package
    docker image. Also creates BuildLog with build/push information.

    Args:
        build_id: ID of the build being executed
    """
    docker_client = docker.from_env()

    logger.info(f"Starting build {build_id}")

    workdir = f"{settings.BUILDER_WORKDIR_BASE}/{build_id}"
    os.makedirs(workdir)

    build = Build.objects.select_related("environment").get(id=build_id)
    build.status = Build.IN_PROGRESS
    build.save()

    environment = build.environment
    package = build.package
    package_contents = build.resources.package_contents
    package_definition = build.resources.package_definition
    function_definitions = package_definition.get("functions")

    image_name, dockerfile = build.resources.image_details
    full_image_name = f"{settings.REGISTRY}/{image_name}"

    if not package:
        with transaction.atomic():
            package = _create_package_from_definition(
                package_definition, environment, image_name
            )
            build.package = package
            build.save()

    # Need to validate the potentially new function schema, but
    # don't save it until the build has finished.
    functions, function_parameters = _create_functions_from_definition(
        function_definitions, package
    )
    _extract_package_contents(package_contents, workdir)
    _load_dockerfile_template(dockerfile, workdir)

    try:
        image, build_result = docker_client.images.build(
            path=workdir, pull=True, forcerm=True, tag=full_image_name
        )
        build_log = _format_build_results(build_result)
        build.status = Build.COMPLETE
    except (APIError, BuildError) as exc:
        build_log = (
            _format_build_results(exc.build_log)
            if hasattr(exc, "build_log")
            else str(exc)
        )
        build.status = Build.ERROR

    try:
        push_result = docker_client.images.push(full_image_name, stream=True)
        build_log += "\n" + _format_push_results(push_result)
    except APIError as exc:
        build_log += "\n" + str(exc)
        build.status = Build.ERROR

    with transaction.atomic():
        # Build has succeeded, save all the things now
        if build.status == Build.COMPLETE:
            for func in functions:
                func.save()

            for parameter in function_parameters:
                parameter.save()

            package.image_name = image_name
            package.save()

            _delete_removed_function_parameters(function_parameters, package)
            _deactivate_removed_functions(function_definitions, package)

        BuildLog.objects.create(build=build, log=build_log)
        build.save()

    logger.debug(f"Cleaning up remnants of build {build_id}")
    shutil.rmtree(workdir)

    try:
        docker_client.images.remove(image.id)
    except DockerException:
        logger.warn(f"Unable to remove build image: {image.id}")

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

    package_obj.save()

    return package_obj


def _create_parameters_from_definition(
    function_definition: dict, function: Function
) -> List[FunctionParameter]:
    """Creates the FunctionParameter objects for the provided function based on the
    function_definition"""
    parameters = []
    parameter_defs = function_definition.get("parameters", [])

    for parameter in parameter_defs:
        try:
            function_parameter = FunctionParameter.objects.get(
                function=function, name=parameter.get("name")
            )
        except FunctionParameter.DoesNotExist:
            function_parameter = FunctionParameter(
                function=function, name=parameter.get("name")
            )

        function_parameter.description = parameter.get("description")
        function_parameter.parameter_type = parameter.get("type")
        function_parameter.default = parameter.get("default")
        function_parameter.required = parameter.get("required")

        parameters.append(function_parameter)

    return parameters


def _create_functions_from_definition(definitions: list[dict], package: Package):
    """Creates the functions in the package from the definition file"""
    functions = []
    function_parameters = []

    for function_def in definitions:
        name = function_def.get("name")
        try:
            function_obj = Function.objects.get(package=package, name=name)
        except Function.DoesNotExist:
            function_obj = Function(
                package=package, name=name, environment=package.environment
            )

        function_obj.display_name = function_def.get("display_name")
        function_obj.summary = function_def.get("summary")
        function_obj.return_type = function_def.get("return_type")
        function_obj.description = function_def.get("description")
        function_obj.variables = function_def.get("variables", [])
        function_obj.active = True

        functions.append(function_obj)
        function_parameters.extend(
            _create_parameters_from_definition(function_def, function_obj)
        )

    return functions, function_parameters


def _deactivate_removed_functions(definitions, package: Package):
    """Deactivate and package functions not present in the definitions"""
    function_names = []

    for function_def in definitions:
        function_names.append(function_def.get("name"))

    removed_functions = Function.objects.filter(package=package).exclude(
        name__in=function_names
    )

    for function in removed_functions:
        function.deactivate()


def _delete_removed_function_parameters(
    function_parameters: List[FunctionParameter], package: Package
) -> None:
    """Deletes any FunctionParameters that are not in the provided function_parameters
    for the supplied package
    """
    ids_to_keep = [parameter.id for parameter in function_parameters]

    FunctionParameter.objects.filter(function__package=package).exclude(
        id__in=ids_to_keep
    ).delete()
