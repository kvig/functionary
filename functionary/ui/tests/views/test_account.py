import re

import pytest
from django.urls import reverse

from core.models import User


def _get_token(response):
    content = str(response.content)
    token = re.match(r'^.*data-token="(?P<token>[a-z0-9]+)">\1<.*$', content)
    return token.group("token") if token else None


@pytest.fixture
def user():
    user_obj = User.objects.create(username="logged_in_user")

    return user_obj


@pytest.mark.django_db
def test_token_and_refresh(client, user):
    client.force_login(user)

    detail_url = reverse("ui:account-detail")
    response = client.get(detail_url)
    old_token = _get_token(response)

    assert old_token is not None

    refresh_url = reverse("ui:token-refresh")
    response = client.post(refresh_url)
    new_token = _get_token(response)

    assert new_token is not None
    assert old_token != new_token
