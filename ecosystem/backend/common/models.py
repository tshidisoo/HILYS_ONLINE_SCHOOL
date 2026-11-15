"""Base pieces every record uses: timestamps, soft delete with a bin, and a demo flag."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_demo = models.BooleanField(default=False, help_text="Invented demo record; remove before going live.")

    class Meta:
        abstract = True


class AliveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeletable(TimeStamped):
    """People delete the wrong record. Deleting moves it to the bin; leadership can restore it."""
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="+")

    objects = AliveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by", "updated_at"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by", "updated_at"])


CURRENCIES = [("USD", "US dollar"), ("GBP", "Pound sterling"), ("ZAR", "South African rand")]


def MoneyField(**kwargs):
    """Money is exact: decimals, never floats."""
    return models.DecimalField(max_digits=12, decimal_places=2, **kwargs)


def CurrencyField(**kwargs):
    kwargs.setdefault("default", "USD")
    return models.CharField(max_length=3, choices=CURRENCIES, **kwargs)
