from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from common.errors import RuleBroken
from common.testing import client_for, make_family, make_package, make_student, make_user
from enrolments.models import Enrolment
from teacherpay import rules as pay

from . import rules
from .models import Lesson


class LessonTests(TestCase):
    def setUp(self):
        self.t1 = make_user("t1", "teacher")
        self.t2 = make_user("t2", "teacher")
        self.fin = make_user("fin", "finance")
        self.s1 = make_student(make_family("A"), "Ann")
        self.s2 = make_student(make_family("B"), "Ben")
        self.e1 = Enrolment.objects.create(student=self.s1, teacher=self.t1, package=make_package(), stage="active",
                                           weekly_slots=[{"weekday": 0, "time": "17:00"}, {"weekday": 3, "time": "17:00"}])
        self.e2 = Enrolment.objects.create(student=self.s2, teacher=self.t2, package=make_package(), stage="active")
        past = timezone.now() - timedelta(days=1)
        self.l1 = Lesson.objects.create(enrolment=self.e1, teacher=self.t1, starts_at=past)
        self.l2 = Lesson.objects.create(enrolment=self.e2, teacher=self.t2, starts_at=past)

    def test_report_rules(self):
        with self.assertRaises(RuleBroken):
            rules.report(self.l2, self.t1, "taught", "note")  # not your lesson
        with self.assertRaises(RuleBroken):
            rules.report(self.l1, self.t1, "taught", "")  # parent note needed
        rules.report(self.l1, self.t1, "cut_short", "Power cut")
        self.assertTrue(self.l1.makeup_owed)
        m = rules.book_makeup(self.l1, timezone.now() + timedelta(days=2), self.t1)
        self.assertEqual(m.makeup_for, self.l1)
        with self.assertRaises(RuleBroken):
            rules.book_makeup(self.l1, timezone.now(), self.t1)
        future = Lesson.objects.create(enrolment=self.e1, teacher=self.t1, starts_at=timezone.now() + timedelta(days=3))
        with self.assertRaises(RuleBroken):
            rules.report(future, self.t1, "taught", "too early")

    def test_teacher_portal_sees_only_own(self):
        c = client_for(self.t1)
        ids = [l["id"] for l in c.get("/api/teacher/lessons/").data]
        self.assertEqual(ids, [self.l1.pk])
        names = [s["name"] for s in c.get("/api/teacher/students/").data]
        self.assertEqual(names, ["Ann"])
        r = c.post(f"/api/teacher/lessons/{self.l2.pk}/report/", {"status": "taught", "parent_note": "x"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(c.get("/api/lessons/").status_code, 403)  # staff list is closed to teachers

    def test_schedule_month_is_safe_twice(self):
        n = rules.schedule_month(self.e1, 2026, 12)
        self.assertGreater(n, 0)
        self.assertEqual(rules.schedule_month(self.e1, 2026, 12), 0)

    def test_teacher_pay_counts_only_reported(self):
        rules.report(self.l1, self.t1, "taught", "Good")
        Lesson.objects.create(enrolment=self.e1, teacher=self.t1, starts_at=timezone.now() - timedelta(hours=5))
        d = self.l1.starts_at
        st = pay.build(self.t1, d.year, d.month)
        self.assertEqual(len(st.lines), 1)
        self.assertEqual(st.unreported, 1)
        with self.assertRaises(RuleBroken):
            pay.approve(st, self.fin)
