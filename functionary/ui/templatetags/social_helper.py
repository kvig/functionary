from allauth.socialaccount.providers.base import ProviderAccount
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
    if "form" in context:
        for account in context["form"].accounts:
            if account.provider == provider_id:
                return account.get_provider_account().account
    return None
