from django.urls import path

from .site import ui_admin_site

urlpatterns = [
    path("", ui_admin_site.urls),
]
