from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from core.auth import Permission
from core.models import Environment, Function, Task

from ..forms.forms import FunctionForm


class FunctionListView(ListView):
    model = Function

    def get_queryset(self):
        """Filters functions not in the environment then sorts based
        on package name, then function name."""

        env_id = self.request.session["environment_id"]
        return (
            super()
            .get_queryset()
            .filter(package__environment__id=env_id)
            .order_by("package__name", "name")
        )


class FunctionDetailView(DetailView):
    model = Function

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = FunctionForm(self.get_object())
        context["form"] = form.render("forms/function_detail.html")
        return context


def execute(request) -> HttpResponse:
    func = None
    form = None

    if request.method == "POST":
        env = Environment.objects.get(id=request.session.get("environment_id"))
        permissions = request.user.environment_permissions(env, inherited=True)

        if request.user.is_superuser or Permission.TASK_CREATE.value in permissions:
            func = Function.objects.get(id=request.POST["function_id"])
            form = FunctionForm(func, request.POST)

            if form.is_valid():

                # Create the new Task, the validated parameters are in form.cleaned_data
                Task.objects.create(
                    environment=env,
                    creator=request.user,
                    function=func,
                    parameters=form.cleaned_data,
                )

                # redirect to a new URL:
                return HttpResponseRedirect("/ui/task_list/")
        else:
            return HttpResponseForbidden()

    # if a GET (or any other method), create a blank form
    else:
        func = Function.objects.get(id=request.GET["function_id"])
        form = FunctionForm(func)

    return render(
        request,
        "core/function_detail.html",
        {"function": func, "form": form.render("forms/function_detail.html")},
    )
