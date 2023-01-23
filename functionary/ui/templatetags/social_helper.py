from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.base import Provider, ProviderAccount
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def find_account(context, provider_id: str) -> ProviderAccount | None:
    """This tag checks the SocialAccounts in the form found in the
    templates context and returns the desired ProviderAccount.

    Args:
        context: the template's context, automatically passed in
        provider_id: ID of the SocialAccount to find

    Returns:
        The matching ProviderAccount or None
    """
    if form := context.get("form"):
        for account in form.accounts:
            if account.provider == provider_id:
                return account.get_provider_account().account
    return None


@register.simple_tag()
def configured_providers() -> list[dict[str, Provider]]:
    """This tag returns a list of tuples of the configured Providers.

    Returns:
        List of tuples of configured provider name and Provider
    """
    provider_pairs = []
    for app in SocialApp.objects.all():
        provider_pairs.append(
            {"name": app.name, "provider": providers.registry.by_id(app.provider)}
        )
    return provider_pairs
