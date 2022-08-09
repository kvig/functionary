from django.urls import path
from .views import dashboard, functions


app_name = "ui"

urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("function_list/", functions.function_list, name="function_list"),
    path("function/<uuid:id>", functions.function, name="function"),
]
