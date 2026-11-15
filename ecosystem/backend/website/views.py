"""Public, throttled endpoints for the website, and the public verification and feedback pages."""
from django.shortcuts import render
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from billing.models import Document
from catalogue.models import CatalogueItem
from curriculum.models import Certificate
from leads import rules as lead_rules
from settings_app.models import CompanySettings
from workflow.models import Feedback
from workflow.notify import notify, staff

from .models import SiteContent
from .throttles import PublicThrottle


class EnquirySerializer(serializers.Serializer):
    """Website form. Loose on purpose: anything odd is flagged for cleanup, never rejected."""
    parent_name = serializers.CharField(max_length=120, allow_blank=True, required=False)
    phone = serializers.CharField(max_length=40, allow_blank=True, required=False)
    email = serializers.CharField(max_length=200, allow_blank=True, required=False)
    country = serializers.CharField(max_length=2, allow_blank=True, required=False)
    time_zone = serializers.CharField(max_length=64, allow_blank=True, required=False)
    child_name = serializers.CharField(max_length=120, allow_blank=True, required=False)
    child_age = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=120)
    interest = serializers.ChoiceField(choices=["live", "video", "plus", "not_sure"], required=False)
    suggested_level = serializers.CharField(max_length=40, allow_blank=True, required=False)
    message = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    source = serializers.ChoiceField(choices=["Website", "Level check", "Parent app"], required=False)
    website = serializers.CharField(allow_blank=True, required=False)  # honeypot: people leave it empty


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicThrottle])
def enquiry(request):
    s = EnquirySerializer(data=request.data)
    s.is_valid(raise_exception=True)
    data = dict(s.validated_data)
    if data.pop("website", ""):
        return Response({"ok": True}, status=201)  # a bot; say nothing
    source = data.pop("source", "Website")
    email = data.get("email", "")
    if email and "@" not in email:
        data["message"] = (data.get("message", "") + f"\n(Email as typed: {email})").strip()
        data["email"] = ""
    lead = lead_rules.create_lead(data, source=source)
    notify(staff("owner", "coordinator"), f"New enquiry: {lead}", f"{lead.get_interest_display()} · reply by "
           f"{timezone.localtime(lead.reply_due_at).strftime('%a %H:%M')} UTC", f"/leads?open={lead.pk}")
    return Response({"ok": True, "message": "Thank you. We'll reply within one working day."}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([PublicThrottle])
def catalogue(request):
    items = CatalogueItem.objects.filter(is_active=True, on_website=True)
    return Response([{"name": i.name, "kind": i.get_kind_display(), "lesson_type": i.get_lesson_type_display(),
                      "price": str(i.price), "currency": i.currency, "unit": i.unit} for i in items])


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([PublicThrottle])
def content(request):
    return Response([{"kind": c.kind, "title": c.title, "body": c.body, "author": c.author}
                     for c in SiteContent.objects.filter(is_published=True)])


def verify(request, code):
    """Anyone holding a HILYS document can check it is genuine. Shows only what is printed on it."""
    code = (code or "").strip().upper()[:16]
    doc = Document.objects.filter(verify_code=code).exclude(status="draft").select_related("family").first()
    cert = None if doc else Certificate.objects.filter(verify_code=code).select_related("student", "book").first()
    ctx = {"company": CompanySettings.get(), "doc": doc, "cert": cert, "code": code}
    return render(request, "public/verify.html", ctx, status=200 if (doc or cert) else 404)


def feedback(request, token):
    fb = Feedback.objects.filter(token=token).select_related("family").first()
    ctx = {"company": CompanySettings.get(), "fb": fb, "done": False, "errors": []}
    if fb and request.method == "POST" and not fb.answered_at:
        rating = request.POST.get("rating", "")
        if not rating.isdigit() or not 1 <= int(rating) <= 5:
            ctx["errors"].append("Please choose how happy you are, from 1 to 5.")
        else:
            fb.rating = int(rating)
            fb.would_recommend = request.POST.get("recommend") == "yes"
            fb.best = request.POST.get("best", "")[:2000]
            fb.improve = request.POST.get("improve", "")[:2000]
            fb.may_quote = request.POST.get("may_quote") == "on"
            fb.answered_at = timezone.now()
            fb.save()
            notify(staff("owner"), f"Feedback from {fb.family}", f"{fb.rating} out of 5", "/feedback")
    ctx["done"] = bool(fb and fb.answered_at)
    return render(request, "public/feedback.html", ctx, status=200 if fb else 404)


class SiteContentSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = SiteContent
        fields = ["id", "kind", "kind_label", "title", "body", "author", "is_published", "sort_order"]


from rest_framework import viewsets  # noqa: E402

from common.permissions import IsInternalStaff  # noqa: E402


class SiteContentViewSet(viewsets.ModelViewSet):
    """Website content the owner changes from the staff app. Publishing a review needs the owner."""
    serializer_class = SiteContentSerializer
    permission_classes = [IsInternalStaff]
    queryset = SiteContent.objects.all()
    filterset_fields = ["kind", "is_published"]

    def perform_update(self, serializer):
        if serializer.validated_data.get("is_published") and not self.request.user.is_leadership:
            from common.errors import RuleBroken
            raise RuleBroken("Only the owner can publish to the website.", "is_published")
        serializer.save()

    def perform_create(self, serializer):
        if serializer.validated_data.get("is_published") and not self.request.user.is_leadership:
            from common.errors import RuleBroken
            raise RuleBroken("Only the owner can publish to the website.", "is_published")
        serializer.save()
