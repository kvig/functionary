from django.forms import ModelForm, ValidationError

from core.models import Environment, Team, Variable


class VariableForm(ModelForm):
    template_name = "forms/var_form.html"

    class Meta:
        model = Variable
        fields = ["name", "protect", "description", "value", "environment", "team"]

    def __init__(self, data, parent_id=None, **kwargs):
        super().__init__(data, **kwargs)
        if parent_id:
            self.parent_id = parent_id
        elif "instance" in kwargs:
            self.parent_id = (
                kwargs["instance"].environment.id or kwargs["instance"].team.id
            )
        elif "parent_id" in data:
            print("Expected")
            self.parent_id = data["parent_id"]
        else:
            print("UNEXPECTED")
            if hasattr(data, "parent_id"):
                self.parent_id = data.parent_id
            else:
                print("WTF?")

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

        if cleaned_data["environment"] and cleaned_data["team"]:
            raise ValidationError("Can have only a team or an environment, not both")
        elif not cleaned_data["environment"] and not cleaned_data["team"]:
            raise ValidationError("Must select an Environment or Team")

        return cleaned_data
