from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.permissions import IsInternalStaff
from common.views import SoftDeleteMixin

from . import rules
from .models import Enrolment, StageChange


class StageChangeSerializer(serializers.ModelSerializer):
    by_name = serializers.CharField(source="by.display_name", default="", read_only=True)

    class Meta:
        model = StageChange
        fields = ["from_stage", "to_stage", "by_name", "at", "reason"]


class EnrolmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    family = serializers.IntegerField(source="student.family_id", read_only=True)
    family_name = serializers.CharField(source="student.family.parent_name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.display_name", default="", read_only=True)
    package_name = serializers.CharField(source="package.name", default="", read_only=True)
    book_title = serializers.CharField(source="book.title", default="", read_only=True)
    stage_label = serializers.CharField(source="get_stage_display", read_only=True)
    history = StageChangeSerializer(many=True, read_only=True)
    next_gates = serializers.SerializerMethodField()

    class Meta:
        model = Enrolment
        fields = ["id", "student", "student_name", "family", "family_name", "teacher", "teacher_name", "package",
                  "package_name", "book", "book_title", "level", "group_name", "weekly_slots", "stage", "stage_label",
                  "start_date", "end_date", "notes", "history", "next_gates", "is_demo", "created_at"]
        read_only_fields = ["stage", "is_demo"]

    def get_next_gates(self, e):
        return {to: rules.gate_problems(e, to) for to in rules.ALLOWED[e.stage]}

    def validate_weekly_slots(self, v):
        rules.validate_slots(v)
        return v


class EnrolmentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = EnrolmentSerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["student__first_name", "student__family__parent_name", "group_name"]
    filterset_fields = ["stage", "teacher", "level", "package", "student__family"]
    ordering_fields = ["created_at", "stage", "start_date"]

    def get_queryset(self):
        return Enrolment.objects.select_related("student__family", "teacher", "package", "book").prefetch_related("history__by")

    def perform_create(self, serializer):
        e = serializer.save()
        record(self.request.user, "create", e, f"Enrolled {e.student}")

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        e = rules.move(self.get_object(), request.data.get("stage"), request.user, request.data.get("reason", ""))
        if e.stage == Enrolment.Stage.ACTIVE:
            from common.business_time import today
            from lessons.rules import schedule_month
            d = today()
            schedule_month(e, d.year, d.month)
        return Response(self.get_serializer(e).data)

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        from lessons.rules import schedule_month
        made = schedule_month(self.get_object(), int(request.data["year"]), int(request.data["month"]))
        return Response({"created": made})
