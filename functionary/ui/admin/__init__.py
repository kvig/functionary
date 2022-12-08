from django.contrib import admin

from core.admin.environment import EnvironmentAdmin
from core.admin.team import TeamAdmin
from core.admin.user import UserAdmin
from core.models import Environment, Team, User

admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(User, UserAdmin)

admin.site.site_header = "Functionary Administration"
admin.site.site_title = "Functionary Admin"
admin.site.site_url = "/ui"
