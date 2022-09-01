from django_unicorn.components import UnicornView
from core.models import Environment


class EnvToSelectView(UnicornView):
    environments = {}  # Environment.objects.none()

    def hydrate(self):
        envs = Environment.objects.all().order_by('team__name', 'name')  # .filter(user=self.request.user)
        self.environments = {}
        for env in envs:
            self.environments.setdefault(env.team.name, []).append(env)
