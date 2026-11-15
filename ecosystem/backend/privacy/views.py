from datetime import timedelta

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.business_time import today
from common.permissions import IsInternalStaff, IsLeadership
from families.models import Family

from .models import DataRequest, SensitiveAccess


class DataRequestSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    family_name = serializers.CharField(source="family.parent_name", default="", read_only=True)

    class Meta:
        model = DataRequest
        fields = ["id", "family", "family_name", "requester", "kind", "kind_label", "status", "status_label",
                  "due_on", "notes", "created_at"]


class DataRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DataRequestSerializer
    permission_classes = [IsInternalStaff]
    queryset = DataRequest.objects.select_related("family")
    filterset_fields = ["status", "kind"]
    http_method_names = ["get", "post", "patch"]

    def perform_create(self, serializer):
        serializer.save(due_on=today() + timedelta(days=30), handled_by=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[IsLeadership], url_path=r"export/(?P<family_id>\d+)")
    def export(self, request, family_id=None):
        """Everything held about one family, as one file."""
        from families.serializers import FamilySerializer
        from billing.views import DocumentSerializer, PaymentSerializer
        from lessons.views import LessonSerializer, lesson_queryset
        fam = Family.objects.get(pk=family_id)
        data = {"family": FamilySerializer(fam).data,
                "students": [{"name": s.name, "birth_year": s.birth_year, "level": s.level, "support_notes": s.support_notes, "notes": s.notes} for s in fam.students.all()],
                "lessons": LessonSerializer(lesson_queryset().filter(enrolment__student__family=fam), many=True).data,
                "documents": DocumentSerializer(fam.documents.all(), many=True).data,
                "payments": PaymentSerializer(fam.payments.all(), many=True).data,
                "messages": [{"at": m.created_at, "from": str(m.sender), "body": m.body} for m in fam.messages.all()]}
        record(request.user, "export", fam, f"Exported all data for {fam}")
        resp = Response(data)
        resp["Content-Disposition"] = f'attachment; filename="family-{fam.pk}-data.json"'
        return resp

    @action(detail=False, methods=["get"], permission_classes=[IsLeadership])
    def sensitive_access(self, request):
        rows = SensitiveAccess.objects.select_related("user", "student")[:100]
        return Response([{"at": r.at, "user": str(r.user), "student": str(r.student)} for r in rows])
