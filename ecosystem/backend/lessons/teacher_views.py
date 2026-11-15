"""The teacher portal. A teacher sees only their own lessons, students, trials and pay. Never another teacher's."""
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common.errors import RuleBroken
from common.permissions import IsTeacher
from curriculum import rules as curriculum
from curriculum.models import Book, Unit
from enrolments.models import Enrolment
from families.models import Student
from teacherpay.models import PayStatement

from . import rules
from .models import Lesson
from .views import LessonSerializer, filter_range, lesson_queryset


class TeacherLessonSerializer(LessonSerializer):
    next_unit = serializers.SerializerMethodField()
    support_notes = serializers.SerializerMethodField()

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ["next_unit", "support_notes"]

    def get_next_unit(self, ls):
        u = rules.next_unit(ls.enrolment) if ls.enrolment_id else None
        return {"id": u.pk, "label": f"Lesson {u.number}: {u.title_nd} ({u.title_en})"} if u else None

    def get_support_notes(self, ls):
        return ls.enrolment.student.support_notes if ls.enrolment_id else ""


def own_lessons(user):
    return lesson_queryset().filter(teacher=user)


@api_view(["GET"])
@permission_classes([IsTeacher])
def lessons(request):
    qs = filter_range(own_lessons(request.user), request.query_params)
    if request.query_params.get("status"):
        qs = qs.filter(status=request.query_params["status"])
    return Response(TeacherLessonSerializer(qs[:300], many=True).data)


@api_view(["POST"])
@permission_classes([IsTeacher])
def report(request, pk):
    lesson = own_lessons(request.user).filter(pk=pk).first()
    if not lesson:
        raise RuleBroken("We could not find that lesson in your timetable.", "detail")
    unit = Unit.objects.filter(pk=request.data.get("unit")).first() if request.data.get("unit") else None
    rules.report(lesson, request.user, request.data.get("status"), request.data.get("parent_note", ""),
                 request.data.get("private_note", ""), unit, request.data.get("trial_level", ""))
    return Response(TeacherLessonSerializer(lesson).data)


@api_view(["GET"])
@permission_classes([IsTeacher])
def students(request):
    out = []
    for e in Enrolment.objects.filter(teacher=request.user).exclude(stage="stopped").select_related("student__family", "book", "package"):
        p = curriculum.progress(e.student, e.book) if e.book else None
        out.append({"enrolment": e.pk, "student": e.student.pk, "name": e.student.name, "level": e.student.get_level_display(),
                    "stage": e.get_stage_display(), "package": e.package.name if e.package else "",
                    "group_name": e.group_name, "family_time_zone": e.student.family.time_zone,
                    "weekly_slots": e.weekly_slots, "book": e.book.title if e.book else "", "book_id": e.book_id,
                    "progress": {"done": p["done"], "total": p["total"]} if p else None})
    return Response(out)


@api_view(["GET"])
@permission_classes([IsTeacher])
def student_progress(request, pk):
    e = Enrolment.objects.filter(teacher=request.user, student_id=pk).select_related("student", "book").first()
    if not e or not e.book:
        raise RuleBroken("This child is not in your class.", "detail")
    data = curriculum.progress(e.student, e.book)
    data["checks"] = [{"checked_on": c.checked_on, "score": c.score, "result": c.get_result_display()}
                      for c in e.student.book_checks.filter(book=e.book)]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsTeacher])
def book_check(request):
    student = Student.objects.filter(pk=request.data.get("student"), enrolments__teacher=request.user).first()
    book = Book.objects.filter(pk=request.data.get("book")).first()
    if not student or not book:
        raise RuleBroken("Choose one of your students and the book.", "student")
    check = curriculum.record_check(student, book, request.user, request.data.get("parts") or [],
                                    practice_notes=request.data.get("practice_notes", ""))
    return Response({"score": check.score, "result": check.get_result_display(),
                     "certificate": check.certificate.number if hasattr(check, "certificate") else None}, status=201)


@api_view(["GET"])
@permission_classes([IsTeacher])
def pay(request):
    rows = PayStatement.objects.filter(teacher=request.user).exclude(status="draft") | PayStatement.objects.filter(teacher=request.user, status="draft")
    return Response([{"month": s.month, "status": s.get_status_display(), "total": str(s.total), "currency": s.currency,
                      "lessons": len(s.lines), "unreported": s.unreported, "paid_on": s.paid_on}
                     for s in rows.order_by("-month")])


@api_view(["GET"])
@permission_classes([IsTeacher])
def units(request):
    return Response([{"id": u.pk, "label": f"Lesson {u.number}: {u.title_nd} ({u.title_en})", "book": u.book_id}
                     for u in Unit.objects.select_related("book")])
