from django.conf import settings
from django.db import models

from common.fields import EncryptedTextField
from common.models import SoftDeletable


class Family(SoftDeletable):
    """The customer: the parent who pays, and the children who learn."""
    parent_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=80, blank=True)
    time_zone = models.CharField(max_length=64, default="Europe/London")
    payer_name = models.CharField(max_length=120, blank=True, help_text="If someone else pays, e.g. a grandparent.")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="owned_families")
    login = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="family")
    tags = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    founding_family = models.BooleanField(default=False)
    needs_cleanup = models.BooleanField(default=False, db_index=True)
    cleanup_reasons = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["parent_name"]
        verbose_name_plural = "families"

    def __str__(self):
        return self.parent_name


class Student(SoftDeletable):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        CONVERSATION = "conversation", "Conversation"
        UNKNOWN = "", "Not checked yet"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="students")
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)
    # Sensitive: encrypted, and opening a record that has one is logged.
    support_notes = EncryptedTextField(blank=True, help_text="Learning needs or health notes the teacher should know.")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["first_name"]

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.name


class Message(models.Model):
    """Messages between a family and HILYS (staff or the child's teacher)."""
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_by_family = models.BooleanField(default=False)
    read_by_staff = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
