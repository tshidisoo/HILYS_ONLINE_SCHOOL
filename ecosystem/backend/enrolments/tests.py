from datetime import date

from django.test import TestCase

from billing import rules as billing
from billing.models import Document
from common.errors import RuleBroken
from common.testing import make_family, make_package, make_student, make_user
from curriculum.models import Book

from . import rules
from .models import Enrolment


class GateTests(TestCase):
    def setUp(self):
        self.co = make_user("co", "coordinator")
        self.teacher = make_user("t", "teacher")
        self.fam = make_family("F", email="f@example.com")
        self.s = make_student(self.fam, level="")
        self.e = Enrolment.objects.create(student=self.s)

    def test_gates_block_and_then_allow(self):
        with self.assertRaises(RuleBroken) as ctx:
            rules.move(self.e, "waiting", self.co)
        self.assertIn("level", ctx.exception.message)
        self.e.level, self.e.teacher, self.e.package = "beginner", self.teacher, make_package()
        rules.move(self.e, "waiting", self.co)
        with self.assertRaises(RuleBroken) as ctx:
            rules.move(self.e, "active", self.co)
        self.assertIn("weekly lesson times", ctx.exception.message)
        self.assertIn("invoice", ctx.exception.message)
        self.e.weekly_slots = [{"weekday": 1, "time": "17:30"}]
        inv = Document.objects.create(kind="invoice", family=self.fam)
        billing.set_lines(inv, [{"description": "x", "unit_price": "48"}])
        billing.issue(inv, self.co)
        rules.move(self.e, "active", self.co)
        self.assertEqual(self.e.history.count(), 2)

    def test_pause_needs_reason_and_illegal_moves_blocked(self):
        with self.assertRaises(RuleBroken):
            rules.move(self.e, "finished", self.co)
        self.e.stage = "active"
        self.e.save()
        with self.assertRaises(RuleBroken):
            rules.move(self.e, "paused", self.co)
        rules.move(self.e, "paused", self.co, "Holiday")

    def test_finishing_a_book_needs_the_end_of_book_check(self):
        from curriculum import rules as curriculum
        book = Book.objects.create(code="b1", title="Book 1")
        self.e.stage, self.e.book = "active", book
        self.e.save()
        with self.assertRaises(RuleBroken):
            rules.move(self.e, "finished", self.co)
        check = curriculum.record_check(self.s, book, self.teacher, [True, True, True, False, False, False])
        self.assertEqual(check.result, "practice")
        self.assertTrue(hasattr(check, "certificate"))
        rules.move(self.e, "finished", self.co)

    def test_slot_validation(self):
        for bad in ([{"weekday": 9, "time": "10:00"}], [{"weekday": 1, "time": "25:00"}], ["Tuesday"]):
            with self.assertRaises(RuleBroken):
                rules.validate_slots(bad)
