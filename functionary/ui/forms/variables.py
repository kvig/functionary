from django.forms import ModelForm, ValidationError

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

    def clean(self):
        cleaned_data = self.cleaned_data
        if "name" in cleaned_data:
            var_name = cleaned_data["name"]

            if not self.instance and (
                Variable.objects.filter(
                    name=var_name, environment_id=self.parent_id
                ).exists()
                or Variable.objects.filter(
                    name=var_name, team_id=self.parent_id
                ).exists()
            ):
                raise ValidationError(
                    f"A Variable named {var_name} already exists for {self.parent_id}"
                )

        env = cleaned_data.get("environment", None)
        team = cleaned_data.get("team", None)
        if env and team:
            raise ValidationError("Can have only a Team or an Environment, not both")
        elif not env and not team:
            raise ValidationError("Must select an Environment or Team")

        return cleaned_data
