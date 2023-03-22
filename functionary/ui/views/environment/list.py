from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from core.models import Environment
from ui.tables.enviroment import EnviromentFilter, EnvironmentTable

PAGINATION_AMOUNT = 15


class EnvironmentListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = Environment
    table_class = EnvironmentTable
    paginate_by = PAGINATION_AMOUNT
    template_name = "default_list.html"
    filterset_class = EnviromentFilter
    queryset = Environment.objects.select_related("team")
