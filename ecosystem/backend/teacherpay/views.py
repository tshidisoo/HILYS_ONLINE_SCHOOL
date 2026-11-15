from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsFinance
from finance.models import Account
from users.models import User

from . import rules
from .models import PayStatement


class PayStatementSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.display_name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PayStatement
        fields = ["id", "teacher", "teacher_name", "month", "currency", "lines", "total", "status", "status_label",
                  "paid_on", "unreported"]
        read_only_fields = fields


class PayStatementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PayStatementSerializer
    permission_classes = [IsFinance]
    filterset_fields = ["teacher", "month", "status"]
    queryset = PayStatement.objects.select_related("teacher")

    @action(detail=False, methods=["post"])
    def build(self, request):
        y, m = (int(x) for x in request.data["month"].split("-"))
        out = [rules.build(t, y, m) for t in User.objects.filter(role=User.Role.TEACHER, teacher_profile__isnull=False)]
        return Response(self.get_serializer(out, many=True).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return Response(self.get_serializer(rules.approve(self.get_object(), request.user)).data)

    @action(detail=True, methods=["post"])
    def paid(self, request, pk=None):
        st = rules.mark_paid(self.get_object(), request.user, Account.objects.get(pk=request.data.get("account")))
        return Response(self.get_serializer(st).data)
