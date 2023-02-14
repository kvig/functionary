import logging
from uuid import UUID

from celery.utils.log import get_task_logger
from django.conf import settings

from core.celery import app
from core.models import (
    Environment,
    ScheduledTask,
    Task,
    TaskLog,
    TaskResult,
    WorkflowRunStep,
)
from core.utils.messaging import get_route, send_message
from core.utils.minio import MinioInterface, generate_filename
from core.utils.parameter import PARAMETER_TYPE

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

    _handle_file_parameters(task)

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
    _update_task_status(task, status)

    # If this task is part of a WorkflowRun continue it or update its status
    if workflow_run_step := WorkflowRunStep.objects.filter(task=task):
        _handle_workflow_run(workflow_run_step.get(), task)


@app.task
def run_scheduled_task(scheduled_task_id: str) -> None:
    """Creates and executes a Task according to a schedule

    Uses the given ScheduledTask object id as a string to fetch the ScheduledTask.
    The necessary metadata is taken from the ScheduledTask object to construct
    a new Task. The new Task is then associated with that ScheduledTask. The
    ScheduledTask metadata is then updated with the newly created Task.

    Args:
        scheduled_task_id: A string of the ID for the ScheduledTask object

    Returns:
        None
    """
    scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)

    task = Task.objects.create(
        environment=scheduled_task.environment,
        creator=scheduled_task.creator,
        function=scheduled_task.function,
        return_type=scheduled_task.function.return_type,
        parameters=scheduled_task.parameters,
        scheduled_task=scheduled_task,
    )

    scheduled_task.update_most_recent_task(task)


def _update_task_status(task: Task, status: int) -> None:
    match status:
        case 0:
            task.status = Task.COMPLETE
        case _:
            task.status = Task.ERROR

    task.save()

    if task.scheduled_task is not None and status == "ERROR":
        task.scheduled_task.error()


def _handle_workflow_run(workflow_run_step: WorkflowRunStep, task: Task) -> None:
    """Start the next task for a WorkflowRun or update its status as appropriate"""
    workflow_run = workflow_run_step.workflow_run

    match task.status:
        case Task.COMPLETE:
            if next_step := workflow_run_step.workflow_step.next:
                next_step.execute(workflow_run=workflow_run)
            else:
                workflow_run.complete()
        case Task.ERROR:
            workflow_run.error()


def _handle_file_parameters(task: Task) -> None:
    """Update all file parameter's filenames to presigned URLs

    This function will mutate all file parameters to their
    corresponding presigned URLs. This should only be done
    before a task is sent to the runner. The task should not
    save the presigned URL to its database entry.

    Arguments:
        task: The task that is about to be sent to the runner

    Returns:
        None
    """
    environment = task.environment
    parameters = task.parameters

    for parameter in task.function.parameters.filter(
        parameter_type=PARAMETER_TYPE.FILE, name__in=parameters.keys()
    ):
        param_name = parameter.name

        filename = generate_filename(task, param_name, parameters[param_name])
        parameters[param_name] = _get_presigned_url(filename, environment)


def _get_presigned_url(filename: str, environment: Environment) -> str:
    minio = MinioInterface(bucket_name=str(environment.id))
    presigned_url = minio.get_presigned_url(filename)
    return presigned_url
