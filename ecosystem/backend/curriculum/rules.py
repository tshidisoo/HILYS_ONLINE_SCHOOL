from django.db import transaction

from billing.numbering import next_number
from common.business_time import today
from common.errors import RuleBroken

from .models import BookCheck, Certificate


def result_for(score):
    """Pass rule from docs/curriculum/book1-assessment.md (a draft for Sija to adjust)."""
    if score >= 5:
        return BookCheck.Result.CERTIFICATE
    if score >= 3:
        return BookCheck.Result.CERTIFICATE_WITH_PRACTICE
    return BookCheck.Result.REPEAT


@transaction.atomic
def record_check(student, book, teacher, parts, checked_on=None, practice_notes="", is_demo=False):
    if len(parts) != 6 or not all(isinstance(p, bool) for p in parts):
        raise RuleBroken("Tick or untick each of the six parts.", "parts")
    score = sum(parts)
    check = BookCheck.objects.create(student=student, book=book, teacher=teacher, parts=parts, score=score,
                                     result=result_for(score), checked_on=checked_on or today(),
                                     practice_notes=practice_notes, is_demo=is_demo)
    if check.result != BookCheck.Result.REPEAT:
        Certificate.objects.create(student=student, book=book, book_check=check, issued_on=check.checked_on,
                                   number=next_number("certificate", check.checked_on.year), is_demo=is_demo)
    return check


def progress(student, book):
    """Which units of the book this child has been taught (from reported lessons)."""
    from lessons.models import Lesson
    done = set(Lesson.objects.filter(enrolment__student=student, unit__book=book, status=Lesson.Status.TAUGHT)
               .values_list("unit__number", flat=True))
    units = list(book.units.all())
    return {"book": book.title, "total": len(units), "done": len(done),
            "units": [{"number": u.number, "title_nd": u.title_nd, "title_en": u.title_en,
                       "culture": u.culture, "done": u.number in done} for u in units]}
