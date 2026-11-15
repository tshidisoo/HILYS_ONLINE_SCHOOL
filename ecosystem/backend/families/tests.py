from django.test import TestCase

from common.errors import RuleBroken
from common.testing import client_for, make_family, make_student, make_user
from privacy.models import SensitiveAccess

from .models import Family
from .validation import save_family


class DuplicateTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner", "owner")
        self.co = make_user("co", "coordinator")
        save_family(Family(parent_name="First", email="same@example.com", phone="07700 900111"), self.co)

    def test_matching_email_is_a_hard_stop(self):
        with self.assertRaises(RuleBroken):
            save_family(Family(parent_name="Second", email="SAME@example.com"), self.owner, override_reason="sure")

    def test_matching_phone_needs_owner_and_reason_and_is_logged(self):
        with self.assertRaises(RuleBroken):
            save_family(Family(parent_name="Second", phone="+447700900111"), self.co, override_reason="cousin")
        with self.assertRaises(RuleBroken):
            save_family(Family(parent_name="Second", phone="+447700900111"), self.owner)
        f = save_family(Family(parent_name="Second", phone="+447700900111"), self.owner, override_reason="Shared family phone")
        from audit.models import AuditEntry
        self.assertTrue(AuditEntry.objects.filter(action="override", object_id=str(f.pk)).exists())

    def test_outside_records_are_flagged_not_rejected(self):
        f = save_family(Family(parent_name="From app", email="same@example.com"), self.co, from_outside=True)
        self.assertTrue(f.needs_cleanup)


class FamilyAccessTests(TestCase):
    def test_teachers_and_parents_cannot_list_families(self):
        make_family("A")
        self.assertEqual(client_for(make_user("t", "teacher")).get("/api/families/").status_code, 403)
        self.assertEqual(client_for(make_user("p", "parent")).get("/api/families/").status_code, 403)
        self.assertEqual(client_for(make_user("c", "coordinator")).get("/api/families/").status_code, 200)

    def test_support_notes_are_encrypted_hidden_in_lists_and_access_is_logged(self):
        s = make_student(make_family("A"))
        s.support_notes = "Needs short breaks"
        s.save()
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("select support_notes from families_student where id=%s", [s.pk])
            self.assertNotIn("short breaks", cur.fetchone()[0])
        c = client_for(make_user("c", "coordinator"))
        listed = c.get("/api/students/").data["results"][0]
        self.assertNotIn("support_notes", listed)
        self.assertTrue(listed["has_support_notes"])
        self.assertEqual(c.get(f"/api/students/{s.pk}/support_notes/").data["support_notes"], "Needs short breaks")
        self.assertEqual(SensitiveAccess.objects.count(), 1)

    def test_delete_goes_to_bin_and_owner_restores(self):
        f = make_family("Bin me")
        c = client_for(make_user("c", "coordinator"))
        self.assertEqual(c.delete(f"/api/families/{f.pk}/").status_code, 204)
        self.assertFalse(Family.objects.filter(pk=f.pk).exists())
        self.assertEqual(c.get("/api/families/bin/").status_code, 403)
        o = client_for(make_user("o", "owner"))
        self.assertEqual(o.post(f"/api/families/{f.pk}/restore/").status_code, 200)
        self.assertTrue(Family.objects.filter(pk=f.pk).exists())
