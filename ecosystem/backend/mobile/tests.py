from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from billing import rules as billing
from billing.models import Document
from common.testing import client_for, make_family, make_package, make_student, make_user
from enrolments.models import Enrolment
from lessons.models import Lesson


class ParentScopeTests(TestCase):
    def setUp(self):
        self.p1, self.p2 = make_user("p1", "parent"), make_user("p2", "parent")
        self.f1 = make_family("One", email="one@example.com", login=self.p1)
        self.f2 = make_family("Two", email="two@example.com", login=self.p2)
        t = make_user("t", "teacher")
        co = make_user("co", "coordinator")
        for fam in (self.f1, self.f2):
            s = make_student(fam, fam.parent_name + " kid")
            e = Enrolment.objects.create(student=s, teacher=t, package=make_package(), stage="active")
            Lesson.objects.create(enrolment=e, teacher=t, starts_at=timezone.now() - timedelta(days=1), status="taught",
                                  parent_note=f"note for {fam.parent_name}", private_note="SECRET", reported_at=timezone.now())
            inv = Document.objects.create(kind="invoice", family=fam)
            billing.set_lines(inv, [{"description": "x", "unit_price": "10"}])
            billing.issue(inv, co)
        self.other_doc = Document.objects.get(family=self.f2)

    def test_parent_sees_only_own_family(self):
        c = client_for(self.p1)
        notes = c.get("/api/parent/notes/").data
        self.assertEqual([n["note"] for n in notes], ["note for One"])
        self.assertNotIn("SECRET", str(notes))
        self.assertEqual(len(c.get("/api/parent/documents/").data), 1)
        self.assertEqual(c.get(f"/api/parent/documents/{self.other_doc.pk}/pdf/").status_code, 400)
        self.assertEqual(c.get("/api/documents/").status_code, 403)

    def test_messages_go_to_staff(self):
        c = client_for(self.p1)
        r = c.post("/api/parent/messages/", {"body": "Hello"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.f1.messages.count(), 1)
