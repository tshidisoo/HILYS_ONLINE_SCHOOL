from celery import shared_task
from django.utils import timezone

from billing.models import Document
from common.business_time import today
from leads.models import Lead

from .notify import notify, staff


@shared_task
def remind_late_leads():
    n = 0
    for lead in Lead.objects.filter(status=Lead.Status.NEW, first_reply_at__isnull=True, reply_due_at__lt=timezone.now()):
        to = [lead.owner] if lead.owner else staff("owner", "coordinator")
        n += notify(to, f"Late reply: {lead}", "This lead has waited more than one working day.",
                    f"/leads?open={lead.pk}", key=f"late-lead-{lead.pk}")
    return n


@shared_task
def remind_overdue_invoices():
    n = 0
    for inv in Document.objects.filter(kind="invoice", status__in=["issued", "part_paid"], due_date__lt=today()):
        n += notify(staff("owner", "finance"), f"Overdue: {inv.number}", f"{inv.family} owes {inv.currency} {inv.outstanding()}",
                    f"/documents?open={inv.pk}", key=f"overdue-{inv.pk}-{today():%Y-%m-%d}")
    return n


@shared_task
def remind_expiring_quotes():
    n = 0
    soon = today().toordinal() + 2
    for q in Document.objects.filter(kind="quotation", status="issued", due_date__isnull=False):
        if q.due_date.toordinal() <= soon:
            n += notify(staff("owner", "coordinator"), f"Quotation ending: {q.number}", f"For {q.family}",
                        f"/documents?open={q.pk}", key=f"quote-{q.pk}")
    return n
