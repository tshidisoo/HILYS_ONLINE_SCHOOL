from django.conf import settings
from django.db import models

from common.models import SoftDeletable


class Lead(SoftDeletable):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        TRIAL_BOOKED = "trial_booked", "Trial booked"
        TRIAL_DONE = "trial_done", "Trial done"
        CONVERTED = "converted", "Became a family"
        DISMISSED = "dismissed", "Dismissed"

    class Interest(models.TextChoices):
        LIVE = "live", "Live lessons"
        VIDEO = "video", "Video course"
        PLUS = "plus", "HILYS Plus"
        NOT_SURE = "not_sure", "Not sure yet"

    parent_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="Two-letter country code, e.g. GB")
    time_zone = models.CharField(max_length=64, blank=True)
    child_name = models.CharField(max_length=120, blank=True)
    child_age = models.PositiveSmallIntegerField(null=True, blank=True)
    interest = models.CharField(max_length=20, choices=Interest.choices, default=Interest.LIVE)
    suggested_level = models.CharField(max_length=40, blank=True, help_text="From the website level check.")
    message = models.TextField(blank=True)
    source = models.CharField(max_length=40, default="Website")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="owned_leads")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    notes = models.TextField(blank=True)
    reply_due_at = models.DateTimeField(null=True, blank=True)
    first_reply_at = models.DateTimeField(null=True, blank=True)
    follow_ups = models.JSONField(default=list, blank=True, help_text="Ticked follow-ups: [{at, by, note}]")
    dismissed_reason = models.CharField(max_length=200, blank=True)
    needs_cleanup = models.BooleanField(default=False, db_index=True)
    cleanup_reasons = models.JSONField(default=list, blank=True)
    family = models.ForeignKey("families.Family", null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.parent_name or self.email or self.phone or f"Lead {self.pk}"
