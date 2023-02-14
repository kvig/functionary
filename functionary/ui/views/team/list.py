from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import SingleTableView

from core.models import Team
from ui.tables.team import TeamTable

PAGINATION_AMOUNT = 15


class TeamListView(LoginRequiredMixin, SingleTableView):
    model = Team
    table_class = TeamTable
    paginate_by = PAGINATION_AMOUNT
    template_name = "default_list.html"
