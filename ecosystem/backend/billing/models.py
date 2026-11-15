import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum

from common.models import CurrencyField, MoneyField, TimeStamped


def _code():
    return secrets.token_hex(5).upper()


class NumberSequence(models.Model):
    """Gapless numbers per document kind per year. Rows are locked while a number is taken."""
    kind = models.CharField(max_length=20)
    year = models.PositiveSmallIntegerField()
    last = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("kind", "year")]


class Document(TimeStamped):
    class Kind(models.TextChoices):
        QUOTATION = "quotation", "Quotation"
        INVOICE = "invoice", "Invoice"
        RECEIPT = "receipt", "Receipt"
        CREDIT_NOTE = "credit_note", "Credit note"
        PAYMENT_PLAN = "payment_plan", "Payment plan"
        STATEMENT = "statement", "Statement"
        AGREEMENT = "agreement", "Enrolment agreement"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PART_PAID = "part_paid", "Part paid"
        PAID = "paid", "Paid"
        ACCEPTED = "accepted", "Accepted"
        CANCELLED = "cancelled", "Cancelled"

    ISSUED_STATES = ["issued", "part_paid", "paid", "accepted"]

    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    number = models.CharField(max_length=30, blank=True, db_index=True)
    family = models.ForeignKey("families.Family", on_delete=models.PROTECT, related_name="documents")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True)
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    period = models.CharField(max_length=7, blank=True, help_text="Month the invoice is for, yyyy-mm.")
    currency = CurrencyField()
    total = MoneyField(default=Decimal("0"))
    notes = models.TextField(blank=True)
    related = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
                                help_text="Quotation → invoice; credit note or plan → its invoice.")
    payment = models.OneToOneField("Payment", null=True, blank=True, on_delete=models.PROTECT, related_name="receipt")
    verify_code = models.CharField(max_length=16, unique=True, default=_code)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    amended_reason = models.TextField(blank=True)
    is_draft_text = models.BooleanField(default=False, help_text="Legal wording that still needs the owner and a lawyer.")

    class Meta:
        ordering = ["-issue_date", "-id"]

    def __str__(self):
        return f"{self.get_kind_display()} {self.number or '(draft)'}"

    @property
    def is_locked(self):
        return self.status != self.Status.DRAFT

    def paid_amount(self):
        return self.allocations.filter(payment__reversed_at__isnull=True).aggregate(s=Sum("amount"))["s"] or Decimal("0")

    def credited_amount(self):
        return self.children.filter(kind=self.Kind.CREDIT_NOTE, status__in=self.ISSUED_STATES).aggregate(
            s=Sum("total"))["s"] or Decimal("0")

    def outstanding(self):
        if self.kind != self.Kind.INVOICE or self.status in (self.Status.DRAFT, self.Status.CANCELLED):
            return Decimal("0")
        return max(self.total - self.paid_amount() - self.credited_amount(), Decimal("0"))


class Line(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("catalogue.CatalogueItem", null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = MoneyField()
    student = models.ForeignKey("families.Student", null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def amount(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))


class Installment(models.Model):
    plan = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="installments")
    due_date = models.DateField()
    amount = MoneyField()

    class Meta:
        ordering = ["due_date"]


class Payment(TimeStamped):
    class Method(models.TextChoices):
        MUKURU = "mukuru", "Mukuru"
        ECOCASH = "ecocash", "EcoCash Diaspora"
        WESTERN_UNION = "western_union", "Western Union"
        BANK = "bank", "Bank transfer"
        CASH = "cash", "Cash"
        CARD = "card", "Card (online)"

    family = models.ForeignKey("families.Family", on_delete=models.PROTECT, related_name="payments")
    amount = MoneyField()
    currency = CurrencyField()
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=80, blank=True)
    received_on = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    note = models.CharField(max_length=200, blank=True)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    reversed_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-received_on", "-id"]

    def allocated(self):
        return self.allocations.aggregate(s=Sum("amount"))["s"] or Decimal("0")

    def unallocated(self):
        return Decimal("0") if self.reversed_at else self.amount - self.allocated()

    def __str__(self):
        return f"{self.currency} {self.amount} from {self.family} ({self.get_method_display()})"


class Allocation(models.Model):
    """Which invoice a payment settles. Without these nobody can say what was paid for."""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
    invoice = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="allocations")
    amount = MoneyField()
