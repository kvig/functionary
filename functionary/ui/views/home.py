from django.shortcuts import render

from core.models import EnvironmentUserRole


def home(request):
    if "environment_id" not in request.session:
        role = (
            EnvironmentUserRole.objects.filter(user=request.user)
            .order_by("environment__team__name", "environment__name")
            .first()
        )
        if role:
            request.session["environment_id"] = str(role.environment.id)
    return render(request, "home.html")
