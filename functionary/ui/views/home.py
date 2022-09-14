from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.models import Environment


@login_required
def home(request):
    if "environment_id" not in request.session:
        envs = request.user.environments()
        if envs:
            request.session["environment_id"] = str(envs.first().id)
        elif request.user.is_superuser:
            request.session["environment_id"] = str(
                Environment.objects.all().order_by("team__name", "name").first().id
            )

    return render(request, "home.html")
