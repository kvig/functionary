from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import View

from core.auth import Permission
from core.models import Environment, Team, Variable

from ..forms.variables import VariableForm


def _get_parent(parent_id):
    parent = Environment.objects.filter(id=parent_id)
    if not parent:
        parent = Team.objects.filter(id=parent_id)
    return parent.get() if parent else None


def _render_variable_row(request, parent_id, variable):
    context = {
        "parent_id": parent_id,
        "variable": variable,
    }

    return render(request, "partials/variable_row.html", context)


def _render_variable_rows(request, parent_id=None, parent=None):
    parent = parent or _get_parent(parent_id)
    context = {
        "parent_id": parent_id,
        "variables": parent.vars,
    }

    return render(request, "partials/variable_rows.html", context)


def _render_variable_form(request, form, parent_id, variable=None, add=False):
    context = {"form": form, "variable": variable, "parent_id": parent_id, "add": add}

    if variable:
        context["pk"] = variable.id

    return render(request, "forms/variable_form.html", context)


@require_http_methods(["GET"])
@login_required
def all_variables(request, parent_id):
    parent_object = _get_parent(parent_id)

    if request.user.has_perm(Permission.VARIABLE_READ, parent_object):
        context = {
            "parent_id": parent_id,
            "variables": parent_object.vars,
        }

        return render(request, "partials/variable_rows.html", context)
    return HttpResponseForbidden()


@require_http_methods(["DELETE"])
@login_required
def delete_variable(request, pk):
    variable = get_object_or_404(Variable, id=pk)

    if request.user.has_perm(Permission.VARIABLE_DELETE, variable):
        variable.delete()
        return HttpResponse("")

    return HttpResponseForbidden(f"Permission denied deleting {variable.name}")


class VariableView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, parent_id):
        data = request.POST.copy()
        parent = _get_parent(parent_id)

        if parent:
            if isinstance(parent, Environment):
                data["environment"] = parent
            else:
                data["team"] = parent

        form = VariableForm(parent_id, data=data)

        if form.is_valid():
            form.save()
            return _render_variable_rows(request, parent=parent, parent_id=parent_id)

        return _render_variable_form(request, form, parent_id, add=True)

    def get(self, request, parent_id):
        form = VariableForm(parent_id)

        return _render_variable_form(request, form, parent_id, add=True)

    def test_func(self):
        obj = (
            _get_parent(self.kwargs["parent_id"])
            if "parent_id" in self.kwargs
            else get_object_or_404(Variable, id=self.kwargs["pk"])
        )
        if self.request.method == "POST":
            return self.request.user.has_perm(Permission.VARIABLE_CREATE, obj)
        else:
            return self.request.user.has_perm(Permission.VARIABLE_READ, obj)


class UpdateVariableView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk, parent_id):
        variable = get_object_or_404(Variable, id=pk)

        data = request.POST.copy()
        data["environment"] = variable.environment
        data["team"] = variable.team

        form = VariableForm(parent_id, data=data, instance=variable)

        if form.is_valid():
            form.save()
            return _render_variable_rows(request, parent_id=parent_id)

        return _render_variable_form(request, form, parent_id, variable)

    def get(self, request, pk, parent_id):
        variable = get_object_or_404(Variable, id=pk)

        data = request.POST.copy() if request.POST else vars(variable)
        data["environment"] = variable.environment
        data["team"] = variable.team

        form = VariableForm(parent_id, data=data, instance=variable)
        return _render_variable_form(request, form, parent_id, variable)

    def handle_no_permission(self):
        return HttpResponseForbidden("Permission Denied")

    def test_func(self):
        obj = (
            _get_parent(self.kwargs["parent_id"])
            if "parent_id" in self.kwargs
            else get_object_or_404(Variable, id=self.kwargs["pk"])
        )
        if self.request.method in ["POST", "GET"]:
            return self.request.user.has_perm(Permission.VARIABLE_UPDATE, obj)
        else:
            return self.request.user.has_perm(Permission.VARIABLE_READ, obj)
