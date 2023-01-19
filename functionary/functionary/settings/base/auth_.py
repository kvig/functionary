import json

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
        '{"facebook":{"SCOPE":["public_profile"]},"github":{"SCOPE":["user","repo","read:org"]},"gitlab":{"GITLAB_URL":"https://gitlab.com"}}',
        "SocialAccount Providers Configuration",
        "config_field",
    ),
}


def setting_getter(setting_name: str, default_value):
    from constance import config
    from django.conf import settings

    val = getattr(config, setting_name, None)
    try:
        val = json.loads(val)
    except Exception:
        pass
    if not val:
        val = getattr(settings, setting_name, default_value)

    return val


ALLAUTH_SETTING_GETTER = setting_getter
