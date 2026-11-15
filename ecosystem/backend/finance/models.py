from django.conf import settings
from django.db import models

from common.models import CurrencyField, MoneyField, TimeStamped


class Account(models.Model):
    class Kind(models.TextChoices):
        BANK = "bank", "Bank"
        CASH = "cash", "Cash"
        MOBILE = "mobile", "Mobile money / remittance"

    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    currency = CurrencyField()
    payment_methods = models.JSONField(default=list, blank=True, help_text="Payment methods that land in this account.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Entry(TimeStamped):
    """Money in, money out and transfers. Finance here is cash flow, not bookkeeping."""

    class Kind(models.TextChoices):
        INCOME = "income", "Money in"
        EXPENSE = "expense", "Money out"
        TRANSFER_OUT = "transfer_out", "Transfer out"
        TRANSFER_IN = "transfer_in", "Transfer in"

    CATEGORIES = ["Lesson fees", "Course fees", "Teacher pay", "Internet and data", "Software", "Marketing",
                  "Transfer fees", "Equipment", "Printing", "Other"]

    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="entries")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    amount = MoneyField()
    currency = CurrencyField()
    category = models.CharField(max_length=40, default="Other")
    on_date = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    receipt_photo = models.FileField(upload_to="private/expenses/", blank=True)
    payment = models.ForeignKey("billing.Payment", null=True, blank=True, on_delete=models.SET_NULL, related_name="entries")
    pay_statement = models.ForeignKey("teacherpay.PayStatement", null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name="entries")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-on_date", "-id"]
