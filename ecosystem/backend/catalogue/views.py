from rest_framework import serializers, viewsets

from audit.log import record
from common.permissions import IsInternalStaff
from common.views import SoftDeleteMixin

from .models import CatalogueItem


class CatalogueItemSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    lesson_type_label = serializers.CharField(source="get_lesson_type_display", read_only=True)
    lessons_per_month = serializers.IntegerField(read_only=True)

    class Meta:
        model = CatalogueItem
        fields = ["id", "name", "description", "kind", "kind_label", "lesson_type", "lesson_type_label",
                  "lessons_per_week", "lessons_per_month", "price", "currency", "unit", "is_active", "on_website",
                  "is_draft_price", "sort_order"]


class CatalogueViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    serializer_class = CatalogueItemSerializer
    permission_classes = [IsInternalStaff]
    queryset = CatalogueItem.objects.all()
    search_fields = ["name", "description"]
    filterset_fields = ["kind", "lesson_type", "is_active", "on_website", "currency"]
    ordering_fields = ["sort_order", "name", "price"]

    def perform_update(self, serializer):
        old = serializer.instance.price
        item = serializer.save()
        if old != item.price:
            record(self.request.user, "price", item, f"Changed price of {item} from {old} to {item.price} {item.currency}")
