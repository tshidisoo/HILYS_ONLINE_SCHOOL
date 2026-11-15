from django.conf import settings
from django.db import models

from common.models import TimeStamped


class DataRequest(TimeStamped):
    class Kind(models.TextChoices):
        SEE = "see", "See my data"
        DELETE = "delete", "Delete my data"
        CORRECT = "correct", "Correct my data"

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"
        REFUSED = "refused", "Refused (with reason)"

    family = models.ForeignKey("families.Family", null=True, blank=True, on_delete=models.SET_NULL, related_name="data_requests")
    requester = models.CharField(max_length=160)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    due_on = models.DateField(null=True, blank=True, help_text="Reply within one month.")
    notes = models.TextField(blank=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["status", "due_on"]


class SensitiveAccess(models.Model):
    """Opening a child's support notes is logged."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    student = models.ForeignKey("families.Student", on_delete=models.CASCADE, related_name="+")
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-at"]
