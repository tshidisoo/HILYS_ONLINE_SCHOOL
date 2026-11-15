"""Lesson rules: reporting, make-ups, what counts for pay, and the monthly timetable."""
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from audit.log import record
from common.business_time import business_tz, month_bounds
from common.errors import RuleBroken

from .models import Lesson

S = Lesson.Status
OWES_MAKEUP = {S.CANCELLED, S.CUT_SHORT}
COUNTS_FOR_PAY = {S.TAUGHT, S.MISSED}  # missed-without-notice still counts as a used lesson


def report(lesson, user, status, parent_note="", private_note="", unit=None, trial_level=""):
    """A teacher reports a lesson. Only its own teacher (or staff) may; the report is needed before pay."""
    if user.is_teacher and lesson.teacher_id != user.pk:
        raise RuleBroken("This is not your lesson.", "detail")
    if status not in S.values or status == S.SCHEDULED:
        raise RuleBroken("Choose what happened in the lesson.", "status")
    if lesson.starts_at > timezone.now() + timedelta(minutes=lesson.minutes) and status in (S.TAUGHT, S.MISSED, S.CUT_SHORT):
        raise RuleBroken("This lesson has not happened yet.", "status")
    if status == S.TAUGHT and not (parent_note or "").strip():
        raise RuleBroken("Write a short note for the parent: what the child learned or practised.", "parent_note")
    if lesson.kind == Lesson.Kind.TRIAL and status == S.TAUGHT and not trial_level:
        raise RuleBroken("Choose the level you found in the trial.", "trial_level")
    lesson.status = status
    lesson.parent_note = parent_note or ""
    lesson.private_note = private_note or ""
    if unit is not None:
        lesson.unit = unit
    lesson.makeup_owed = status in OWES_MAKEUP
    lesson.trial_level = trial_level or lesson.trial_level
    lesson.reported_at = timezone.now()
    lesson.save()
    if lesson.kind == Lesson.Kind.TRIAL and lesson.lead_id and status == S.TAUGHT:
        from leads.models import Lead
        Lead.objects.filter(pk=lesson.lead_id).update(status=Lead.Status.TRIAL_DONE, suggested_level=trial_level)
    record(user, "lesson", lesson, f"Reported {lesson}: {S(status).label}")
    return lesson


def book_makeup(lesson, starts_at, user):
    if not lesson.makeup_owed:
        raise RuleBroken("This lesson does not owe a make-up.", "detail")
    if hasattr(lesson, "makeup") and lesson.makeup:
        raise RuleBroken("A make-up is already booked for this lesson.", "detail")
    m = Lesson.objects.create(kind=Lesson.Kind.MAKEUP, enrolment=lesson.enrolment, teacher=lesson.teacher,
                              starts_at=starts_at, minutes=lesson.minutes, makeup_for=lesson, is_demo=lesson.is_demo)
    lesson.makeup_owed = False
    lesson.save(update_fields=["makeup_owed", "updated_at"])
    record(user, "lesson", m, f"Booked make-up for {lesson}")
    return m


@transaction.atomic
def schedule_month(enrolment, year, month):
    """Creates the month's lessons from the weekly times. Safe to run twice."""
    if enrolment.stage != enrolment.Stage.ACTIVE or not enrolment.teacher_id:
        return 0
    start, end = month_bounds(year, month)
    tz = business_tz()
    made, day = 0, start.date()
    while day < end.date():
        for slot in enrolment.weekly_slots:
            if day.weekday() != slot["weekday"]:
                continue
            h, m = (int(x) for x in slot["time"].split(":"))
            at = datetime.combine(day, time(h, m), tzinfo=tz)
            if enrolment.start_date and day < enrolment.start_date:
                continue
            _, created = Lesson.objects.get_or_create(
                enrolment=enrolment, starts_at=at, kind=Lesson.Kind.REGULAR,
                defaults={"teacher_id": enrolment.teacher_id, "is_demo": enrolment.is_demo})
            made += created
        day += timedelta(days=1)
    return made


def next_unit(enrolment):
    """The next Book unit this child has not been taught."""
    if not enrolment.book_id:
        return None
    done = set(Lesson.objects.filter(enrolment__student=enrolment.student, status=S.TAUGHT, unit__isnull=False)
               .values_list("unit_id", flat=True))
    return enrolment.book.units.exclude(pk__in=done).first()
