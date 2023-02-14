import logging

from celery.apps.beat import Beat
from django.conf import settings
from django.core.management.base import BaseCommand
from django_celery_beat import schedulers

from core.celery import app
from core.management.commands.utils import run
from core.utils.messaging import initialize_messaging, wait_for_connection

LOG_LEVEL = settings.LOG_LEVEL
logger = logging.getLogger("celery.beat")
logger.setLevel(getattr(logging, LOG_LEVEL))


CHECK_FOR_CHANGES_INTERVAL_SECONDS = 5


class Command(BaseCommand):
    help = "Run the scheduler"

    def handle(self, *args, **options):
        wait_for_connection()
        initialize_messaging()

        scheduler = Beat(
            app=app,
            max_interval=CHECK_FOR_CHANGES_INTERVAL_SECONDS,
            scheduler=schedulers.DatabaseScheduler,
            loglevel=LOG_LEVEL,
        )

        run(scheduler.run)
