"""Every rule for a lead lives here. The website, app and staff screens all call these."""
from django.utils import timezone

from common.business_time import add_working_day
from common.errors import RuleBroken
from common.phones import normalise_phone

from .models import Lead


def reply_clock(lead, now=None):
    """On time, due soon (under 3 hours left) or late. Stops once someone has replied."""
    if lead.first_reply_at or lead.status in (Lead.Status.CONVERTED, Lead.Status.DISMISSED) or not lead.reply_due_at:
        return "answered"
    now = now or timezone.now()
    left = (lead.reply_due_at - now).total_seconds()
    if left < 0:
        return "late"
    return "due_soon" if left < 3 * 3600 else "on_time"


def prepare(lead, received_at=None):
    """Normalise and flag a lead. Never rejects it: a lead that breaks a rule is saved under Needs cleanup."""
    reasons = []
    lead.parent_name = (lead.parent_name or "").strip()
    lead.email = (lead.email or "").strip().lower()
    if lead.phone:
        lead.phone, ok = normalise_phone(lead.phone, lead.country or None)
        if not ok:
            reasons.append("Phone number looks wrong")
    if not lead.phone and not lead.email:
        reasons.append("No phone or email: we cannot reply")
    if not lead.parent_name:
        reasons.append("No parent name")
    if lead.child_age is not None and not (3 <= lead.child_age <= 18):
        reasons.append("Child's age looks unusual")
    lead.cleanup_reasons = reasons
    lead.needs_cleanup = bool(reasons)
    if lead.reply_due_at is None:
        lead.reply_due_at = add_working_day(received_at or timezone.now())
    return lead


def create_lead(data, source, owner=None, is_demo=False, received_at=None):
    lead = Lead(source=source, owner=owner, is_demo=is_demo, **data)
    prepare(lead, received_at)
    lead.save()
    return lead


def mark_replied(lead, user, note=""):
    now = timezone.now()
    if not lead.first_reply_at:
        lead.first_reply_at = now
    lead.follow_ups = list(lead.follow_ups) + [{"at": now.isoformat(), "by": user.display_name, "note": note}]
    if lead.status == Lead.Status.NEW:
        lead.status = Lead.Status.CONTACTED
    lead.save()
    return lead


def dismiss(lead, reason):
    if not (reason or "").strip():
        raise RuleBroken("Say why the lead is being dismissed.", "reason")
    lead.status = Lead.Status.DISMISSED
    lead.dismissed_reason = reason.strip()
    lead.save()
    return lead
