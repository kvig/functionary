from typing import Union

from django_celery_beat.models import CrontabSchedule
from django_celery_beat.validators import (
    crontab_validator,
    day_of_month_validator,
    day_of_week_validator,
    hour_validator,
    minute_validator,
    month_of_year_validator,
)


def get_or_create_crontab_schedule(
    minute: Union[int, str],
    hour: Union[int, str],
    day_of_month: Union[int, str],
    month_of_year: Union[int, str],
    day_of_week: Union[int, str],
) -> CrontabSchedule:
    """Get or create a CrontabSchedule

    If the submitted crontab schedule already exists, returns
    the existing crontab schedule. Otherwise, creates and
    returns a new crontab schedule.

    Args:
        minute: int or valid crontab str representing minute
        hour: int or valid crontab str representing hour
        day_of_month: int or valid crontab str representing the day of the month
        month_of_year: int or valid crontab str representing the month of the year
        day_of_week: int or valid crontab str representing the day of the week

    Returns:
        CronTabSchedule: The new, or existing, crontab schedule

    Raises:
        ValueError: One of the provided values was not valid crontab syntax
    """
    crontab_str = f"{minute} {hour} {day_of_month} {month_of_year} {day_of_week}"

    crontab_validator(crontab_str)
    crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )

    return crontab_schedule


def is_valid_scheduled_minute(value: str) -> bool:
    try:
        minute_validator(value)
        return True
    except Exception:
        return False


def is_valid_scheduled_hour(value: str) -> bool:
    try:
        hour_validator(value)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_month(value: str) -> bool:
    try:
        day_of_month_validator(value)
        return True
    except Exception:
        return False


def is_valid_scheduled_month_of_year(value: str) -> bool:
    try:
        month_of_year_validator(value)
        return True
    except Exception:
        return False


def is_valid_scheduled_day_of_week(value: str) -> bool:
    try:
        day_of_week_validator(value)
        return True
    except Exception:
        return False
