from django.conf import settings
from django.db import models

from common.models import TimeStamped


class Lesson(TimeStamped):
    class Kind(models.TextChoices):
        TRIAL = "trial", "Free trial"
        REGULAR = "regular", "Lesson"
        MAKEUP = "makeup", "Make-up lesson"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        TAUGHT = "taught", "Taught"
        MOVED = "moved", "Moved (24h notice)"
        MISSED = "missed", "Missed (counts as used)"
        CANCELLED = "cancelled", "Cancelled by HILYS"
        CUT_SHORT = "cut_short", "Cut short (power or internet)"

    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.REGULAR)
    enrolment = models.ForeignKey("enrolments.Enrolment", null=True, blank=True, on_delete=models.CASCADE,
                                  related_name="lessons")
    lead = models.ForeignKey("leads.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="trial_lessons")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lessons_taught")
    starts_at = models.DateTimeField(db_index=True)
    minutes = models.PositiveSmallIntegerField(default=30)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    unit = models.ForeignKey("curriculum.Unit", null=True, blank=True, on_delete=models.SET_NULL)
    parent_note = models.TextField(blank=True, help_text="Shown to the family.")
    private_note = models.TextField(blank=True, help_text="Only HILYS staff and the teacher see this.")
    reported_at = models.DateTimeField(null=True, blank=True)
    makeup_owed = models.BooleanField(default=False)
    makeup_for = models.OneToOneField("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="makeup")
    trial_level = models.CharField(max_length=20, blank=True, help_text="Level the teacher found in a trial.")

    class Meta:
        ordering = ["starts_at"]

    @property
    def is_group(self):
        return bool(self.enrolment and self.enrolment.package and self.enrolment.package.lesson_type == "group")

    def __str__(self):
        who = self.enrolment.student if self.enrolment else self.lead
        return f"{self.get_kind_display()} with {who} at {self.starts_at:%Y-%m-%d %H:%M} UTC"
