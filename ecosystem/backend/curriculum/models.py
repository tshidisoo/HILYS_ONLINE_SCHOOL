import secrets

from django.conf import settings
from django.db import models

from common.models import TimeStamped


def _code():
    return secrets.token_hex(5).upper()


class Book(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g. book-1
    title = models.CharField(max_length=120)
    level = models.CharField(max_length=20, default="beginner")
    order = models.PositiveSmallIntegerField(default=1)
    is_ready = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Unit(models.Model):
    """One lesson of a book, imported from materials/book1/lessons.py."""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="units")
    number = models.PositiveSmallIntegerField()
    title_nd = models.CharField(max_length=120)
    title_en = models.CharField(max_length=120)
    kind = models.CharField(max_length=30)
    culture = models.CharField(max_length=120, blank=True)
    pages = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["book__order", "number"]
        unique_together = [("book", "number")]

    def __str__(self):
        return f"{self.book.title} lesson {self.number}: {self.title_nd}"


class BookCheck(TimeStamped):
    """The end-of-book spoken check (docs/curriculum/book1-assessment.md): six parts, ticked or not."""
    PARTS = ["Says the 5 vowels", "Reads syllables", "Makes the 3 clicks", "Reads 8 words",
             "Reads 3 sentences", "Talks a little"]

    class Result(models.TextChoices):
        CERTIFICATE = "certificate", "Certificate"
        CERTIFICATE_WITH_PRACTICE = "practice", "Certificate, with things to practise"
        REPEAT = "repeat", "Not yet: repeat lessons and try again"

    student = models.ForeignKey("families.Student", on_delete=models.CASCADE, related_name="book_checks")
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    checked_on = models.DateField()
    parts = models.JSONField(default=list, help_text="Six booleans, one per part.")
    score = models.PositiveSmallIntegerField(default=0)
    result = models.CharField(max_length=20, choices=Result.choices)
    practice_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-checked_on"]


class Certificate(TimeStamped):
    student = models.ForeignKey("families.Student", on_delete=models.PROTECT, related_name="certificates")
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    book_check = models.OneToOneField(BookCheck, on_delete=models.PROTECT, related_name="certificate")
    number = models.CharField(max_length=30, unique=True)
    issued_on = models.DateField()
    verify_code = models.CharField(max_length=16, unique=True, default=_code)

    class Meta:
        ordering = ["-issued_on"]
