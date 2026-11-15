from django.urls import include, path
from rest_framework.routers import DefaultRouter

from analytics import views as analytics
from audit.views import AuditViewSet
from billing.views import DocumentViewSet, PaymentViewSet
from catalogue.views import CatalogueViewSet
from curriculum.views import BookCheckViewSet, BookViewSet, CertificateViewSet
from enrolments.views import EnrolmentViewSet
from families.views import FamilyViewSet, StudentViewSet
from finance import views as finance
from leads.views import LeadViewSet
from lessons import teacher_views as teacher
from lessons.views import LessonViewSet
from mobile import views as parent
from pipeline.views import OpportunityViewSet
from privacy.views import DataRequestViewSet
from settings_app.views import company_settings
from teacherpay.views import PayStatementViewSet
from users import views as users
from website import views as website
from workflow import views as workflow

router = DefaultRouter()
for prefix, viewset in [
    ("users", users.UserViewSet), ("audit", AuditViewSet), ("catalogue", CatalogueViewSet), ("leads", LeadViewSet),
    ("families", FamilyViewSet), ("students", StudentViewSet), ("books", BookViewSet), ("book-checks", BookCheckViewSet),
    ("certificates", CertificateViewSet), ("enrolments", EnrolmentViewSet), ("lessons", LessonViewSet),
    ("pipeline", OpportunityViewSet), ("documents", DocumentViewSet), ("payments", PaymentViewSet),
    ("finance/accounts", finance.AccountViewSet), ("finance/entries", finance.EntryViewSet),
    ("teacher-pay", PayStatementViewSet), ("tasks", workflow.TaskViewSet), ("feedback", workflow.FeedbackViewSet),
    ("privacy/requests", DataRequestViewSet), ("site-content", website.SiteContentViewSet),
]:
    router.register(prefix, viewset, basename=prefix.replace("/", "-"))

api = [
    path("auth/login/", users.login), path("auth/logout/", users.logout), path("auth/me/", users.me),
    path("auth/password/", users.change_password),
    path("settings/", company_settings),
    path("home/", analytics.home), path("analytics/", analytics.company),
    path("finance/overview/", finance.overview), path("finance/export/", finance.export),
    path("notifications/", workflow.notifications), path("notifications/read/", workflow.notifications_read),
    # Teacher portal
    path("teacher/lessons/", teacher.lessons), path("teacher/lessons/<int:pk>/report/", teacher.report),
    path("teacher/students/", teacher.students), path("teacher/students/<int:pk>/progress/", teacher.student_progress),
    path("teacher/book-check/", teacher.book_check), path("teacher/pay/", teacher.pay), path("teacher/units/", teacher.units),
    # Parent app
    path("parent/overview/", parent.overview), path("parent/timetable/", parent.timetable), path("parent/notes/", parent.notes),
    path("parent/children/<int:pk>/progress/", parent.progress), path("parent/documents/", parent.documents),
    path("parent/documents/<int:pk>/pdf/", parent.document_pdf), path("parent/certificates/<int:pk>/pdf/", parent.certificate_pdf),
    path("parent/messages/", parent.messages),
    # Public website
    path("public/enquiry/", website.enquiry), path("public/catalogue/", website.catalogue), path("public/content/", website.content),
    path("", include(router.urls)),
]

urlpatterns = [
    path("api/", include(api)),
    path("verify/<str:code>", website.verify),
    path("feedback/<str:token>", website.feedback),
]
