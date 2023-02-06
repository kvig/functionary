ACCOUNT_ADAPTER = "ui.admin.auth.FunctionaryAccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 900
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
USER_MODEL_EMAIL_FIELD = None
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_PREFIX = "constance:functionary:"
CONSTANCE_ADDITIONAL_FIELDS = {"config_field": ["django.forms.fields.JSONField", {}]}
CONSTANCE_CONFIG = {
    "SOCIALACCOUNT_PROVIDERS": (
        {
            "github": {},
            "gitlab": {},
            "keycloak": {},
        },
        "SocialAccount Providers Configuration",
        "config_field",
    ),
}


def constance_settings_proxy(setting_name, default_value):
    """Custom settings function for django-allauth.

    This function will check Constance for the given setting_name and
    revert to the django.conf.settings if it's not found. This function
    allows the SOCIALACCOUNT_PROVIDERS to be configured outside of these
    config files.

    Args:
        setting_name: The name of the setting to fetch
        default_value: The default to use if it's not configured

    Returns:
        The configured setting from Constance. If it's not found, the setting
        from django.conf.settings, otherwise the default_value.
    """
    from constance import config
    from django.conf import settings

    if (value := getattr(config, setting_name, None)) is None:
        value = getattr(settings, setting_name, default_value)
    return value


ALLAUTH_SETTING_GETTER = constance_settings_proxy
