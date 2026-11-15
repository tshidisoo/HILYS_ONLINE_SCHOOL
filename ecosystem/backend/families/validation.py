"""All rules for families and students. The website, app, teacher portal and staff screens all call these."""
from django.db.models import Q

from audit.log import record
from common.errors import RuleBroken
from common.phones import normalise_phone

from .models import Family


def flag(family):
    reasons = []
    if not family.email and not family.phone:
        reasons.append("No phone or email")
    if family.phone:
        family.phone, ok = normalise_phone(family.phone, family.country or None)
        if not ok:
            reasons.append("Phone number looks wrong")
    if family.whatsapp:
        family.whatsapp, _ = normalise_phone(family.whatsapp, family.country or None)
    family.email = (family.email or "").strip().lower()
    family.cleanup_reasons = reasons
    family.needs_cleanup = bool(reasons)
    return family


def find_duplicates(family, exclude_pk=None):
    """Returns (hard, soft): a matching email is a hard stop; a matching phone may be overridden."""
    qs = Family.objects.exclude(pk=exclude_pk) if exclude_pk else Family.objects.all()
    hard = list(qs.filter(email=family.email)) if family.email else []
    soft = list(qs.filter(Q(phone=family.phone) | Q(whatsapp=family.phone))) if family.phone else []
    return hard, [f for f in soft if f not in hard]


def save_family(family, user, override_reason="", from_outside=False):
    """Staff saves are checked for duplicates. Records from the website or app are never rejected, only flagged."""
    flag(family)
    hard, soft = find_duplicates(family, exclude_pk=family.pk)
    if from_outside:
        if hard or soft:
            family.needs_cleanup = True
            family.cleanup_reasons = family.cleanup_reasons + ["Might be a duplicate of an existing family"]
        family.save()
        return family
    if hard:
        raise RuleBroken(f"A family with this email already exists: {hard[0].parent_name}.", "email", "duplicate")
    if soft:
        if not override_reason.strip():
            raise RuleBroken(f"A family with this phone number already exists: {soft[0].parent_name}. "
                             "The owner can save it anyway with a reason.", "phone", "duplicate_phone")
        if not user.can_override_rules:
            raise RuleBroken("Only the owner can save a family whose phone matches another family.", "phone")
    is_new = family.pk is None
    family.save()
    if soft:
        record(user, "override", family, f"Saved {family} despite matching phone with {soft[0]}", override_reason)
    record(user, "create" if is_new else "update", family, f"{'Added' if is_new else 'Updated'} family {family}")
    return family
