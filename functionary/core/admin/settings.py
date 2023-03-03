from constance import admin as constance_admin
from constance.admin import Config as ConstanceConfig


class FunctionarySettings(ConstanceConfig):
    """Proxy class to display other config settings from Constance."""

    class Meta(ConstanceConfig.Meta):
        proxy = True
        app_label = "core"
        object_name = "Settings"
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    _meta = Meta()


class SettingsAdmin(constance_admin.ConstanceAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        model._meta.concrete_model = FunctionarySettings
