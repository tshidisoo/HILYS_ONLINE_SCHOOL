from django.db import models

from common.models import TimeStamped


class SiteContent(TimeStamped):
    """Website content the owner changes without a developer: announcements, testimonials, FAQs."""

    class Kind(models.TextChoices):
        ANNOUNCEMENT = "announcement", "Announcement"
        TESTIMONIAL = "testimonial", "Parent review"
        FAQ = "faq", "Question and answer"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.CharField(max_length=120, blank=True, help_text="For reviews: first name and city, with permission.")
    is_published = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["kind", "sort_order"]
