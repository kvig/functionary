import pytest

from core.models import Function, Package, Team, User, Workflow, WorkflowStep
from core.utils.parameter import PARAMETER_TYPE
from core.utils.workflow import add_step, move_step, remove_step


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
    return Package.objects.create(name="testpackage", environment=environment)


@pytest.fixture
def function(package):
    _function = Function.objects.create(
        name="testfunction",
        package=package,
        environment=package.environment,
    )

    _function.parameters.create(name="prop1", parameter_type=PARAMETER_TYPE.INTEGER)

    return _function


@pytest.fixture
def workflow(function, environment, user):
    workflow_ = Workflow.objects.create(
        environment=environment, name="workflow", creator=user
    )

    last = WorkflowStep.objects.create(
        workflow=workflow_,
        name="last",
        function=function,
        parameter_template='{"prop1": 3}',
        next=None,
    )

    middle = WorkflowStep.objects.create(
        workflow=workflow_,
        name="middle",
        function=function,
        parameter_template='{"prop1": 2}',
        next=last,
    )

    _ = WorkflowStep.objects.create(
        workflow=workflow_,
        name="first",
        function=function,
        parameter_template='{"prop1": 1}',
        next=middle,
    )

    return workflow_


@pytest.fixture
def other_workflow(function, environment, user):
    other_workflow_ = Workflow.objects.create(
        environment=environment, name="other_workflow", creator=user
    )

    _ = WorkflowStep.objects.create(
        workflow=other_workflow_,
        name="first",
        function=function,
        parameter_template='{"prop1": 99}',
        next=None,
    )

    return other_workflow_


@pytest.mark.django_db
def test_add_step_at_end(workflow, function):
    """Steps can be added to the end of the workflow"""
    new_last = add_step(
        workflow=workflow,
        name="new_last",
        function=function,
        parameter_template='{"prop1": 12}',
    )

    assert workflow.steps.count() == 4
    assert workflow.steps.get(name="new_last").next is None
    assert workflow.steps.get(name="last").next == new_last


@pytest.mark.django_db
def test_add_step_in_middle(workflow, function):
    """Steps can be added to the middle of the workflow"""
    second = add_step(
        workflow=workflow,
        name="second",
        function=function,
        parameter_template='{"prop1": 12}',
        next=workflow.steps.get(name="middle"),
    )

    assert workflow.steps.count() == 4
    assert workflow.steps.get(name="first").next == second


@pytest.mark.django_db
def test_add_step_workflow_must_match_next(workflow, other_workflow, function):
    """Workflow for next step must match workflow value"""
    with pytest.raises(ValueError):
        _ = add_step(
            workflow=workflow,
            name="new_step",
            function=function,
            parameter_template='{"prop1": 99}',
            next=other_workflow.steps.get(name="first"),
        )


@pytest.mark.django_db
def test_remove_step(workflow):
    """Steps can be removed from the workflow"""
    remove_step(workflow.steps.get(name="middle"))

    first = workflow.steps.get(name="first")
    last = workflow.steps.get(name="last")

    assert workflow.steps.count() == 2
    assert first.next == last


@pytest.mark.django_db
def test_move_step(workflow):
    """Steps can be moved to another point in the Workflow"""
    first = workflow.steps.get(name="first")
    middle = workflow.steps.get(name="middle")
    last = workflow.steps.get(name="last")

    move_step(last, first)

    first.refresh_from_db()
    middle.refresh_from_db()
    last.refresh_from_db()

    move_step(first, None)

    # New order should be last, middle, first
    ordered_steps = workflow.ordered_steps
    assert ordered_steps[0] == last
    assert ordered_steps[1] == middle
    assert ordered_steps[2] == first


@pytest.mark.django_db
def test_move_step_only_within_same_workflow(workflow, other_workflow):
    """The step to move and its new next target must be in the same Workflow"""
    with pytest.raises(ValueError):
        move_step(
            workflow.steps.get(name="first"), other_workflow.steps.get(name="first")
        )
