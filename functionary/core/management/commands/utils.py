import logging
from time import sleep
from typing import Callable

from django.conf import settings
from django.db.utils import DatabaseError

LOG_LEVEL = settings.LOG_LEVEL
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL))

SLEEP_DURATION = 5


def run(command: Callable) -> None:
    """Run the given the command

    The given command will be executed to see if the necessary
    database migrations have been run. If the migrations have not
    been run, the command will be re-run after a delay.

    Args:
        command: The callable command to execute

    Returns:
        None
    """
    is_ready = False
    while not is_ready:
        try:
            command()
            is_ready = True
        except DatabaseError:
            logger.error(
                f"Database is not ready. "
                f"Ensure database is available and migrations have been run. "
                f"Retrying command in {SLEEP_DURATION} seconds."
            )
            sleep(SLEEP_DURATION)
