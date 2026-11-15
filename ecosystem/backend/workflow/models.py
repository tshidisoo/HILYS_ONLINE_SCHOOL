import secrets

from django.conf import settings
from django.db import models

from common.models import TimeStamped


def _token():
    return secrets.token_urlsafe(16)


class Task(TimeStamped):
    class Status(models.TextChoices):
        OPEN = "open", "To do"
        DOING = "doing", "Doing"
        DONE = "done", "Done"

    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    due_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    link_type = models.CharField(max_length=30, blank=True)
    link_id = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["status", "due_on"]


class Feedback(TimeStamped):
    """A survey link per family at the end of a book or a term. Answers are for leadership only."""
    family = models.ForeignKey("families.Family", on_delete=models.CASCADE, related_name="feedback")
    token = models.CharField(max_length=40, unique=True, default=_token)
    reason = models.CharField(max_length=120, default="End of Book 1")
    sent_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)
    best = models.TextField(blank=True)
    improve = models.TextField(blank=True)
    may_quote = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=300, blank=True)
    link = models.CharField(max_length=200, blank=True, help_text="Screen path with ?open=<id>")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    key = models.CharField(max_length=80, blank=True, db_index=True, help_text="Stops the same reminder twice.")

    class Meta:
        ordering = ["-created_at"]
