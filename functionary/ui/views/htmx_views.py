from django.shortcuts import render

from ..forms.variables import VariableForm


def htmx_variable_form(request, parent_id):
    form = VariableForm({"parent_id": parent_id})
    context = {"form": form, "parent_id": parent_id, "add": True}
    context.update(
        {
            "form": form.render("forms/var_form.html", context),
        }
    )
    return render(request, "forms/variable_form.html", context=context)
