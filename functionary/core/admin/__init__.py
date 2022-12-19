from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)

admin.site.login = login_required(admin.site.login)
admin.site.unregister(Group)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(EmailAddress)
