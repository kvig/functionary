from django.contrib import admin
from django.contrib.auth.models import Group

from core.models import (
    Environment,
    EnvironmentUserRole,
    EnvironmentVariable,
    Function,
    Package,
    Task,
    TaskLog,
    TaskResult,
    Team,
    TeamUserRole,
    User,
)

from .user import UserAdmin

admin.site.register(Environment, admin.ModelAdmin)
admin.site.register(EnvironmentUserRole, admin.ModelAdmin)
admin.site.register(EnvironmentVariable, admin.ModelAdmin)
admin.site.register(Function, admin.ModelAdmin)
admin.site.register(Package, admin.ModelAdmin)
admin.site.register(Task, admin.ModelAdmin)
admin.site.register(TaskLog, admin.ModelAdmin)
admin.site.register(TaskResult, admin.ModelAdmin)
admin.site.register(Team, admin.ModelAdmin)
admin.site.register(TeamUserRole, admin.ModelAdmin)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
