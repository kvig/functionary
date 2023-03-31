import pytest
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from core.models import Function, Package, ScheduledTask, Task, Team, User
from core.models.package import PACKAGE_STATUS


@pytest.fixture
def user():
    return User.objects.create(username="user")


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(
        name="testpackage", environment=environment, status=PACKAGE_STATUS.ACTIVE
    )


@pytest.fixture
def disabled_package(environment):
    return Package.objects.create(
        name="disabledpackage", environment=environment, status=PACKAGE_STATUS.DISABLED
    )


@pytest.fixture
def default_package(environment):
    return Package.objects.create(name="defaultpackage", environment=environment)


@pytest.fixture
def function(package):
    return Function.objects.create(
        name="testfunction",
        environment=package.environment,
        package=package,
        active=True,
    )


@pytest.fixture
def task(function, environment, user):
    return Task.objects.create(
        function=function,
        environment=environment,
        parameters={"prop1": "value1"},
        creator=user,
    )


@pytest.fixture
def periodic_task():
    return PeriodicTask.objects.create(
        name="periodicTemp",
        task="task1",
        crontab=CrontabSchedule.objects.create(hour=7, minute=30, day_of_week=1),
    )


@pytest.fixture
def scheduled_task(function, environment, user, periodic_task):
    return ScheduledTask.objects.create(
        name="testtask",
        description="description",
        creator=user,
        function=function,
        environment=environment,
        parameters={"name": "input", "summary": "summary", "type": "text"},
        periodic_task=periodic_task,
        status=ScheduledTask.ACTIVE,
    )


@pytest.mark.django_db
def test_active_packages(package, disabled_package, default_package):
    """This checks filtering of inactive packages"""
    assert package.is_active
    assert not disabled_package.is_active

    active_packages = Package.active_objects.all()
    assert len(active_packages) == 1
    assert default_package not in active_packages
    assert disabled_package not in active_packages
    assert package in active_packages

    package.deactivate()
    active_packages = Package.active_objects.all()
    assert len(active_packages) == 0

    all_packages = Package.objects.all()
    assert len(all_packages) == 3
    assert default_package in all_packages
    assert disabled_package in all_packages
    assert package in all_packages


@pytest.mark.django_db
@pytest.mark.usefixtures("scheduled_task")
def test_deactivate_package_pauses_schedules(package, function):
    """This marks the package to inactive and causes scheduled tasks to pause"""
    assert function.is_active is True
    assert function.scheduled_tasks.filter(status=ScheduledTask.ACTIVE).exists()

    package.deactivate()
    assert function.active is True
    assert function.is_active is False
    assert package.is_active is False

    for scheduled_t in function.scheduled_tasks.all():
        assert scheduled_t.status == ScheduledTask.PAUSED
