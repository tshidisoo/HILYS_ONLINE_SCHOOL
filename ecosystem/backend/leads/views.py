from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.errors import RuleBroken
from common.permissions import IsInternalStaff
from common.views import SoftDeleteMixin

from . import rules
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    interest_label = serializers.CharField(source="get_interest_display", read_only=True)
    owner_name = serializers.CharField(source="owner.display_name", default="", read_only=True)
    reply_clock = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = ["id", "parent_name", "phone", "email", "country", "time_zone", "child_name", "child_age", "interest",
                  "interest_label", "suggested_level", "message", "source", "owner", "owner_name", "status",
                  "status_label", "notes", "reply_due_at", "first_reply_at", "reply_clock", "follow_ups",
                  "dismissed_reason", "needs_cleanup", "cleanup_reasons", "family", "is_demo", "created_at"]
        read_only_fields = ["reply_due_at", "first_reply_at", "follow_ups", "needs_cleanup", "cleanup_reasons",
                            "family", "dismissed_reason", "is_demo"]

    def get_reply_clock(self, lead):
        return rules.reply_clock(lead)

    def create(self, data):
        return rules.create_lead(data, source=data.pop("source", "Phone"), owner=data.pop("owner", None))

    def update(self, lead, data):
        for k, v in data.items():
            setattr(lead, k, v)
        rules.prepare(lead)
        lead.save()
        return lead


class LeadViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["parent_name", "child_name", "email", "phone", "message"]
    filterset_fields = ["status", "source", "owner", "needs_cleanup", "interest"]
    ordering_fields = ["created_at", "reply_due_at", "parent_name"]

    def get_queryset(self):
        qs = Lead.objects.select_related("owner")
        if self.request.query_params.get("clock") == "late":
            from django.utils import timezone
            qs = qs.filter(first_reply_at__isnull=True, reply_due_at__lt=timezone.now()).exclude(
                status__in=[Lead.Status.CONVERTED, Lead.Status.DISMISSED])
        if self.request.query_params.get("open") == "1":
            qs = qs.exclude(status__in=[Lead.Status.CONVERTED, Lead.Status.DISMISSED])
        return qs

    def perform_create(self, serializer):
        lead = serializer.save()
        record(self.request.user, "create", lead, f"Added lead {lead}")

    @action(detail=True, methods=["post"])
    def replied(self, request, pk=None):
        lead = rules.mark_replied(self.get_object(), request.user, request.data.get("note", ""))
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        lead = rules.dismiss(self.get_object(), request.data.get("reason", ""))
        record(request.user, "dismiss", lead, f"Dismissed lead {lead}", lead.dismissed_reason)
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"])
    def book_trial(self, request, pk=None):
        from lessons.models import Lesson
        from users.models import User
        lead = self.get_object()
        teacher = User.objects.filter(pk=request.data.get("teacher"), role=User.Role.TEACHER).first()
        if not teacher:
            raise RuleBroken("Choose a teacher for the trial.", "teacher")
        starts_at = serializers.DateTimeField().to_internal_value(request.data.get("starts_at"))
        Lesson.objects.create(kind=Lesson.Kind.TRIAL, lead=lead, teacher=teacher, starts_at=starts_at, is_demo=lead.is_demo)
        if not lead.first_reply_at:
            rules.mark_replied(lead, request.user, "Trial booked")
        lead.status = Lead.Status.TRIAL_BOOKED
        lead.save()
        record(request.user, "trial", lead, f"Booked a trial for {lead} with {teacher}")
        return Response(self.get_serializer(lead).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def convert(self, request, pk=None):
        """Turns a lead into a family with its first child and an enrolment at the Trial stage."""
        from enrolments.models import Enrolment
        from families.models import Family, Student
        from families.validation import save_family
        lead = self.get_object()
        if lead.status == Lead.Status.CONVERTED:
            raise RuleBroken("This lead is already a family.", "detail")
        fam = Family(parent_name=lead.parent_name or "Unnamed parent", email=lead.email, phone=lead.phone,
                     country=lead.country, time_zone=lead.time_zone or "Europe/London", owner=lead.owner or request.user,
                     source=lead.source, is_demo=lead.is_demo)
        save_family(fam, request.user, override_reason=request.data.get("override_reason", ""))
        child = Student.objects.create(family=fam, first_name=lead.child_name or "Child", level=lead.suggested_level or "",
                                       is_demo=lead.is_demo)
        trial = lead.trial_lessons.order_by("-starts_at").first()
        Enrolment.objects.create(student=child, lead=lead, level=child.level, teacher=trial.teacher if trial else None,
                                 is_demo=lead.is_demo)
        lead.status, lead.family = Lead.Status.CONVERTED, fam
        lead.save()
        record(request.user, "convert", lead, f"Lead {lead} became family {fam}")
        return Response({"family": fam.pk, "lead": self.get_serializer(lead).data})

    @action(detail=False, methods=["post"])
    def paste(self, request):
        """Paste a list: one lead per line, as  name, phone or email, child's name."""
        made = []
        for line in (request.data.get("text") or "").splitlines():
            parts = [p.strip() for p in line.split(",")]
            if not parts or not parts[0]:
                continue
            contact = parts[1] if len(parts) > 1 else ""
            data = {"parent_name": parts[0], "email" if "@" in contact else "phone": contact,
                    "child_name": parts[2] if len(parts) > 2 else ""}
            made.append(rules.create_lead(data, source=request.data.get("source", "WhatsApp"), owner=request.user))
        record(request.user, "create", None, f"Pasted {len(made)} leads")
        return Response(self.get_serializer(made, many=True).data, status=201)
