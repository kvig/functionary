import itertools
import json
import logging

import docker

from .celery import app
from .messaging import send_message

OUTPUT_SEPARATOR = b"==== Output From Command ====\n"

logger = logging.getLogger(__name__)


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(docker.errors.DockerException,),
)
def pull_image(task) -> None:
    package = task.get("package")

    docker_client = docker.from_env()
    docker_client.images.pull(package)

    logger.debug(f"Pulled {package}")


@app.task()
def run_task(_=None, task=None):
    exit_status, output, result = _run_task(task)

    return {
        "task_id": task["id"],
        "status": exit_status,
        "output": output.decode(),
        "result": result.decode(),
    }


def _run_task(task):
    package = task.get("package")
    function = task.get("function")
    parameters = json.dumps(task["function_parameters"])
    variables = task.get("variables")
    run_command = ["--function", function, "--parameters", parameters]

    logging.info("Running %s from package %s", function, package)
    docker_client = docker.from_env()
    container = docker_client.containers.run(
        package,
        auto_remove=False,
        detach=True,
        command=run_command,
        environment=variables,
    )

    exit_status = container.wait()["StatusCode"]
    output, result = _parse_container_logs(container.logs(stream=True))

    container.remove()

    return (exit_status, output, result)


def _parse_container_logs(logs):
    output = b"".join(
        itertools.takewhile(lambda x: x != OUTPUT_SEPARATOR, logs)
    ).rstrip()
    result = b"".join(logs).rstrip()

    return output, result


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_result(result):
    # TODO: The routing key should come from the configuration information received
    #       during runner registration.
    send_message("tasking.results", "TASK_RESULT", result)
