from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView

from core.models import Environment
from ui.tables.enviroment import EnvironmentTable

PAGINATION_AMOUNT = 15


class EnvironmentListView(LoginRequiredMixin, SingleTableView):
    model = Environment
    table_class = EnvironmentTable
    paginate_by = PAGINATION_AMOUNT
    template_name = "default_list.html"
