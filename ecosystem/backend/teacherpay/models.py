from django.conf import settings
from django.db import models

from common.models import CurrencyField, MoneyField, TimeStamped


class PayStatement(TimeStamped):
    """What a teacher is owed for a month: reported lessons that count, at their rates."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid"

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pay_statements")
    month = models.CharField(max_length=7)  # yyyy-mm
    currency = CurrencyField()
    lines = models.JSONField(default=list)
    total = MoneyField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    paid_on = models.DateField(null=True, blank=True)
    unreported = models.PositiveIntegerField(default=0, help_text="Past lessons with no report yet: not paid until reported.")

    class Meta:
        unique_together = [("teacher", "month")]
        ordering = ["-month", "teacher__first_name"]
