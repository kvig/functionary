from .constance_ import constance_settings_proxy

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

ALLAUTH_SETTING_GETTER = constance_settings_proxy
