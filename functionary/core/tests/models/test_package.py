import pytest

from core.models import Package, Team
from core.models.package import DISABLED, ENABLED


@pytest.fixture
def team():
    return Team.objects.create(name="team")


@pytest.fixture
def environment(team):
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(
        name="testpackage", environment=environment, status=ENABLED
    )


@pytest.fixture
def disabled_package(environment):
    return Package.objects.create(
        name="disabledpackage", environment=environment, status=DISABLED
    )


@pytest.fixture
def default_package(environment):
    return Package.objects.create(name="defaultpackage", environment=environment)


@pytest.mark.django_db
def test_active_packages(package, disabled_package, default_package):
    """This checks filtering of packages with the status of 'DISABLED'"""
    assert package.status != DISABLED
    assert disabled_package.status == DISABLED

    active_packages = Package.active_objects.all()
    assert len(active_packages) == 1
    assert default_package not in active_packages
    assert disabled_package not in active_packages
    assert package in active_packages

    package.disable()
    active_packages = Package.active_objects.all()
    assert len(active_packages) == 0

    all_packages = Package.objects.all()
    assert len(all_packages) == 3
    assert default_package in all_packages
    assert disabled_package in all_packages
    assert package in all_packages
