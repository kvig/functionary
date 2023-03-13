from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.base import Provider, ProviderAccount
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def find_account(context, provider_id: str) -> ProviderAccount | None:
    """This tag checks the SocialAccounts in the templates
    context and returns the desired ProviderAccount.

    Args:
        context: the template's context, automatically passed in
        provider_id: ID of the SocialAccount to find

    Returns:
        The matching ProviderAccount or None
    """
    for account in context.get("socialaccounts", None):
        if account["provider"] == provider_id:
            return account

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


@register.simple_tag(takes_context=True)
def unwrap_exception(context) -> dict[str, str | None]:
    """This tag attempts to unwrap the exception stored in auth_error.
    It will recurse until it finds a populated 'strerror' value.
    """
    exc = context.get("auth_error", {}).get("exception", None)

    try:
        while exc:
            # Ultimately verify_message or strerror is the informative value to display.
            # Check if args is populated when reason isnt, it's the desired exception
            # to unwind. Otherwise check if reason is populated.
            if hasattr(exc, "strerror") and exc.strerror:
                return {
                    "reason": exc.reason,
                    "message": exc.verify_message or exc.strerror,
                }
            elif not hasattr(exc, "reason") and hasattr(exc, "args"):
                exc = exc.args[0]
            elif hasattr(exc, "reason"):
                exc = exc.reason
            else:
                break
    except Exception:
        pass

    return {"reason": "Unknown", "message": None}
