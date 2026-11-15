"""Stages and their gates. The only place these rules live."""
from audit.log import record
from common.errors import RuleBroken

from .models import Enrolment, StageChange

S = Enrolment.Stage
ALLOWED = {
    S.TRIAL: {S.WAITING, S.STOPPED},
    S.WAITING: {S.ACTIVE, S.STOPPED, S.TRIAL},
    S.ACTIVE: {S.PAUSED, S.FINISHED, S.STOPPED},
    S.PAUSED: {S.ACTIVE, S.STOPPED},
    S.FINISHED: {S.ACTIVE},
    S.STOPPED: {S.WAITING},
}
NEEDS_REASON = {S.PAUSED, S.STOPPED}


def gate_problems(enrolment, to):
    """What stops this enrolment moving to `to`. An empty list means it can move."""
    problems = []
    if to in (S.WAITING, S.ACTIVE):
        if not enrolment.level:
            problems.append("Set the child's level (from the trial lesson).")
        if not enrolment.teacher_id:
            problems.append("Choose a teacher.")
        if not enrolment.package_id:
            problems.append("Choose a package from the price book.")
    if to == S.ACTIVE:
        if not enrolment.weekly_slots:
            problems.append("Add the weekly lesson times.")
        from billing.models import Document
        if not Document.objects.filter(family=enrolment.student.family, kind=Document.Kind.INVOICE,
                                       status__in=Document.ISSUED_STATES).exists():
            problems.append("Issue the first month's invoice to the family.")
    if to == S.FINISHED and enrolment.book_id:
        from curriculum.models import BookCheck
        passed = BookCheck.objects.filter(student=enrolment.student, book=enrolment.book, score__gte=3).exists()
        if not passed:
            problems.append(f"Record an end-of-book check of 3 or more for {enrolment.book}.")
    return problems


def move(enrolment, to, user, reason=""):
    if to not in S.values:
        raise RuleBroken("That stage does not exist.", "stage")
    if to == enrolment.stage:
        return enrolment
    if to not in ALLOWED[enrolment.stage]:
        raise RuleBroken(f"An enrolment cannot go from {enrolment.get_stage_display()} to {S(to).label}.", "stage")
    if to in NEEDS_REASON and not reason.strip():
        raise RuleBroken("Say why.", "reason")
    problems = gate_problems(enrolment, to)
    if problems:
        raise RuleBroken("Not yet: " + " ".join(problems), "stage", "gate")
    StageChange.objects.create(enrolment=enrolment, from_stage=enrolment.stage, to_stage=to, by=user, reason=reason)
    enrolment.stage = to
    enrolment.save(update_fields=["stage", "updated_at"])
    record(user, "stage", enrolment, f"Moved {enrolment.student} to {S(to).label}", reason)
    return enrolment


def validate_slots(slots):
    for s in slots or []:
        if not isinstance(s, dict) or s.get("weekday") not in range(7) or not isinstance(s.get("time"), str):
            raise RuleBroken("Each lesson time needs a day and a time, like Tuesday 17:30.", "weekly_slots")
        h, _, m = s["time"].partition(":")
        if not (h.isdigit() and m.isdigit() and 0 <= int(h) < 24 and 0 <= int(m) < 60):
            raise RuleBroken(f"{s['time']} is not a time. Use 24-hour time, like 17:30.", "weekly_slots")
