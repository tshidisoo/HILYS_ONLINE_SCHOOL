from django.conf import settings
from django.db import models

from common.models import SoftDeletable


class Enrolment(SoftDeletable):
    """The unit of work: one child learning with one teacher on one package."""

    class Stage(models.TextChoices):
        TRIAL = "trial", "Trial"
        WAITING = "waiting", "Waiting to start"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        FINISHED = "finished", "Finished"
        STOPPED = "stopped", "Stopped"

    student = models.ForeignKey("families.Student", on_delete=models.CASCADE, related_name="enrolments")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="enrolments_taught")
    package = models.ForeignKey("catalogue.CatalogueItem", null=True, blank=True, on_delete=models.PROTECT)
    book = models.ForeignKey("curriculum.Book", null=True, blank=True, on_delete=models.PROTECT)
    level = models.CharField(max_length=20, blank=True)
    group_name = models.CharField(max_length=60, blank=True, help_text="Children sharing a group lesson share this name.")
    weekly_slots = models.JSONField(default=list, blank=True,
                                    help_text='Lesson times in Harare time: [{"weekday": 1, "time": "17:30"}]')
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.TRIAL, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    lead = models.ForeignKey("leads.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="enrolments")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} – {self.get_stage_display()}"


class StageChange(models.Model):
    enrolment = models.ForeignKey(Enrolment, on_delete=models.CASCADE, related_name="history")
    from_stage = models.CharField(max_length=20, blank=True)
    to_stage = models.CharField(max_length=20)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-at"]
