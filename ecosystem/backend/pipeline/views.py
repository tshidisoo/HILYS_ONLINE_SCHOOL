from django.db.models import Q
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.business_time import today
from common.errors import RuleBroken
from common.permissions import IsInternalStaff
from common.views import SoftDeleteMixin

from .models import Opportunity


class OpportunitySerializer(serializers.ModelSerializer):
    stage_label = serializers.CharField(source="get_stage_display", read_only=True)
    weighted_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    who = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source="owner.display_name", default="", read_only=True)

    class Meta:
        model = Opportunity
        fields = ["id", "title", "family", "lead", "organisation", "who", "stage", "stage_label", "chance", "value",
                  "currency", "weighted_value", "owner", "owner_name", "expected_close", "closed_on", "lost_to",
                  "lost_reason", "notes", "is_demo"]
        read_only_fields = ["stage", "closed_on", "lost_to", "lost_reason", "is_demo"]

    def get_who(self, o):
        return str(o.family or o.lead or o.organisation or "")


class OpportunityViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = OpportunitySerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["title", "organisation", "family__parent_name"]
    filterset_fields = ["stage", "owner", "currency"]
    queryset = Opportunity.objects.select_related("family", "lead", "owner")

    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        o = self.get_object()
        to = request.data.get("stage")
        if to not in Opportunity.Stage.values:
            raise RuleBroken("That stage does not exist.", "stage")
        if to == "lost":
            if not (request.data.get("lost_to") or "").strip() or not (request.data.get("lost_reason") or "").strip():
                raise RuleBroken("Say who or what it was lost to, and why.", "lost_reason")
            o.lost_to, o.lost_reason = request.data["lost_to"].strip(), request.data["lost_reason"].strip()
        o.stage, o.chance = to, Opportunity.DEFAULT_CHANCE[to]
        o.closed_on = today() if to in ("won", "lost") else None
        o.save()
        record(request.user, "stage", o, f"Moved opportunity {o.title} to {o.get_stage_display()}", o.lost_reason)
        return Response(self.get_serializer(o).data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        d = today()
        out = {}
        for o in Opportunity.objects.all():
            c = out.setdefault(o.currency, {"open_value": 0, "weighted": 0, "won_this_month": 0, "lost_this_month": 0})
            if o.stage not in ("won", "lost"):
                c["open_value"] += o.value
                c["weighted"] += o.weighted_value
            elif o.closed_on and o.closed_on.year == d.year and o.closed_on.month == d.month:
                c["won_this_month" if o.stage == "won" else "lost_this_month"] += o.value
        return Response(out)
