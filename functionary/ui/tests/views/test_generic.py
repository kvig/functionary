"""Tests the custom generic views.

NOTE: The tests contained here use the workflow views to exercise various aspects
of the generic view functionality. This is done strictly out of convenience since
those views build on the generic views that need to be tested. It would be preferable
to build these tests off of independent views constructed specifically for test
purposes, but in the absense of an independent django test app this method was chosen
instead.
"""
from uuid import uuid4

import pytest
from django.urls import reverse

from core.auth import Role
from core.models import (
    EnvironmentUserRole,
    Function,
    Package,
    Team,
    User,
    Workflow,
    WorkflowStep,
)
from core.utils.parameter import PARAMETER_TYPE


@pytest.fixture
def environment():
    team = Team.objects.create(name="team")
    return team.environments.get()


@pytest.fixture
def inactive_environment():
    team = Team.objects.create(name="otherteam")
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
def user_with_read_access(environment, inactive_environment):
    user_obj = User.objects.create(username="readaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.READ_ONLY.name, environment=environment
    )
    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.READ_ONLY.name, environment=inactive_environment
    )

    return user_obj


@pytest.fixture
def user_with_edit_access(environment, inactive_environment):
    user_obj = User.objects.create(username="editaccess")

    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.ADMIN.name, environment=environment
    )
    EnvironmentUserRole.objects.create(
        user=user_obj, role=Role.ADMIN.name, environment=inactive_environment
    )

    return user_obj


@pytest.fixture
def user_without_access():
    return User.objects.create(username="noaccess")


@pytest.fixture
def workflow(environment, user_with_edit_access):
    return Workflow.objects.create(
        environment=environment, name="testworkflow", creator=user_with_edit_access
    )


@pytest.fixture
def workflow_for_inactive_environment(inactive_environment, user_with_edit_access):
    return Workflow.objects.create(
        environment=inactive_environment,
        name="testworkflow",
        creator=user_with_edit_access,
    )


@pytest.fixture
def workflow_step(workflow, function):
    return WorkflowStep.objects.create(
        workflow=workflow,
        name="teststep",
        function=function,
        parameter_template='{"prop1": 42}',
    )


@pytest.mark.django_db
def test_list_view_filters_by_active_environment(
    client, workflow, workflow_for_inactive_environment, user_with_read_access
):
    """The results returned by PermissionedListView should only include entries for
    the active environment
    """
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-list")
    response = client.get(url)
    response_body = response.content.decode()

    assert response.status_code == 200
    assert str(workflow.id) in response_body
    assert str(workflow_for_inactive_environment.id) not in response_body


@pytest.mark.django_db
def test_list_returns_403_for_no_access(client, workflow, user_without_access):
    """PermissionedListView returns 403 for a user lacking access to the environment"""
    client.force_login(user_without_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-list")
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_detail_view_filters_by_active_environment(
    client, workflow, workflow_for_inactive_environment, user_with_read_access
):
    """PermissionedDetailView should show objects only for the active environment,
    even if the user has permission.
    """
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    active_environment_url = reverse("ui:workflow-detail", kwargs={"pk": workflow.pk})
    response = client.get(active_environment_url)

    assert response.status_code == 200

    inactive_environment_url = reverse(
        "ui:workflow-detail", kwargs={"pk": workflow_for_inactive_environment.pk}
    )
    response = client.get(inactive_environment_url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_create_view_allows_post_with_access(
    client, environment, user_with_edit_access
):
    """PermissionedCreateView allows POST for a user with access"""
    client.force_login(user_with_edit_access)

    session = client.session
    session["environment_id"] = str(environment.id)
    session.save()

    url = reverse("ui:workflow-create")
    response = client.post(
        url, {"name": "new_workflow", "environment": str(environment.id)}
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_create_view_returns_403_for_post_without_access(
    client, environment, user_with_read_access
):
    """PermissionedCreateView allows POST for a user with access"""
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(environment.id)
    session.save()

    url = reverse("ui:workflow-create")
    response = client.post(
        url, {"name": "new_workflow", "environment": str(environment.id)}
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_view_allows_post_with_access(client, workflow, user_with_edit_access):
    """PermissionedUpdateView allows POST for a user with access"""
    client.force_login(user_with_edit_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-update", kwargs={"pk": workflow.pk})
    response = client.post(url, {"name": "new_name"})

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_view_returns_403_for_post_without_access(
    client, workflow, user_with_read_access
):
    """PermissionedUpdateView allows POST for a user with access"""
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-update", kwargs={"pk": workflow.pk})
    response = client.post(url, {"name": "new_name"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_view_allows_post_with_access(client, workflow, user_with_edit_access):
    """PermissionedDeleteView allows POST for a user with access"""
    client.force_login(user_with_edit_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-delete", kwargs={"pk": workflow.pk})
    response = client.post(url)

    # 302 expected for redirect to "success_url"
    assert response.status_code == 302


@pytest.mark.django_db
def test_delete_view_returns_403_for_post_without_access(
    client, workflow, user_with_read_access
):
    """PermissionedDeleteView allows POST for a user with access"""
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    url = reverse("ui:workflow-delete", kwargs={"pk": workflow.pk})
    response = client.post(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_nested_route_filters_by_parent_object(
    client,
    workflow,
    workflow_step,
    user_with_read_access,
):
    """Nested routes identify the parent object and use it in the queryset filtering"""
    client.force_login(user_with_read_access)

    session = client.session
    session["environment_id"] = str(workflow.environment.id)
    session.save()

    valid_workflow_url = reverse(
        "ui:workflowstep-edit",
        kwargs={"workflow_pk": workflow.pk, "pk": workflow_step.pk},
    )
    response = client.get(valid_workflow_url)

    assert response.status_code == 200

    # Same object, but accessed via the wrong / invalid parent route
    invalid_workflow_url = reverse(
        "ui:workflowstep-edit",
        kwargs={"workflow_pk": uuid4(), "pk": workflow_step.pk},
    )
    response = client.get(invalid_workflow_url)

    assert response.status_code == 404
