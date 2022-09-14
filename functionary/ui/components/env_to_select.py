from django_unicorn.components import UnicornView

from core.models import Environment


class EnvToSelectView(UnicornView):
    environments = {}

    def hydrate(self):
        # Clear any old environments first
        self.environments = {}

        if self.request.user.is_superuser:
            envs = Environment.objects.all().order_by("team__name", "name")
        else:
            envs = self.request.user.environments()

        for env in envs:
            self.environments.setdefault(env.team.name, []).append(env)
