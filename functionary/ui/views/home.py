from django.shortcuts import render

from core.models import Environment, EnvironmentUserRole


def home(request):
    if "environment_id" not in request.session:
        role = (
            EnvironmentUserRole.objects.filter(user=request.user)
            .order_by("environment__team__name", "environment__name")
            .first()
        )
        if role:
            request.session["environment_id"] = str(role.environment.id)
        elif request.user.is_superuser:
            request.session["environment_id"] = str(
                Environment.objects.all().order_by("team__name", "name").first().id
            )

    return render(request, "home.html")
