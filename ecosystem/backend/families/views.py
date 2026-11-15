import secrets

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.errors import RuleBroken
from common.permissions import IsInternalStaff
from common.views import SoftDeleteMixin
from privacy.models import SensitiveAccess
from users.models import User

from . import validation
from .models import Family, Message, Student
from .serializers import FamilySerializer, MessageSerializer, StudentSerializer


class FamilyViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = FamilySerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["parent_name", "email", "phone", "students__first_name", "city"]
    filterset_fields = ["country", "owner", "needs_cleanup", "founding_family"]
    ordering_fields = ["parent_name", "created_at"]

    def get_queryset(self):
        return Family.objects.select_related("owner").prefetch_related("students").distinct()

    def perform_create(self, serializer):
        reason = serializer.validated_data.pop("override_reason", "")
        fam = Family(**serializer.validated_data)
        validation.save_family(fam, self.request.user, override_reason=reason)
        serializer.instance = fam

    def perform_update(self, serializer):
        reason = serializer.validated_data.pop("override_reason", "")
        fam = serializer.instance
        for k, v in serializer.validated_data.items():
            setattr(fam, k, v)
        validation.save_family(fam, self.request.user, override_reason=reason)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Everything that has happened with this family, newest first."""
        from audit.models import AuditEntry
        fam = self.get_object()
        events = []
        for d in fam.documents.exclude(status="draft"):
            events.append({"at": str(d.issue_date), "what": f"{d.get_kind_display()} {d.number}", "detail": f"{d.currency} {d.total} · {d.get_status_display()}"})
        for p in fam.payments.all():
            events.append({"at": str(p.received_on), "what": "Payment" + (" (reversed)" if p.reversed_at else ""), "detail": f"{p.currency} {p.amount} by {p.get_method_display()}"})
        for s in fam.students.all():
            for e in s.enrolments.all():
                for h in e.history.all():
                    events.append({"at": h.at.date().isoformat(), "what": f"{s.first_name}: {e.Stage(h.to_stage).label}", "detail": h.reason})
        for a in AuditEntry.objects.filter(object_type="Family", object_id=str(fam.pk))[:30]:
            events.append({"at": a.at.date().isoformat(), "what": a.summary, "detail": a.reason})
        events.sort(key=lambda e: e["at"], reverse=True)
        return Response(events)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        fam = self.get_object()
        if request.method == "POST":
            body = (request.data.get("body") or "").strip()
            if not body:
                raise RuleBroken("Write a message first.", "body")
            Message.objects.create(family=fam, sender=request.user, body=body, read_by_staff=True)
        fam.messages.filter(read_by_staff=False).update(read_by_staff=True)
        return Response(MessageSerializer(fam.messages.select_related("sender"), many=True).data)

    @action(detail=True, methods=["post"])
    def create_login(self, request, pk=None):
        """Gives the parent a login for the app. The one-time password is shown once to staff."""
        fam = self.get_object()
        if fam.login_id:
            raise RuleBroken("This family already has an app login.", "detail")
        if not fam.email:
            raise RuleBroken("Add the parent's email first; it is their username.", "email")
        if User.objects.filter(username=fam.email).exists():
            raise RuleBroken("Another login already uses this email.", "email")
        password = secrets.token_urlsafe(9)
        u = User.objects.create_user(username=fam.email, email=fam.email, password=password, role=User.Role.PARENT,
                                     first_name=fam.parent_name.split(" ")[0], time_zone=fam.time_zone)
        fam.login = u
        fam.save(update_fields=["login"])
        record(request.user, "create", u, f"Created app login for {fam}")
        return Response({"username": u.username, "password": password})


class StudentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["first_name", "last_name", "family__parent_name"]
    filterset_fields = ["family", "level"]

    def get_queryset(self):
        return Student.objects.select_related("family")

    @action(detail=True, methods=["get"])
    def support_notes(self, request, pk=None):
        s = self.get_object()
        SensitiveAccess.objects.create(user=request.user, student=s)
        return Response({"support_notes": s.support_notes})
