import logging
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings

from core.celery import app
from core.models import Task, TaskLog, TaskResult
from core.utils.messaging import get_route, send_message

logger = get_task_logger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


def _generate_task_message(task: Task) -> dict:
    """Generates tasking message from the provided Task"""
    variables = {var.name: var.value for var in task.variables}
    return {
        "id": str(task.id),
        "package": task.function.package.full_image_name,
        "function": task.function.name,
        "function_parameters": task.parameters,
        "variables": variables,
    }


def _protect_output(task, output):
    """Mask the values of the tasks protected variables in the output.

    Does a simple protection for variable values over 4 characters
    long. This is arbitrary, but the results are easily reversed if
    its too short.
    """
    mask = list(task.variables.filter(protect=True).values_list("value", flat=True))
    protected_output = output
    for to_mask in mask:
        if len(to_mask) > 4:
            protected_output = protected_output.replace(to_mask, "********")

    return protected_output


@app.task(
    default_retry_delay=30,
    retry_kwargs={
        "max_retries": 3,
    },
    autoretry_for=(Exception,),
)
def publish_task(task_id: UUID) -> None:
    """Publish the tasking message to the message broker so that it can be received
    and executed by a runner.

    Args:
        task_id: ID of the task to be executed
    """
    logger.debug(f"Publishing message for Task: {task_id}")

    task = Task.objects.select_related(
        "function", "function__package", "environment"
    ).get(id=task_id)

    exchange, routing_key = get_route(task)
    send_message(exchange, routing_key, "TASK_PACKAGE", _generate_task_message(task))


@app.task()
def record_task_result(task_result_message: dict) -> None:
    """Parses the task result message and generates a TaskResult entry for it

    Args:
        task_result_message: The message body from a TASK_RESULT message.
    """
    task_id = task_result_message["task_id"]
    status = task_result_message["status"]
    output = task_result_message["output"]
    result = task_result_message["result"]

    try:
        task = Task.objects.select_related("function", "environment").get(id=task_id)
    except Task.DoesNotExist:
        logger.error("Unable to record results for task %s: task not found", task_id)
        return

    TaskLog.objects.create(task=task, log=_protect_output(task, output))
    TaskResult.objects.create(task=task, result=result)

    # TODO: This status determination feels like it belongs in the runner. This should
    #       be reworked so that there are explicitly known statuses that could come
    #       back from the runner, rather than passing through the command exit status
    #       as is happening now.
    task.status = "COMPLETE" if status == 0 else "ERROR"
    task.save()
