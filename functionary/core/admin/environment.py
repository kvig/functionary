from django import forms
from django.contrib import admin

from core.models import Environment, EnvironmentUserRole


class UserRoleInline(admin.TabularInline):
    """Inline form to add users to the Environment"""

    model = EnvironmentUserRole
    extra = 0
    verbose_name = "User"

    def has_change_permission(self, request, obj):
        return False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        # By default, Django wraps the widget to allow you to create these
        # objects inline with the form. Unwrap the widget since this is not
        # what we want.
        if db_field.attname == "user_id":
            field.widget = field.widget.widget
        return field


class EnvironmentForm(forms.ModelForm):
    """Custom form to show the environments associated with the team"""

    class Meta:
        model = Environment
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(EnvironmentForm, self).__init__(*args, **kwargs)
        if "team" in self.fields:
            self.fields["team"].widget = self.fields["team"].widget.widget


class EnvironmentAdmin(admin.ModelAdmin):
    form = EnvironmentForm
    fields = ["name", "team"]
    ordering = ["name", "team"]
    list_display = ("name", "team")
    inlines = (UserRoleInline,)

    def get_readonly_fields(self, request, obj=None):
        # When editting, the Team field should be readonly
        if obj:
            return ["team"]
        else:
            return []
