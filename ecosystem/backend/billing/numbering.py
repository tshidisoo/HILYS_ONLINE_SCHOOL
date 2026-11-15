from django.db import transaction

from settings_app.models import CompanySettings

from .models import NumberSequence


@transaction.atomic
def next_number(kind, year):
    """Gapless: the sequence row is locked, so two people issuing at once get consecutive numbers."""
    seq, _ = NumberSequence.objects.get_or_create(kind=kind, year=year)
    seq = NumberSequence.objects.select_for_update().get(pk=seq.pk)
    seq.last += 1
    seq.save(update_fields=["last"])
    prefix = getattr(CompanySettings.get(), f"{kind}_prefix", kind[:3].upper())
    return f"{prefix}-{year}-{seq.last:04d}"
