from django.db.models import Q
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.errors import RuleBroken
from common.permissions import IsInternalStaff
from curriculum.models import Unit

from . import rules
from .models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    teacher_name = serializers.CharField(source="teacher.display_name", read_only=True)
    who = serializers.SerializerMethodField()
    family_name = serializers.SerializerMethodField()
    family_time_zone = serializers.SerializerMethodField()
    unit_label = serializers.SerializerMethodField()
    is_group = serializers.BooleanField(read_only=True)
    has_makeup = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "kind", "kind_label", "enrolment", "lead", "teacher", "teacher_name", "who", "family_name",
                  "family_time_zone", "starts_at", "minutes", "status", "status_label", "unit", "unit_label",
                  "parent_note", "private_note", "reported_at", "makeup_owed", "has_makeup", "makeup_for",
                  "trial_level", "is_group", "is_demo"]
        read_only_fields = ["status", "reported_at", "makeup_owed", "is_demo", "parent_note", "private_note", "trial_level"]

    def get_who(self, ls):
        if ls.enrolment_id:
            g = ls.enrolment.group_name
            return f"{ls.enrolment.student.name}" + (f" ({g})" if g else "")
        return f"Trial: {ls.lead.child_name or 'child'} ({ls.lead})" if ls.lead_id else ""

    def get_family_name(self, ls):
        if ls.enrolment_id:
            return ls.enrolment.student.family.parent_name
        return ls.lead.parent_name if ls.lead_id else ""

    def get_family_time_zone(self, ls):
        if ls.enrolment_id:
            return ls.enrolment.student.family.time_zone
        return (ls.lead.time_zone or "Europe/London") if ls.lead_id else ""

    def get_unit_label(self, ls):
        return f"Lesson {ls.unit.number}: {ls.unit.title_nd}" if ls.unit_id else ""

    def get_has_makeup(self, ls):
        return hasattr(ls, "makeup") and ls.makeup is not None


def lesson_queryset():
    return Lesson.objects.select_related("enrolment__student__family", "enrolment__package", "lead", "teacher", "unit", "makeup")


def filter_range(qs, params):
    if params.get("from"):
        qs = qs.filter(starts_at__gte=params["from"])
    if params.get("to"):
        qs = qs.filter(starts_at__lt=params["to"])
    if params.get("unreported") == "1":
        from django.utils import timezone
        qs = qs.filter(status=Lesson.Status.SCHEDULED, starts_at__lt=timezone.now())
    return qs


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [IsInternalStaff]
    filterset_fields = ["teacher", "status", "kind", "enrolment", "makeup_owed", "enrolment__student__family"]
    search_fields = ["enrolment__student__first_name", "enrolment__student__family__parent_name", "lead__parent_name"]
    ordering_fields = ["starts_at"]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        return filter_range(lesson_queryset(), self.request.query_params)

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        lesson = self.get_object()
        unit = Unit.objects.filter(pk=request.data.get("unit")).first() if request.data.get("unit") else None
        rules.report(lesson, request.user, request.data.get("status"), request.data.get("parent_note", ""),
                     request.data.get("private_note", ""), unit, request.data.get("trial_level", ""))
        return Response(self.get_serializer(lesson).data)

    @action(detail=True, methods=["post"])
    def makeup(self, request, pk=None):
        at = serializers.DateTimeField().to_internal_value(request.data.get("starts_at"))
        m = rules.book_makeup(self.get_object(), at, request.user)
        return Response(self.get_serializer(m).data, status=201)

    @action(detail=True, methods=["post"])
    def move_time(self, request, pk=None):
        lesson = self.get_object()
        if lesson.status != Lesson.Status.SCHEDULED:
            raise RuleBroken("Only a scheduled lesson can be moved.", "detail")
        lesson.starts_at = serializers.DateTimeField().to_internal_value(request.data.get("starts_at"))
        lesson.save(update_fields=["starts_at", "updated_at"])
        return Response(self.get_serializer(lesson).data)
