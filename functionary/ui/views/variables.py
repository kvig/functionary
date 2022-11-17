from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, Team, Variable

from ..forms.variables import VariableForm


def _get_parent(parent_id):
    parent = Environment.objects.filter(id=parent_id)
    if not parent:
        parent = Team.objects.filter(id=parent_id)
    return parent.get() if parent else None


@require_POST
@login_required
def add_unicorn(request):
    form = None

    parent = _get_parent(request.POST.get("parent_id"))
    if request.user.has_perm(Permission.VARIABLE_CREATE, parent):
        form = VariableForm(request.POST)

        if form.is_valid():
            kws = {
                "name": form.cleaned_data["name"],
                "value": form.cleaned_data["value"],
                "description": form.cleaned_data["description"],
                "protect": form.cleaned_data["protect"],
            }

            if isinstance(parent, Environment):
                Variable.objects.create(environment=parent, **kws)
            else:
                Variable.objects.create(team=parent, **kws)

            # redirect to the same URL
            return redirect(to=request.META["HTTP_REFERER"])
        args = {"form": form, "object": parent}
        return render(request, "core/environment_detail.html", context=args, status=400)

    return HttpResponseForbidden()


@login_required
def add_variable(request, parent_id):
    parent = _get_parent(parent_id)

    if request.user.has_perm(Permission.VARIABLE_CREATE, parent):
        return HttpResponseForbidden()

    POST = None
    if request.POST:
        POST = request.POST.copy()
        if isinstance(parent, Environment):
            POST["environment"] = parent
        else:
            POST["team"] = parent

    form = VariableForm(POST)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(to=request.META.get("HTTP_REFERER"))
    context = {
        "form": form,
        "parent": parent,
    }

    return render(request, "forms/variable_form.html", context)


@login_required
def update_variable(request, pk):
    variable = get_object_or_404(Variable, id=pk)

    if request.user.has_perm(Permission.VARIABLE_UPDATE, variable):
        parent_id = variable.environment.id or variable.team.id
        form = VariableForm(
            request.POST or vars(variable), parent_id=parent_id, instance=variable
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                return redirect(to=request.META.get("HTTP_REFERER"))

        context = {"form": form, "variable": variable, "parent_id": parent_id}
        return render(request, "forms/variable_form.html", context)

    return HttpResponseForbidden()


@require_POST
@login_required
def delete_variable(request, pk):
    variable = get_object_or_404(Variable, id=pk)

    if request.user.has_perm(Permission.VARIABLE_DELETE, variable):
        variable.delete()
        return HttpResponse("")

    return HttpResponseForbidden()


class VariableView(LoginRequiredMixin, UserPassesTestMixin, View):
    form_class = VariableForm

    def post(self, request, parent_id):
        POST = request.POST.copy()
        parent = _get_parent(parent_id)

        if parent:
            if isinstance(parent, Environment):
                POST["environment"] = parent
            else:
                POST["team"] = parent

        form = VariableForm(POST, parent_id=parent_id)

        if form.is_valid():
            form.save()
            context = {"variable": form.instance, "parent_id": parent_id}
            return render(request, "core/variable/row.html", context)

        context = {"form": form, "parent_id": parent_id, "add": True}
        context.update(
            {
                "form": form.render("forms/var_form.html", context),
            }
        )
        return render(request, "forms/variable_form.html", context)

    def get(self, request, pk):
        variable = get_object_or_404(Variable, id=pk)
        context = {
            "variable": variable,
            "parent_id": variable.environment.id
            if variable.environment
            else variable.team.id,
        }
        context["var_update"] = request.user.has_perm(
            Permission.VARIABLE_UPDATE, variable
        )
        context["var_delete"] = request.user.has_perm(
            Permission.VARIABLE_DELETE, variable
        )

        return render(request, "core/variable/row.html", context)

    def test_func(self):
        obj = (
            _get_parent(self.kwargs["parent_id"])
            if "parent_id" in self.kwargs
            else get_object_or_404(Variable, id=self.kwargs["pk"])
        )
        match self.request.method:
            case "POST":
                return self.request.user.has_perm(Permission.VARIABLE_CREATE, obj)
            case _:
                return self.request.user.has_perm(Permission.VARIABLE_READ, obj)


class UpdateVariableView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk, parent_id):
        variable = get_object_or_404(Variable, id=pk)

        data = request.POST.copy()
        data["environment"] = variable.environment
        data["team"] = variable.team

        form = VariableForm(data, parent_id=parent_id, instance=variable)

        if form.is_valid():
            form.save()
            context = {"variable": variable, "parent_id": parent_id}
            context["var_update"] = request.user.has_perm(
                Permission.VARIABLE_UPDATE, variable
            )
            context["var_delete"] = request.user.has_perm(
                Permission.VARIABLE_DELETE, variable
            )

            return render(request, "core/variable/row.html", context)

        context = {
            "form": form,
            "variable": variable,
            "parent_id": parent_id,
        }
        return render(request, "forms/variable_form.html", context)

    def get(self, request, pk, parent_id):
        variable = get_object_or_404(Variable, id=pk)

        POST = request.POST.copy() if request.POST else vars(variable)
        POST["environment"] = variable.environment
        POST["team"] = variable.team

        form = VariableForm(POST, parent_id=parent_id, instance=variable)
        context = {"form": form, "variable": variable, "parent_id": parent_id}
        context.update(
            {
                "form": form.render("forms/var_form.html", context),
            }
        )

        return render(request, "forms/variable_form.html", context)

    def test_func(self):
        obj = (
            _get_parent(self.kwargs["parent_id"])
            if "parent_id" in self.kwargs
            else get_object_or_404(Variable, id=self.kwargs["pk"])
        )
        match self.request.method:
            case "POST":
                return self.request.user.has_perm(Permission.VARIABLE_UPDATE, obj)
            case "GET":
                return self.request.user.has_perm(Permission.VARIABLE_UPDATE, obj)
            case _:
                return self.request.user.has_perm(Permission.VARIABLE_READ, obj)
