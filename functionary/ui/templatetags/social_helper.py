from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def find_account(context, provider_id):
    if "form" in context:
        for account in context["form"].accounts:
            if account.provider == provider_id:
                return account.get_provider_account().account
    return None
