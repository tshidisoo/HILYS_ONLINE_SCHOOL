from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from common.business_time import add_working_day
from common.testing import client_for, make_user

from . import rules
from .models import Lead

HRE = ZoneInfo("Africa/Harare")


class ReplyClockTests(TestCase):
    def test_weekday_morning_is_due_next_working_day_same_time(self):
        due = add_working_day(datetime(2026, 11, 17, 10, 0, tzinfo=HRE))  # Tuesday
        self.assertEqual(due, datetime(2026, 11, 18, 10, 0, tzinfo=HRE))

    def test_friday_evening_waits_for_monday_morning_count(self):
        due = add_working_day(datetime(2026, 11, 20, 19, 0, tzinfo=HRE))  # Friday after hours
        self.assertEqual(due, datetime(2026, 11, 24, 8, 0, tzinfo=HRE))  # starts Monday 08:00, due Tuesday 08:00

    def test_saturday_counts_from_monday(self):
        due = add_working_day(datetime(2026, 11, 21, 12, 0, tzinfo=HRE))
        self.assertEqual(due.date().isoformat(), "2026-11-24")

    def test_just_before_and_after_midnight_in_harare(self):
        # 23:59 Tuesday Harare is 21:59 UTC; it counts from Wednesday morning.
        before = add_working_day(datetime(2026, 11, 17, 21, 59, tzinfo=ZoneInfo("UTC")))
        self.assertEqual(before, datetime(2026, 11, 19, 8, 0, tzinfo=HRE))
        after = add_working_day(datetime(2026, 11, 17, 22, 1, tzinfo=ZoneInfo("UTC")))  # 00:01 Wednesday Harare
        self.assertEqual(after, datetime(2026, 11, 19, 8, 0, tzinfo=HRE))

    def test_clock_states(self):
        lead = rules.create_lead({"parent_name": "A", "email": "a@example.com"}, "Website")
        lead.reply_due_at = timezone.now() - timedelta(minutes=1)
        self.assertEqual(rules.reply_clock(lead), "late")
        lead.reply_due_at = timezone.now() + timedelta(hours=1)
        self.assertEqual(rules.reply_clock(lead), "due_soon")
        lead.first_reply_at = timezone.now()
        self.assertEqual(rules.reply_clock(lead), "answered")


class LeadRuleTests(TestCase):
    def test_bad_lead_is_saved_and_flagged_not_rejected(self):
        lead = rules.create_lead({"parent_name": "", "phone": "123", "child_age": 40}, "Website")
        self.assertTrue(Lead.objects.filter(pk=lead.pk).exists())
        self.assertTrue(lead.needs_cleanup)
        self.assertIn("No parent name", lead.cleanup_reasons)

    def test_phone_is_normalised(self):
        a = rules.create_lead({"parent_name": "A", "phone": "07700 900123"}, "Website")
        b = rules.create_lead({"parent_name": "B", "phone": "+44 7700 900123"}, "Website")
        self.assertEqual(a.phone, b.phone)
        self.assertEqual(a.phone, "+447700900123")

    def test_dismiss_needs_a_reason(self):
        lead = rules.create_lead({"parent_name": "A", "email": "a@example.com"}, "Website")
        with self.assertRaises(Exception):
            rules.dismiss(lead, " ")


class LeadAccessTests(TestCase):
    def setUp(self):
        rules.create_lead({"parent_name": "A", "email": "a@example.com"}, "Website")

    def test_roles(self):
        for role, code in [("owner", 200), ("coordinator", 200), ("finance", 200), ("teacher", 403), ("parent", 403)]:
            self.assertEqual(client_for(make_user(f"u-{role}", role)).get("/api/leads/").status_code, code, role)
        self.assertEqual(client_for(None).get("/api/leads/").status_code, 401)

    def test_website_enquiry_creates_lead_and_honeypot_is_ignored(self):
        c = client_for(None)
        r = c.post("/api/public/enquiry/", {"parent_name": "Web Parent", "email": "web@example.com", "child_name": "Kid"}, format="json")
        self.assertEqual(r.status_code, 201)
        lead = Lead.objects.get(parent_name="Web Parent")
        self.assertEqual(lead.source, "Website")
        self.assertIsNotNone(lead.reply_due_at)
        c.post("/api/public/enquiry/", {"parent_name": "Bot", "website": "spam"}, format="json")
        self.assertFalse(Lead.objects.filter(parent_name="Bot").exists())

    def test_convert_makes_family_student_enrolment(self):
        lead = Lead.objects.first()
        r = client_for(make_user("co", "coordinator")).post(f"/api/leads/{lead.pk}/convert/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "converted")
        self.assertEqual(lead.family.students.count(), 1)
        self.assertEqual(lead.family.students.first().enrolments.first().stage, "trial")
