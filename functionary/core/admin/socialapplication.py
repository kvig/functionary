import json

from allauth.socialaccount.models import SocialApp
from constance import config as constance_config
from django import forms
from django.contrib import admin


class ConfiguredSocialApp(SocialApp):
    class Meta:
        proxy = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = SocialApp.from_db(db, field_names, values)
        providers = json.loads(constance_config.SOCIALACCOUNT_PROVIDERS)
        instance.provider_config = providers.get(instance.provider)
        return instance


class SocialAppForm(forms.ModelForm):
    """Custom form to show the environments associated with the team"""

    provider_config = forms.fields.JSONField()

    class Meta:
        model = ConfiguredSocialApp
        fields = ["name"]

    def get_initial_for_field(self, field, field_name):
        if field_name == "provider_config" and "provider" in self.initial:
            return json.loads(constance_config.SOCIALACCOUNT_PROVIDERS).get(
                self.initial["provider"], None
            )

        return super().get_initial_for_field(field, field_name)

    def save(self, commit=True):
        providers = self.cleaned_data["provider_config"]
        all_providers = json.loads(constance_config.SOCIALACCOUNT_PROVIDERS)
        all_providers[self.cleaned_data["provider"]] = providers
        setattr(constance_config, "SOCIALACCOUNT_PROVIDERS", json.dumps(all_providers))

        self.cleaned_data["provider_config"] = None
        return super().save(commit)


class SocialAppAdmin(admin.ModelAdmin):
    form = SocialAppForm
    fields = ["provider", "name", "client_id", "secret", "key", "provider_config"]
    ordering = ["name"]
    list_display = ["name"]
