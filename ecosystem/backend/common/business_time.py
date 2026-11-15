"""The server runs in UTC; the business does not. Everything about "today" and working days uses Harare time."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

WORKING_DAYS = {0, 1, 2, 3, 4}  # Monday to Friday
DAY_START, DAY_END = time(8, 0), time(17, 0)


def business_tz():
    return ZoneInfo(settings.BUSINESS_TIME_ZONE)


def now_local():
    return timezone.now().astimezone(business_tz())


def today():
    return now_local().date()


def add_working_day(moment):
    """The reply clock: one working day after `moment`, in business time.

    A lead that arrives on Friday evening is due on Monday at the end of the day;
    one that arrives on Tuesday at 10:00 is due on Wednesday at 10:00.
    """
    local = moment.astimezone(business_tz())
    if local.weekday() not in WORKING_DAYS or local.time() >= DAY_END:
        # Starts counting at the next working morning.
        day = local.date() + timedelta(days=1)
        while day.weekday() not in WORKING_DAYS:
            day += timedelta(days=1)
        local = datetime.combine(day, DAY_START, tzinfo=business_tz())
    elif local.time() < DAY_START:
        local = datetime.combine(local.date(), DAY_START, tzinfo=business_tz())
    due_day = local.date() + timedelta(days=1)
    while due_day.weekday() not in WORKING_DAYS:
        due_day += timedelta(days=1)
    return datetime.combine(due_day, local.time(), tzinfo=business_tz())


def month_bounds(year, month):
    tz = business_tz()
    start = datetime(year, month, 1, tzinfo=tz)
    end = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=tz)
    return start, end
