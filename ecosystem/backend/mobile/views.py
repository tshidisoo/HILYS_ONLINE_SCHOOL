"""Endpoints for the parent app. A parent sees only their own family, everywhere."""
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from billing.models import Document
from billing.rules import balances
from billing.views import pdf_response
from common.errors import RuleBroken
from common.permissions import IsParent
from curriculum import rules as curriculum
from curriculum.models import Certificate
from curriculum.views import certificate_pdf_response
from families.models import Message
from lessons.models import Lesson


def family_of(user):
    fam = getattr(user, "family", None)
    if fam is None or fam.deleted_at:
        raise RuleBroken("This login is not linked to a family. Message HILYS.", "detail")
    return fam


def local(dt, tz):
    return dt.astimezone(ZoneInfo(tz)).strftime("%a %d %b, %H:%M")


@api_view(["GET"])
@permission_classes([IsParent])
def overview(request):
    fam = family_of(request.user)
    now = timezone.now()
    nxt = Lesson.objects.filter(enrolment__student__family=fam, starts_at__gte=now, status="scheduled").select_related(
        "enrolment__student", "teacher").first()
    b = balances(fam)
    children = []
    for s in fam.students.all():
        e = s.enrolments.exclude(stage__in=["stopped"]).select_related("book", "teacher", "package").first()
        p = curriculum.progress(s, e.book) if e and e.book else None
        children.append({"id": s.pk, "name": s.first_name, "level": s.get_level_display(),
                         "teacher": e.teacher.display_name if e and e.teacher else "", "package": e.package.name if e and e.package else "",
                         "stage": e.get_stage_display() if e else "Not enrolled",
                         "progress": {"done": p["done"], "total": p["total"], "book": p["book"]} if p else None})
    return Response({
        "parent": fam.parent_name, "time_zone": fam.time_zone, "children": children,
        "next_lesson": {"child": nxt.enrolment.student.first_name, "when": local(nxt.starts_at, fam.time_zone),
                        "starts_at": nxt.starts_at, "teacher": nxt.teacher.display_name,
                        "zoom": getattr(getattr(nxt.teacher, "teacher_profile", None), "zoom_link", "")} if nxt else None,
        "owed": {c: str(v) for c, v in b["owed"].items()},
        "unread_messages": fam.messages.filter(read_by_family=False).exclude(sender=request.user).count(),
    })


@api_view(["GET"])
@permission_classes([IsParent])
def timetable(request):
    fam = family_of(request.user)
    qs = Lesson.objects.filter(enrolment__student__family=fam).select_related("enrolment__student", "teacher", "unit")
    upcoming = qs.filter(starts_at__gte=timezone.now() - timezone.timedelta(minutes=30)).exclude(status="moved")[:30]
    return Response([{"id": ls.pk, "child": ls.enrolment.student.first_name, "when": local(ls.starts_at, fam.time_zone),
                      "starts_at": ls.starts_at, "minutes": ls.minutes, "teacher": ls.teacher.display_name,
                      "status": ls.get_status_display(), "kind": ls.get_kind_display()} for ls in upcoming])


@api_view(["GET"])
@permission_classes([IsParent])
def notes(request):
    """Lesson notes written for parents. Teachers' private notes are never sent."""
    fam = family_of(request.user)
    qs = Lesson.objects.filter(enrolment__student__family=fam).exclude(status="scheduled").select_related(
        "enrolment__student", "teacher", "unit").order_by("-starts_at")[:40]
    return Response([{"id": ls.pk, "child": ls.enrolment.student.first_name, "when": local(ls.starts_at, fam.time_zone),
                      "teacher": ls.teacher.display_name, "status": ls.get_status_display(), "note": ls.parent_note,
                      "unit": f"Lesson {ls.unit.number}: {ls.unit.title_nd} ({ls.unit.title_en})" if ls.unit else ""} for ls in qs])


@api_view(["GET"])
@permission_classes([IsParent])
def progress(request, pk):
    fam = family_of(request.user)
    s = fam.students.filter(pk=pk).first()
    e = s and s.enrolments.exclude(stage="stopped").filter(book__isnull=False).select_related("book").first()
    if not e:
        raise RuleBroken("Progress shows once your child starts a book.", "detail")
    data = curriculum.progress(s, e.book)
    data["certificates"] = [{"id": c.pk, "number": c.number, "book": c.book.title} for c in s.certificates.all()]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsParent])
def documents(request):
    fam = family_of(request.user)
    qs = fam.documents.exclude(status__in=["draft", "cancelled"]).order_by("-issue_date", "-id")
    return Response([{"id": d.pk, "kind": d.get_kind_display(), "number": d.number, "date": d.issue_date,
                      "total": str(d.total), "currency": d.currency, "status": d.get_status_display(),
                      "outstanding": str(d.outstanding()) if d.kind == "invoice" else None} for d in qs])


@api_view(["GET"])
@permission_classes([IsParent])
def document_pdf(request, pk):
    doc = Document.objects.filter(family=family_of(request.user), pk=pk).exclude(status__in=["draft", "cancelled"]).first()
    if not doc:
        raise RuleBroken("We could not find that document.", "detail")
    return pdf_response(doc)


@api_view(["GET"])
@permission_classes([IsParent])
def certificate_pdf(request, pk):
    cert = Certificate.objects.filter(student__family=family_of(request.user), pk=pk).first()
    if not cert:
        raise RuleBroken("We could not find that certificate.", "detail")
    return certificate_pdf_response(cert)


@api_view(["GET", "POST"])
@permission_classes([IsParent])
def messages(request):
    fam = family_of(request.user)
    if request.method == "POST":
        body = (request.data.get("body") or "").strip()
        if not body:
            raise RuleBroken("Write a message first.", "body")
        Message.objects.create(family=fam, sender=request.user, body=body, read_by_family=True)
        from workflow.notify import notify, staff
        notify(staff("owner", "coordinator"), f"Message from {fam}", body[:120], f"/families?open={fam.pk}")
    fam.messages.exclude(sender=request.user).update(read_by_family=True)
    return Response([{"id": m.pk, "mine": m.sender_id == request.user.pk,
                      "from": "You" if m.sender_id == request.user.pk else (m.sender.display_name if m.sender else "HILYS"),
                      "body": m.body, "at": m.created_at} for m in fam.messages.select_related("sender")])
