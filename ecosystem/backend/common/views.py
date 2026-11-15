from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record

from .permissions import IsLeadership


class SoftDeleteMixin:
    """DELETE moves a record to the bin. Leadership can list the bin and restore."""

    def perform_destroy(self, instance):
        instance.soft_delete(self.request.user)
        record(self.request.user, "delete", instance, f"Moved {instance} to the bin")

    @action(detail=False, methods=["get"], permission_classes=[IsLeadership])
    def bin(self, request):
        model = self.get_queryset().model
        rows = model.all_objects.filter(deleted_at__isnull=False).order_by("-deleted_at")[:200]
        return Response(self.get_serializer(rows, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[IsLeadership])
    def restore(self, request, pk=None):
        model = self.get_queryset().model
        obj = model.all_objects.get(pk=pk)
        obj.restore()
        record(request.user, "restore", obj, f"Restored {obj} from the bin")
        return Response(self.get_serializer(obj).data, status=status.HTTP_200_OK)
