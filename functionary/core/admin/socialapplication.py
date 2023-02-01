from allauth.socialaccount.models import SocialApp
from constance import config as constance_config
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError


def provider_config_from_constance(provider: str) -> dict:
    """Utility method to retrieve the provider config from Constance.

    Args:
        provider: The provider config to retrieve

    Returns:
        The Constance config for the given provider or an empty dict
    """
    all_providers = constance_config.SOCIALACCOUNT_PROVIDERS
    return all_providers.get(provider, {})


class ConfiguredSocialApp(SocialApp):
    """Proxy class to display the provider config from Constance."""

    class Meta:
        proxy = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = SocialApp.from_db(db, field_names, values)
        instance.provider_config = provider_config_from_constance(instance.provider)
        return instance


class SocialAppForm(forms.ModelForm):
    """Custom form to configure the app and the provider.

    The provider configuration is normally stored in the django settings.
    This form allows editting the provider configuration along with the
    actual SocialApp for authentication.
    """

    provider_config = forms.fields.JSONField(
        required=False,
        help_text="Click <a href='https://django-allauth.readthedocs.io/"
        + "en/latest/providers.html'>here</a> for provider configuration options.",
    )

    class Meta:
        model = ConfiguredSocialApp
        fields = ["name"]

    def get_initial_for_field(self, field, field_name):
        if field_name == "provider_config":
            provider = self.initial.get("provider", None)
            return provider_config_from_constance(provider) if provider else {}

        return super().get_initial_for_field(field, field_name)

    def save(self, commit):
        clean_config = self.cleaned_data.get("provider_config", {})
        all_providers = constance_config.SOCIALACCOUNT_PROVIDERS
        all_providers[self.cleaned_data["provider"]] = clean_config
        setattr(constance_config, "SOCIALACCOUNT_PROVIDERS", all_providers)

        self.cleaned_data["provider_config"] = None
        return super().save(commit)

    def clean_provider(self):
        provider = self.cleaned_data["provider"]
        if not provider:
            raise ValueError("Provider is required")
        elif (
            SocialApp.objects.filter(provider=provider)
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise ValidationError("Provider already configured")
        return provider

    def clean(self):
        data = super().clean()
        provider = data.get("provider", None)
        config = data.get("provider_config", None)

        if provider:
            # The SocialApp page is the main point for changing the Constance
            # config. If the config is empty (user deleted the config), reset
            # it to the Constance setting.
            # If it's an empty dict, leave it unless this is an add - the user
            # probably ignored the setting so grab it from Constance.
            if config is None or (self.instance.id is None and not config):
                data["provider_config"] = provider_config_from_constance(provider)

        return data


class SocialAppAdmin(admin.ModelAdmin):
    form = SocialAppForm
    fields = ["provider", "name", "client_id", "secret", "key", "provider_config"]
    ordering = ["name"]
    list_display = ["name"]
