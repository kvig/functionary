import pytest

from core.models import Function, Package, Team
from core.utils.parameter import PARAMETER_TYPE
from ui.forms.tasks import TaskParameterTemplateForm


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def package(environment):
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="int_param", parameter_type=PARAMETER_TYPE.INTEGER)
    _function.parameters.create(name="json_param", parameter_type=PARAMETER_TYPE.JSON)

    return _function


@pytest.mark.django_db
def test_taskparametertemplateform_can_load_initial_values(function):
    form = TaskParameterTemplateForm(
        function=function,
        initial='{"int_param": {{var1}}, "json_param": {{var2}}}',
    )

    assert form.fields["int_param"].initial == "{{var1}}"
    assert form.fields["json_param"].initial == "{{var2}}"
