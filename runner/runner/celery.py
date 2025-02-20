"""Celery Worker App

Instantiates a Celery App that will connect to a Redis instance
to retrieve its internal queue of work to perform.

"""

from logging import getLevelName
from logging.config import dictConfig
from multiprocessing import cpu_count
from os import getenv

from celery import Celery
from celery.apps.worker import Worker
from celery.signals import setup_logging

from .logging_configs import CELERY_LOGGING, LOG_LEVEL

RABBITMQ_HOST = getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = getenv("RABBITMQ_PORT", 5672)
RABBITMQ_USER = getenv("RABBITMQ_USER")
RABBITMQ_PASSWORD = getenv("RABBITMQ_PASSWORD")
RABBITMQ_VHOST = getenv("RUNNER_DEFAULT_VHOST", "public")

WORKER_CONCURRENCY = cpu_count()
WORKER_HOSTNAME = "worker"
WORKER_NAME = f"celery@{WORKER_HOSTNAME}"


app = Celery(
    "runner",
    include=["runner.handlers"],
    broker=(
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}"
        f"@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"
    ),
)


@setup_logging.connect
def config_loggers(*args, **kwargs):
    dictConfig(CELERY_LOGGING)


if __name__ == "__main__":
    worker = Worker(app=app, hostname=WORKER_HOSTNAME)
    worker.setup_defaults(
        concurrency=WORKER_CONCURRENCY, loglevel=getLevelName(LOG_LEVEL)
    )
    worker.start()
