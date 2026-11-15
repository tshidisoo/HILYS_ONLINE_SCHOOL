from django.db import models

from common.models import CurrencyField, MoneyField, SoftDeletable


class CatalogueItem(SoftDeletable):
    """The price book is the only place a price is typed; documents pick from it."""

    class Kind(models.TextChoices):
        PACKAGE = "package", "Monthly lesson package"
        LESSON = "lesson", "Single lesson"
        COURSE = "course", "Video course"
        TRIAL = "trial", "Trial lesson"
        OTHER = "other", "Other"

    class LessonType(models.TextChoices):
        ONE_TO_ONE = "one_to_one", "One-to-one"
        GROUP = "group", "Group (up to 3)"
        NONE = "", "Not a lesson"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices, blank=True)
    lessons_per_week = models.PositiveSmallIntegerField(default=0)
    price = MoneyField()
    currency = CurrencyField()
    unit = models.CharField(max_length=30, default="per month")
    is_active = models.BooleanField(default=True)
    on_website = models.BooleanField(default=True)
    is_draft_price = models.BooleanField(default=True, help_text="Draft until the owner approves the price.")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    @property
    def lessons_per_month(self):
        return self.lessons_per_week * 4  # policy: a month counts as 4 lessons per weekly slot

    def __str__(self):
        return self.name
