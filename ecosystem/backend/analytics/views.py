"""Home: what each role should do today. Analytics: the few numbers that matter, with targets."""
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from billing.models import Document, Payment
from common.business_time import business_tz, now_local, today
from common.permissions import IsInternalStaff
from enrolments.models import Enrolment
from families.models import Family, Message
from leads.models import Lead
from lessons.models import Lesson
from workflow.models import Task


def card(key, title, count, link, tone="neutral", note=""):
    return {"key": key, "title": title, "count": count, "link": link, "tone": tone, "note": note}


@api_view(["GET"])
@permission_classes([IsInternalStaff])
def home(request):
    u, now, d = request.user, timezone.now(), today()
    tz = business_tz()
    day_start = timezone.datetime.combine(d, timezone.datetime.min.time(), tzinfo=tz)
    open_leads = Lead.objects.exclude(status__in=[Lead.Status.CONVERTED, Lead.Status.DISMISSED])
    late_leads = open_leads.filter(first_reply_at__isnull=True, reply_due_at__lt=now)
    overdue = Document.objects.filter(kind="invoice", status__in=["issued", "part_paid"], due_date__lt=d)
    unreported = Lesson.objects.filter(status=Lesson.Status.SCHEDULED, starts_at__lt=now - timedelta(minutes=30))
    todays = Lesson.objects.filter(starts_at__gte=day_start, starts_at__lt=day_start + timedelta(days=1)).exclude(status="moved")
    cards = []
    if u.role in ("owner", "coordinator"):
        cards += [
            card("late_leads", "Leads waiting too long for a reply", late_leads.count(), "/leads?clock=late", "bad" if late_leads.exists() else "good"),
            card("new_leads", "New since yesterday", open_leads.filter(created_at__gte=now - timedelta(days=1)).count(), "/leads?status=new"),
            card("cleanup", "Need cleanup", Lead.objects.filter(needs_cleanup=True).exclude(status="dismissed").count()
                 + Family.objects.filter(needs_cleanup=True).count(), "/leads?needs_cleanup=true", "warn"),
            card("trials", "Trials to turn into families", Lead.objects.filter(status=Lead.Status.TRIAL_DONE).count(), "/leads?status=trial_done", "warn"),
            card("waiting", "Children waiting to start", Enrolment.objects.filter(stage="waiting").count(), "/enrolments?stage=waiting"),
            card("unreported", "Past lessons not reported by the teacher", unreported.count(), "/lessons?unreported=1", "warn" if unreported.exists() else "good"),
            card("makeups", "Make-up lessons owed", Lesson.objects.filter(makeup_owed=True).count(), "/lessons?makeup_owed=true", "warn"),
            card("messages", "Unread messages from families", Message.objects.filter(read_by_staff=False).count(), "/families", "warn"),
        ]
    if u.role in ("owner", "finance"):
        unmatched = sum(1 for p in Payment.objects.filter(reversed_at__isnull=True) if p.unallocated() > 0)
        drafts = Document.objects.filter(kind="invoice", status="draft").count()
        cards += [
            card("overdue", "Overdue invoices", overdue.count(), "/documents?overdue=1", "bad" if overdue.exists() else "good"),
            card("drafts", "Draft invoices to check and issue", drafts, "/documents?kind=invoice&status=draft", "warn" if drafts else "good"),
            card("unmatched", "Payments not matched to an invoice", unmatched, "/payments?unmatched=1", "warn" if unmatched else "good"),
        ]
    tasks = Task.objects.filter(assignee=u).exclude(status="done")
    cards.append(card("tasks", "My tasks due today or late", tasks.filter(due_on__lte=d).count(), "/tasks?mine=1", "warn"))

    owed = defaultdict(Decimal)
    for inv in Document.objects.filter(kind="invoice", status__in=["issued", "part_paid"]):
        owed[inv.currency] += inv.outstanding()
    month_in = defaultdict(Decimal)
    for p in Payment.objects.filter(reversed_at__isnull=True, received_on__year=d.year, received_on__month=d.month):
        month_in[p.currency] += p.amount
    numbers = [
        {"label": "Children learning now", "value": Enrolment.objects.filter(stage="active").values("student").distinct().count()},
        {"label": "Lessons today (Harare time)", "value": todays.count()},
        {"label": "Received this month", "value": ", ".join(f"{c} {v:,.2f}" for c, v in month_in.items()) or "USD 0.00", "hide": u.role == "coordinator"},
        {"label": "Owed to HILYS", "value": ", ".join(f"{c} {v:,.2f}" for c, v in owed.items()) or "USD 0.00", "hide": u.role == "coordinator"},
    ]
    from lessons.views import LessonSerializer
    return Response({
        "greeting": f"{'Good morning' if now_local().hour < 12 else 'Good afternoon' if now_local().hour < 17 else 'Good evening'}, {u.first_name or u.username}",
        "date": d, "cards": cards, "numbers": [n for n in numbers if not n.get("hide")],
        "today": LessonSerializer(todays.select_related("enrolment__student__family", "teacher", "lead", "unit")[:20], many=True).data,
    })


@api_view(["GET"])
@permission_classes([IsInternalStaff])
def company(request):
    d = today()
    since = d - timedelta(days=180)
    leads = Lead.objects.filter(created_at__date__gte=since)
    by_source = Counter(leads.values_list("source", flat=True))
    converted = leads.filter(status=Lead.Status.CONVERTED).count()
    revenue = defaultdict(lambda: defaultdict(Decimal))
    for p in Payment.objects.filter(reversed_at__isnull=True, received_on__gte=since):
        revenue[p.currency][p.received_on.strftime("%Y-%m")] += p.amount
    by_package = defaultdict(int)
    for e in Enrolment.objects.filter(stage="active").select_related("package"):
        by_package[e.package.name if e.package else "No package"] += 1
    taught = Lesson.objects.filter(starts_at__date__gte=d - timedelta(days=30)).values("status").annotate(n=Count("id"))
    returning = Family.objects.annotate(n=Count("documents")).filter(n__gte=3).count()
    kpis = [
        {"label": "Leads answered within one working day", "target": 90, "unit": "%",
         "actual": _pct(leads.filter(first_reply_at__isnull=False, first_reply_at__lte=models_f("reply_due_at")).count(), leads.exclude(status="dismissed").count())},
        {"label": "Leads that became families", "target": 40, "unit": "%", "actual": _pct(converted, leads.count())},
        {"label": "Lessons reported within a day", "target": 95, "unit": "%", "actual": _reported_pct()},
        {"label": "Invoices paid by their due date", "target": 85, "unit": "%", "actual": _on_time_pct()},
    ]
    for k in kpis:
        k["status"] = "good" if k["actual"] is not None and k["actual"] >= k["target"] else "warn" if k["actual"] is not None and k["actual"] >= k["target"] * 0.75 else "bad" if k["actual"] is not None else "none"
    return Response({
        "kpis": kpis,
        "leads_by_source": [{"source": s, "count": n} for s, n in by_source.most_common()],
        "conversion": {"leads": leads.count(), "families": converted},
        "revenue_by_month": {c: [{"month": m, "amount": v} for m, v in sorted(rows.items())] for c, rows in revenue.items()},
        "children_by_package": [{"package": k, "count": v} for k, v in sorted(by_package.items(), key=lambda x: -x[1])],
        "work_by_stage": list(Enrolment.objects.values("stage").annotate(n=Count("id")).order_by("stage")),
        "lessons_last_30_days": list(taught),
        "returning_families": returning,
    })


def models_f(name):
    from django.db.models import F
    return F(name)


def _pct(a, b):
    return round(100 * a / b) if b else None


def _reported_pct():
    qs = Lesson.objects.exclude(status=Lesson.Status.SCHEDULED).filter(reported_at__isnull=False, starts_at__date__gte=today() - timedelta(days=60))
    on_time = sum(1 for ls in qs.only("starts_at", "reported_at") if ls.reported_at - ls.starts_at <= timedelta(days=1))
    return _pct(on_time, qs.count())


def _on_time_pct():
    paid = Document.objects.filter(kind="invoice", status="paid", due_date__isnull=False)
    on_time = 0
    for inv in paid.prefetch_related("allocations__payment"):
        last = max((a.payment.received_on for a in inv.allocations.all() if not a.payment.reversed_at), default=None)
        on_time += bool(last and last <= inv.due_date)
    return _pct(on_time, paid.count())
