from django.forms import ModelForm

from core.models import Environment, Team, Variable


class VariableForm(ModelForm):
    parent_id = None

    class Meta:
        model = Variable
        fields = ["name", "protect", "description", "value", "environment", "team"]

    def __init__(self, parent_id, **kwargs):
        super().__init__(**kwargs)
        self.parent_id = parent_id

    def clean_name(self):
        return self.cleaned_data["name"].upper()

    def clean_environment(self):
        if not self.cleaned_data["environment"]:
            env = Environment.objects.filter(id=self.parent_id)
            return env.get() if env.exists() else None
        return self.cleaned_data["environment"]

    def clean_team(self):
        if not self.cleaned_data["team"]:
            team = Team.objects.filter(id=self.parent_id)
            return team.get() if team.exists() else None
        return self.cleaned_data["team"]
