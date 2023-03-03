import pprint

from allauth.socialaccount.models import SocialAccount
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.sessions.models import Session
from rest_framework.authtoken.models import Token

from core.admin.environment import EnvironmentAdmin
from core.admin.settings import FunctionarySettings, SettingsAdmin
from core.admin.socialapplication import ConfiguredSocialApp, SocialAppAdmin
from core.admin.team import TeamAdmin
from core.admin.user import UserAdmin
from core.models import Environment, Team, User


class UIAdminSite(AdminSite):
    site_header = "Functionary Administration"
    site_title = "Functionary Admin"
    site_url = "/ui"


class SessionAdmin(ModelAdmin):
    """Custom Admin for the Session Model that decodes the session data."""

    def _session_data(self, obj):
        return pprint.pformat(obj.get_decoded())

    _session_data.allow_tags = True
    list_display = ["session_key", "_session_data", "expire_date"]
    readonly_fields = ["_session_data"]
    exclude = ["session_data"]


ui_admin_site = UIAdminSite(name="ui_admin")

ui_admin_site.register(Token)
ui_admin_site.register(Session, SessionAdmin)
ui_admin_site.register(Environment, EnvironmentAdmin)
ui_admin_site.register(Team, TeamAdmin)
ui_admin_site.register(User, UserAdmin)
ui_admin_site.register(SocialAccount)
ui_admin_site.register(ConfiguredSocialApp, SocialAppAdmin)
ui_admin_site.register([FunctionarySettings], SettingsAdmin)
