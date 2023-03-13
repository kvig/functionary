from allauth.socialaccount import signals
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRefresh
from rest_framework.authtoken.models import Token


@login_required
@require_GET
def details(request):
    account_data = []
    for account in SocialAccount.objects.filter(user=request.user):
        provider_account = account.get_provider_account()
        account_data.append(
            {
                "id": account.pk,
                "provider": account.provider,
                "name": provider_account.to_str(),
                "username": account.extra_data.get("username", None),
            }
        )

    token, _ = Token.objects.get_or_create(user=request.user)
    context = {"socialaccounts": account_data, "token": token}

    return render(request, "account/details.html", context)


@login_required
@require_POST
def disconnect_social(request):
    accounts = SocialAccount.objects.filter(user=request.user)
    account = accounts.filter(id=request.POST["account"])
    if account:
        account.delete()
        signals.social_account_removed.send(
            sender=SocialAccount, request=request, socialaccount=account
        )

    return HttpResponseClientRefresh()


@login_required
@require_POST
def refresh_token(request):
    if token := Token.objects.get(user=request.user):
        token.delete()
    new_token = Token.objects.create(user=request.user)
    context = {"token": new_token}

    return render(request, "partials/token.html", context)
