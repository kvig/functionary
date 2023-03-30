from core.api.permissions import HasEnvironmentPermissionForAction
from core.api.viewsets import EnvironmentReadOnlyModelViewSet
from core.models import Function

from ..serializers import FunctionSerializer


class FunctionViewSet(EnvironmentReadOnlyModelViewSet):
    """View functions across all known packages"""

    queryset = Function.active_objects.all()
    serializer_class = FunctionSerializer
    permission_classes = [HasEnvironmentPermissionForAction]
    environment_through_field = "package"
