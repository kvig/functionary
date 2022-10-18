UNICORN = {
    "APPS": ["ui"],
    "RELOAD_SCRIPT_ELEMENTS": True,
}
LOGIN_URL = "/ui/login"
LOGOUT_URL = "/ui/logout"
LOGIN_REDIRECT_URL = "ui:home"
LOGOUT_REDIRECT_URL = "ui:login"
