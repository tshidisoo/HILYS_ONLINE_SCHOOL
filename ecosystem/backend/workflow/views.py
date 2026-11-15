from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from audit.log import record
from common.permissions import IsInternalStaff, IsLeadership

from .models import Feedback, Notification, Task


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.display_name", default="", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "notes", "assignee", "assignee_name", "due_on", "status", "status_label", "link_type",
                  "link_id", "is_demo", "created_at"]
        read_only_fields = ["is_demo"]


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsInternalStaff]
    filterset_fields = ["assignee", "status", "link_type", "link_id"]
    search_fields = ["title", "notes"]
    ordering_fields = ["due_on", "created_at"]

    def get_queryset(self):
        qs = Task.objects.select_related("assignee")
        if self.request.query_params.get("mine") == "1":
            qs = qs.filter(assignee=self.request.user)
        return qs

    def perform_create(self, serializer):
        t = serializer.save(created_by=self.request.user)
        if t.assignee and t.assignee != self.request.user:
            from .notify import notify
            notify([t.assignee], f"New task: {t.title}", f"From {self.request.user}", f"/tasks?open={t.pk}")


class FeedbackSerializer(serializers.ModelSerializer):
    family_name = serializers.CharField(source="family.parent_name", read_only=True)
    link = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ["id", "family", "family_name", "reason", "sent_at", "answered_at", "rating", "would_recommend",
                  "best", "improve", "may_quote", "link", "is_demo", "created_at"]
        read_only_fields = ["sent_at", "answered_at", "rating", "would_recommend", "best", "improve", "may_quote", "is_demo"]

    def get_link(self, f):
        from django.conf import settings
        return f"{settings.API_PUBLIC_URL}/feedback/{f.token}"


class FeedbackViewSet(viewsets.ModelViewSet):
    """Survey links are made by staff; the answers are for leadership only."""
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.select_related("family")
    filterset_fields = ["family"]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        return [IsInternalStaff()] if self.action == "create" else [IsLeadership()]

    def perform_create(self, serializer):
        f = serializer.save(sent_at=timezone.now())
        record(self.request.user, "create", f, f"Made a feedback link for {f.family}")

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        if not request.user.is_leadership:  # staff get the link to send, not the answers
            resp.data = {"link": resp.data["link"]}
        return resp


@api_view(["GET"])
@permission_classes([])
def notifications(request):
    if not request.user.is_authenticated:
        return Response(status=401)
    qs = Notification.objects.filter(user=request.user)[:30]
    unread = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
    return Response({"unread": unread, "items": [{"id": n.pk, "title": n.title, "body": n.body, "link": n.link,
                                                  "created_at": n.created_at, "read": bool(n.read_at)} for n in qs]})


@api_view(["POST"])
def notifications_read(request):
    Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return Response(status=204)
