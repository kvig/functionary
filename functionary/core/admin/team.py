from django import forms
from django.contrib import admin

from core.models import Environment, Team, TeamUserRole


class EnvironmentChoiceField(forms.ModelMultipleChoiceField):
    """Custom choice field to override the name of the Environment"""

    def label_from_instance(self, obj):
        return obj.name

    def widget_attrs(self, widget):
        return {"disabled": "disabled"}


class UserRoleInline(admin.TabularInline):
    """Inline form to add users to the Team"""

    model = TeamUserRole
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


class TeamForm(forms.ModelForm):
    """Custom form to show the environments associated with the team"""

    environments = EnvironmentChoiceField(
        queryset=Environment.objects.none(),
        required=False,
    )

    class Meta:
        model = Team
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)
        # Since the Team doesn't have a direct reference to the
        # Environments, add the queryset manually for this Team
        if self.instance and "environments" in self.fields:
            self.fields["environments"].queryset = self.instance.environments.order_by(
                "name"
            )


class TeamAdmin(admin.ModelAdmin):
    form = TeamForm
    ordering = ["name"]
    inlines = (UserRoleInline,)

    def get_form(self, request, obj, *args, **kwargs):
        form = super().get_form(request, obj, *args, **kwargs)
        # We don't want environments when adding a Team, remove the
        # field here. Exclude doesn't work because the field is
        # already declared on the form.
        if not obj:
            form.base_fields.pop("environments")
            form.declared_fields.pop("environments")
        return form
