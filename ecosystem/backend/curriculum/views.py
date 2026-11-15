from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsInternalStaff
from families.models import Student

from . import rules
from .models import Book, BookCheck, Certificate, Unit


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "book", "number", "title_nd", "title_en", "kind", "culture", "pages"]


class BookSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ["id", "code", "title", "level", "order", "is_ready", "units"]


class BookCheckSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.display_name", default="", read_only=True)
    result_label = serializers.CharField(source="get_result_display", read_only=True)
    certificate = serializers.SerializerMethodField()

    class Meta:
        model = BookCheck
        fields = ["id", "student", "student_name", "book", "teacher", "teacher_name", "checked_on", "parts", "score",
                  "result", "result_label", "practice_notes", "certificate"]
        read_only_fields = ["score", "result", "teacher"]

    def get_certificate(self, c):
        cert = getattr(c, "certificate", None)
        return {"id": cert.pk, "number": cert.number, "verify_code": cert.verify_code} if cert else None


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookSerializer
    pagination_class = None  # a handful of books
    queryset = Book.objects.prefetch_related("units")
    permission_classes = [IsInternalStaff]

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        return Response(rules.progress(Student.objects.get(pk=request.query_params["student"]), self.get_object()))


class BookCheckViewSet(viewsets.ModelViewSet):
    serializer_class = BookCheckSerializer
    permission_classes = [IsInternalStaff]
    filterset_fields = ["student", "book", "result"]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        return BookCheck.objects.select_related("student", "teacher", "certificate")

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        check = rules.record_check(d["student"], d["book"], request.user, d["parts"], d.get("checked_on"), d.get("practice_notes", ""))
        return Response(self.get_serializer(check).data, status=201)


def certificate_pdf_response(cert):
    from billing.pdf import render_certificate
    resp = HttpResponse(render_certificate(cert), content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{cert.number}.pdf"'
    return resp


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsInternalStaff]
    queryset = Certificate.objects.select_related("student", "book")

    class Ser(serializers.ModelSerializer):
        student_name = serializers.CharField(source="student.name", read_only=True)
        book_title = serializers.CharField(source="book.title", read_only=True)

        class Meta:
            model = Certificate
            fields = ["id", "student", "student_name", "book", "book_title", "number", "issued_on", "verify_code"]

    serializer_class = Ser

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        return certificate_pdf_response(self.get_object())
