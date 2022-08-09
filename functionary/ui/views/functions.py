from django.shortcuts import render
from core.models import Function


def function_list(request):
    functions = Function.objects.all()
    return render(request, "functions/function_list.html", {"functions": functions})


def function(request, id):
    function = Function.objects.get(id=id)
    return render(request, "functions/function.html", {"function": function})
