import csv

from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from common.permissions import IsFinance

from . import rules
from .models import Account, Entry


class AccountSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Account
        fields = ["id", "name", "kind", "kind_label", "currency", "payment_methods", "is_active"]


class EntrySerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)

    class Meta:
        model = Entry
        fields = ["id", "account", "account_name", "kind", "kind_label", "amount", "currency", "category", "on_date",
                  "note", "receipt_photo", "payment", "is_demo"]
        read_only_fields = ["payment", "is_demo", "currency"]

    def validate(self, d):
        if d.get("kind") not in (None, Entry.Kind.EXPENSE, Entry.Kind.INCOME):
            raise serializers.ValidationError({"kind": ["Use the transfer screen to move money between accounts."]})
        if d.get("amount") is not None and d["amount"] <= 0:
            raise serializers.ValidationError({"amount": ["The amount must be more than zero."]})
        return d


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsFinance]
    queryset = Account.objects.all()

    @action(detail=False, methods=["post"])
    def transfer(self, request):
        rules.transfer(request.user, Account.objects.get(pk=request.data["from_account"]),
                       Account.objects.get(pk=request.data["to_account"]), request.data.get("amount"),
                       request.data.get("on_date"), request.data.get("note", ""))
        return Response(status=201)


class EntryViewSet(viewsets.ModelViewSet):
    serializer_class = EntrySerializer
    permission_classes = [IsFinance]
    filterset_fields = ["account", "kind", "category", "currency"]
    search_fields = ["note", "category"]
    ordering_fields = ["on_date", "amount"]
    queryset = Entry.objects.select_related("account")
    http_method_names = ["get", "post", "patch"]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user, currency=serializer.validated_data["account"].currency)


@api_view(["GET"])
@permission_classes([IsFinance])
def overview(request):
    return Response({"accounts": rules.account_balances(), "cash_flow": rules.cash_flow(),
                     "ageing": rules.money_owed_ageing(), "categories": Entry.CATEGORIES})


@api_view(["GET"])
@permission_classes([IsFinance])
def export(request):
    """A clean file an accountant's system can take."""
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="hilys-money.csv"'
    w = csv.writer(resp)
    w.writerow(["Date", "Account", "Type", "Category", "Amount", "Currency", "Note"])
    for e in Entry.objects.select_related("account").order_by("on_date", "id"):
        w.writerow([e.on_date, e.account.name, e.get_kind_display(), e.category, e.amount, e.currency, e.note])
    return resp
