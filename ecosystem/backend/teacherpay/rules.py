from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from audit.log import record
from common.business_time import month_bounds, today
from common.errors import RuleBroken
from lessons.models import Lesson
from lessons.rules import COUNTS_FOR_PAY

from .models import PayStatement


def build(teacher, year, month):
    """(Re)builds a draft statement. A lesson counts only once the teacher has reported it."""
    key = f"{year}-{month:02d}"
    st, _ = PayStatement.objects.get_or_create(teacher=teacher, month=key,
                                               defaults={"currency": teacher.teacher_profile.pay_currency})
    if st.status != PayStatement.Status.DRAFT:
        return st
    start, end = month_bounds(year, month)
    lessons = Lesson.objects.filter(teacher=teacher, starts_at__gte=start, starts_at__lt=end).select_related(
        "enrolment__student", "enrolment__package", "lead")
    prof = teacher.teacher_profile
    lines, total, unreported = [], Decimal("0"), 0
    for ls in lessons:
        if ls.status == Lesson.Status.SCHEDULED:
            if ls.starts_at < timezone.now():
                unreported += 1
            continue
        if ls.status not in COUNTS_FOR_PAY or ls.reported_at is None:
            continue
        rate = prof.pay_group if ls.is_group else prof.pay_one_to_one
        who = str(ls.enrolment.student) if ls.enrolment else (str(ls.lead) if ls.lead else "")
        lines.append({"lesson": ls.pk, "date": ls.starts_at.date().isoformat(), "who": who,
                      "kind": ls.get_kind_display(), "status": ls.get_status_display(), "rate": str(rate)})
        total += rate
    st.lines, st.total, st.unreported, st.currency = lines, total, unreported, prof.pay_currency
    st.save()
    return st


def approve(st, user):
    if not user.can_record_payments:
        raise RuleBroken("Only finance and the owner approve teacher pay.", "detail")
    if st.unreported:
        raise RuleBroken(f"{st.unreported} past lessons are not reported yet. Ask the teacher to report them first.", "detail")
    st.status, st.approved_by = PayStatement.Status.APPROVED, user
    st.save()
    record(user, "approve", st, f"Approved pay for {st.teacher} {st.month}: {st.currency} {st.total}")
    return st


@transaction.atomic
def mark_paid(st, user, account, paid_on=None):
    from finance.models import Entry
    if not user.can_record_payments:
        raise RuleBroken("Only finance and the owner pay teachers.", "detail")
    if st.status != PayStatement.Status.APPROVED:
        raise RuleBroken("Approve the statement first.", "detail")
    if account.currency != st.currency:
        raise RuleBroken("Pay from an account in the same currency.", "account")
    st.status, st.paid_on = PayStatement.Status.PAID, paid_on or today()
    st.save()
    Entry.objects.create(account=account, kind=Entry.Kind.EXPENSE, amount=st.total, currency=st.currency,
                         category="Teacher pay", on_date=st.paid_on, note=f"{st.teacher} {st.month}",
                         pay_statement=st, recorded_by=user, is_demo=st.is_demo)
    record(user, "payment", st, f"Paid {st.teacher} {st.currency} {st.total} for {st.month}")
    return st
