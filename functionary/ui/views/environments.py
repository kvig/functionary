from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django_htmx import http

from core.auth import Permission
from core.models import Environment, Package, Variable


class EnvironmentListView(LoginRequiredMixin, ListView):
    model = Environment

    def get_queryset(self):
        """Sorts based on team name, then env name."""
        if self.request.user.is_superuser:
            return (
                super()
                .get_queryset()
                .select_related("team")
                .order_by("team__name", "name")
            )
        else:
            return self.request.user.environments().select_related("team")


class EnvironmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Environment

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "team",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        env = self.get_object()
        context["packages"] = Package.objects.filter(environment=env)
        context["var_create"] = self.request.user.has_perm(
            Permission.VARIABLE_CREATE, env
        )
        context["var_update"] = self.request.user.has_perm(
            Permission.VARIABLE_UPDATE, env
        )
        context["var_delete"] = self.request.user.has_perm(
            Permission.VARIABLE_DELETE, env
        )
        context["variables"] = (
            env.vars
            if self.request.user.has_perm(Permission.VARIABLE_READ, env)
            else Variable.objects.none()
        )
        return context

    def test_func(self):
        return self.request.user.has_perm(
            Permission.ENVIRONMENT_READ, self.get_object()
        )


class EnvironmentSelectView(LoginRequiredMixin, TemplateView):
    environments = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["environments"] = self.environments
        return context

    def post(self, request):
        pk = request.POST["environment_id"]
        get_object_or_404(Environment, id=pk)

        request.session["environment_id"] = pk
        next = request.POST.get("next")
        if not next:
            next = "/ui/"
        return http.trigger_client_event(HttpResponse(""), "reloadData")

    def get(self, request):
        if self.request.user.is_superuser:
            envs = (
                Environment.objects.select_related("team")
                .all()
                .order_by("team__name", "name")
            )
        else:
            envs = self.request.user.environments.select_related("team").order_by(
                "team__name", "name"
            )

        self.environments = {}
        for env in envs:
            self.environments.setdefault(env.team.name, []).append(env)

        ctx = self.get_context_data()
        ctx["next"] = request.GET["next"]
        return render(request, "forms/environment_selector.html", ctx)
