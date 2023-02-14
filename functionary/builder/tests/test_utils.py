import pytest

from builder import utils
from core.models import Function, Package, Team, User
from core.utils.parameter import PARAMETER_TYPE


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
def package1(environment):
    return Package.objects.create(name="testpackage1", environment=environment)


@pytest.fixture
def package2(environment):
    return Package.objects.create(name="testpackage2", environment=environment)


@pytest.fixture
def function1(package1):
    function = Function.objects.create(
        name="function1",
        environment=package1.environment,
        package=package1,
        active=True,
    )

    function.parameters.create(name="param1", parameter_type=PARAMETER_TYPE.INTEGER)
    function.parameters.create(name="param2", parameter_type=PARAMETER_TYPE.INTEGER)

    return function


@pytest.fixture
def function2(package1):
    return Function.objects.create(
        name="function2",
        environment=package1.environment,
        package=package1,
        active=True,
    )


@pytest.fixture
def function3(package2):
    return Function.objects.create(
        name="function3",
        environment=package2.environment,
        package=package2,
        active=True,
    )


@pytest.fixture
def function4(package2):
    return Function.objects.create(
        name="function4",
        environment=package2.environment,
        package=package2,
        active=True,
    )


@pytest.fixture
def package1_definitions_without_function2(function1):
    function1_def = {
        "name": function1.name,
        "summary": function1.summary,
        "parameters": [],
        "description": "description",
        "display_name": function1.name,
    }

    return [function1_def]


@pytest.mark.django_db
@pytest.mark.usefixtures("function1", "function2", "function3", "function4")
def test_deactivate_removed_functions(
    package1_definitions_without_function2, package1, package2
):
    db_functions = Function.objects.all()
    for function in db_functions:
        assert function.active is True

    utils._deactivate_removed_functions(
        package1_definitions_without_function2, package1
    )

    # package2 functions should still all be active
    assert package2.functions.count() == package2.active_functions.count()

    # package1 function1 should be active, function2 inactive
    assert package1.functions.get(name="function1").active is True
    assert package1.functions.get(name="function2").active is False


@pytest.mark.django_db
def test_delete_removed_function_parameters(function1):
    assert function1.parameters.count() == 2

    parameters_to_keep = function1.parameters.get(name="param1")

    utils._delete_removed_function_parameters([parameters_to_keep], function1.package)

    assert function1.parameters.count() == 1
    assert function1.parameters.filter(name="param1").exists()
