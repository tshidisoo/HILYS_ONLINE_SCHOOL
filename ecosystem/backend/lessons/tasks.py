from celery import shared_task

from common.business_time import today
from enrolments.models import Enrolment

from .rules import schedule_month


@shared_task
def schedule_next_month():
    """From the 20th, make sure next month's lessons exist for every active enrolment."""
    d = today()
    if d.day < 20:
        return 0
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return sum(schedule_month(e, year, month) for e in Enrolment.objects.filter(stage=Enrolment.Stage.ACTIVE))
