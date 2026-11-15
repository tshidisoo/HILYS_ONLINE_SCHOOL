from django.contrib.auth.models import AbstractUser
from django.db import models

from common.models import CurrencyField, MoneyField


class User(AbstractUser):
    """One login per person. Several people may hold one role, and people cover for each other."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        COORDINATOR = "coordinator", "Coordinator"
        FINANCE = "finance", "Finance"
        TEACHER = "teacher", "Teacher"
        PARENT = "parent", "Parent"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COORDINATOR)
    phone = models.CharField(max_length=32, blank=True)
    time_zone = models.CharField(max_length=64, default="Africa/Harare")
    is_suspended = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)

    # Permission questions are answered here, never by comparing role strings in views.
    @property
    def is_internal_staff(self):
        return self.role in {self.Role.OWNER, self.Role.COORDINATOR, self.Role.FINANCE} and not self.is_suspended

    @property
    def is_leadership(self):
        return self.role == self.Role.OWNER and not self.is_suspended

    @property
    def can_record_payments(self):
        return self.role in {self.Role.OWNER, self.Role.FINANCE} and not self.is_suspended

    @property
    def can_issue_documents(self):
        return self.is_internal_staff

    @property
    def can_own_families(self):
        return self.is_internal_staff

    @property
    def can_override_rules(self):
        return self.is_leadership

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER and not self.is_suspended

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT and not self.is_suspended

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def __str__(self):
        return self.display_name


class TeacherProfile(models.Model):
    """Teachers are freelancers who see only their own students in the teacher portal."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    bio = models.TextField(blank=True)
    pay_one_to_one = MoneyField(default=6, help_text="Pay per taught one-to-one lesson (draft rate).")
    pay_group = MoneyField(default=8, help_text="Pay per taught group lesson (draft rate).")
    pay_currency = CurrencyField()
    zoom_link = models.URLField(blank=True)
    takes_new_students = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)
