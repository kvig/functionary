from django.contrib.admin.apps import AdminConfig


class UIAdminConfig(AdminConfig):
    default_site = "ui.admin.site.AdminSite"
