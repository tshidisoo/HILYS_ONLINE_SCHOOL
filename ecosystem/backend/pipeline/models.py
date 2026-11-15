from django.conf import settings
from django.db import models

from common.models import CurrencyField, MoneyField, SoftDeletable


class Opportunity(SoftDeletable):
    """Larger deals: a family with several children, an association, a heritage school."""

    class Stage(models.TextChoices):
        TALKING = "talking", "Talking"
        TRIAL = "trial", "Trial or pilot"
        OFFER = "offer", "Offer sent"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    DEFAULT_CHANCE = {"talking": 20, "trial": 50, "offer": 70, "won": 100, "lost": 0}

    title = models.CharField(max_length=160)
    family = models.ForeignKey("families.Family", null=True, blank=True, on_delete=models.SET_NULL)
    lead = models.ForeignKey("leads.Lead", null=True, blank=True, on_delete=models.SET_NULL)
    organisation = models.CharField(max_length=120, blank=True, help_text="An organisation not yet on record.")
    stage = models.CharField(max_length=10, choices=Stage.choices, default=Stage.TALKING)
    chance = models.PositiveSmallIntegerField(default=20)
    value = MoneyField(default=0)
    currency = CurrencyField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    expected_close = models.DateField(null=True, blank=True)
    closed_on = models.DateField(null=True, blank=True)
    lost_to = models.CharField(max_length=120, blank=True)
    lost_reason = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "opportunities"

    @property
    def weighted_value(self):
        return (self.value * self.chance / 100).quantize(self.value.__class__("0.01"))
