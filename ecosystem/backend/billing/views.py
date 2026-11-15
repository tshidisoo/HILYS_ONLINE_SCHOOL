from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from audit.log import record
from common.errors import RuleBroken
from common.permissions import IsFinance, IsInternalStaff, StaffReadFinanceWrite
from families.models import Family

from . import rules
from .models import Allocation, Document, Installment, Line, Payment
from .pdf import render_document


class LineSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    student_name = serializers.CharField(source="student.name", default="", read_only=True)

    class Meta:
        model = Line
        fields = ["id", "item", "description", "quantity", "unit_price", "amount", "student", "student_name"]


class DocumentSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True, read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    family_name = serializers.CharField(source="family.parent_name", read_only=True)
    related_number = serializers.CharField(source="related.number", default="", read_only=True)
    paid = serializers.SerializerMethodField()
    outstanding = serializers.SerializerMethodField()
    installments = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "kind", "kind_label", "number", "family", "family_name", "status", "status_label", "issue_date",
                  "due_date", "period", "currency", "total", "notes", "related", "related_number", "verify_code",
                  "lines", "paid", "outstanding", "installments", "amended_reason", "is_overdue", "is_demo", "created_at"]
        read_only_fields = ["number", "status", "total", "verify_code", "amended_reason", "is_demo", "issue_date"]

    def get_paid(self, d):
        return str(d.paid_amount()) if d.kind == "invoice" else None

    def get_outstanding(self, d):
        return str(d.outstanding()) if d.kind == "invoice" else None

    def get_installments(self, d):
        return [{"due_date": i.due_date, "amount": str(i.amount)} for i in d.installments.all()]

    def get_is_overdue(self, d):
        from common.business_time import today
        return bool(d.kind == "invoice" and d.status in ("issued", "part_paid") and d.due_date and d.due_date < today())


def pdf_response(doc):
    resp = HttpResponse(render_document(doc), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{doc.number or "draft"}.pdf"'
    return resp


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsInternalStaff]
    search_fields = ["number", "family__parent_name", "notes"]
    filterset_fields = ["kind", "status", "family", "currency", "period"]
    ordering_fields = ["issue_date", "created_at", "total", "due_date"]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        qs = Document.objects.select_related("family", "related").prefetch_related("lines__student", "installments", "allocations__payment")
        if self.request.query_params.get("overdue") == "1":
            from common.business_time import today
            qs = qs.filter(kind="invoice", status__in=["issued", "part_paid"], due_date__lt=today())
        return qs

    def perform_create(self, serializer):
        if serializer.validated_data["kind"] in ("receipt",):
            raise RuleBroken("Receipts are made when a payment is recorded.", "kind")
        doc = serializer.save(created_by=self.request.user, is_draft_text=serializer.validated_data["kind"] == "agreement")
        lines = self.request.data.get("lines") or []
        if lines:
            rules.set_lines(doc, lines)
        record(self.request.user, "create", doc, f"Started a {doc.get_kind_display().lower()} for {doc.family}")

    def perform_update(self, serializer):
        rules.ensure_draft(serializer.instance)
        doc = serializer.save()
        if "lines" in self.request.data:
            rules.set_lines(doc, self.request.data["lines"])

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        return Response(self.get_serializer(rules.issue(self.get_object(), request.user)).data)

    @action(detail=True, methods=["post"])
    def amend(self, request, pk=None):
        doc = rules.amend(self.get_object(), request.user, request.data.get("reason", ""), request.data.get("lines") or [])
        return Response(self.get_serializer(doc).data)

    @action(detail=True, methods=["post"])
    def to_invoice(self, request, pk=None):
        inv = rules.convert_quotation(self.get_object(), request.user)
        record(request.user, "create", inv, f"Turned {self.get_object()} into a draft invoice")
        return Response(self.get_serializer(inv).data, status=201)

    @action(detail=True, methods=["post"])
    def credit(self, request, pk=None):
        cn = rules.credit_note_for(self.get_object(), request.user, request.data.get("amount"), request.data.get("reason", ""))
        return Response(self.get_serializer(cn).data, status=201)

    @action(detail=True, methods=["post"])
    def plan(self, request, pk=None):
        plan = rules.payment_plan_for(self.get_object(), request.user, request.data.get("parts", 3))
        return Response(self.get_serializer(plan).data, status=201)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        doc = self.get_object()
        if doc.kind == "invoice" and doc.allocations.filter(payment__reversed_at__isnull=True).exists():
            raise RuleBroken("Payments are allocated to this invoice. Reverse them or issue a credit note.", "detail")
        if doc.is_locked and not request.user.can_override_rules:
            raise RuleBroken("Only the owner can cancel an issued document.", "detail")
        if doc.is_locked and not (request.data.get("reason") or "").strip():
            raise RuleBroken("Say why it is being cancelled.", "reason")
        doc.status = Document.Status.CANCELLED
        doc.save(update_fields=["status", "updated_at"])
        record(request.user, "cancel", doc, f"Cancelled {doc}", request.data.get("reason", ""))
        return Response(self.get_serializer(doc).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        return pdf_response(self.get_object())

    @action(detail=False, methods=["post"])
    def statement(self, request):
        fam = Family.objects.get(pk=request.data.get("family"))
        doc = rules.statement(fam, request.user, request.data.get("currency", "USD"))
        return Response(self.get_serializer(doc).data, status=201)

    @action(detail=False, methods=["post"])
    def monthly_invoices(self, request):
        """Draft next month's invoices for every active enrolment, one per family. Safe to run twice."""
        from enrolments.models import Enrolment
        period = request.data.get("period")
        if not period or len(period) != 7:
            raise RuleBroken("Choose the month, like 2026-12.", "period")
        made = 0
        by_family = {}
        for e in Enrolment.objects.filter(stage=Enrolment.Stage.ACTIVE, package__isnull=False).select_related("student__family", "package"):
            by_family.setdefault(e.student.family, []).append(e)
        for fam, ens in by_family.items():
            if Document.objects.filter(family=fam, kind="invoice", period=period).exclude(status="cancelled").exists():
                continue
            doc = Document.objects.create(kind="invoice", family=fam, period=period, currency=ens[0].package.currency,
                                          created_by=request.user, is_demo=fam.is_demo)
            rules.set_lines(doc, [{"item": e.package_id, "description": f"{e.package.name} – {period}",
                                   "unit_price": e.package.price, "student": e.student_id} for e in ens])
            made += 1
        record(request.user, "create", None, f"Drafted {made} invoices for {period}")
        return Response({"created": made})


class AllocationSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.number", read_only=True)

    class Meta:
        model = Allocation
        fields = ["invoice", "invoice_number", "amount"]


class PaymentSerializer(serializers.ModelSerializer):
    method_label = serializers.CharField(source="get_method_display", read_only=True)
    family_name = serializers.CharField(source="family.parent_name", read_only=True)
    allocations = AllocationSerializer(many=True, read_only=True)
    unallocated = serializers.SerializerMethodField()
    receipt_id = serializers.SerializerMethodField()
    recorded_by_name = serializers.CharField(source="recorded_by.display_name", default="", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "family", "family_name", "amount", "currency", "method", "method_label", "reference",
                  "received_on", "note", "allocations", "unallocated", "receipt_id", "recorded_by_name",
                  "reversed_at", "reversed_reason", "is_demo", "created_at"]
        read_only_fields = ["reversed_at", "reversed_reason", "is_demo"]

    def get_unallocated(self, p):
        return str(p.unallocated())

    def get_receipt_id(self, p):
        r = getattr(p, "receipt", None)
        return r.pk if r else None


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [StaffReadFinanceWrite]
    search_fields = ["reference", "family__parent_name", "note"]
    filterset_fields = ["family", "method", "currency"]
    ordering_fields = ["received_on", "amount"]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        qs = Payment.objects.select_related("family", "recorded_by", "receipt").prefetch_related("allocations__invoice")
        if self.request.query_params.get("unmatched") == "1":
            qs = [p for p in qs.filter(reversed_at__isnull=True) if p.unallocated() > 0]
        return qs

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        pay = rules.record_payment(request.user, d["family"], d["amount"], d["currency"], d["method"], d["received_on"],
                                   d.get("reference", ""), d.get("note", ""), request.data.get("allocations"))
        return Response(self.get_serializer(pay).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsFinance])
    def reverse(self, request, pk=None):
        pay = rules.reverse_payment(self.get_object(), request.user, request.data.get("reason", ""))
        return Response(self.get_serializer(pay).data)

    @action(detail=True, methods=["post"], permission_classes=[IsFinance])
    def allocate(self, request, pk=None):
        from django.db import transaction
        pay = self.get_object()
        with transaction.atomic():
            rules.allocate(pay, request.data.get("allocations") or [], request.user)
        record(request.user, "allocate", pay, f"Allocated {pay}")
        return Response(self.get_serializer(pay).data)
