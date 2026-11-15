from rest_framework import serializers, viewsets

from common.permissions import IsLeadership

from .models import AuditEntry


class AuditSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.display_name", default="System", read_only=True)

    class Meta:
        model = AuditEntry
        fields = ["id", "at", "actor", "actor_name", "action", "object_type", "object_id", "summary", "reason"]


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    permission_classes = [IsLeadership]
    queryset = AuditEntry.objects.select_related("actor")
    search_fields = ["summary", "reason", "object_type"]
    filterset_fields = ["action", "object_type", "actor"]
