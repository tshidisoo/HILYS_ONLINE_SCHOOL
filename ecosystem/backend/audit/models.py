from django.conf import settings
from django.db import models


class AuditEntry(models.Model):
    """Who did what to which record. Leadership can read it; nobody can edit it."""
    at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=40)
    object_type = models.CharField(max_length=60)
    object_id = models.CharField(max_length=40)
    summary = models.CharField(max_length=300)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-at"]
        verbose_name_plural = "audit entries"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Audit entries cannot be changed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit entries cannot be deleted.")
