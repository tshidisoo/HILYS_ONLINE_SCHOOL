import threading
from datetime import date
from decimal import Decimal

from django.db import connection
from django.test import TestCase, TransactionTestCase

from common.errors import RuleBroken
from common.testing import client_for, make_family, make_package, make_user

from . import rules
from .models import Document
from .numbering import next_number


class BillingLifecycleTests(TestCase):
    def setUp(self):
        self.fin = make_user("fin", "finance")
        self.co = make_user("co", "coordinator")
        self.fam = make_family("Payer", email="payer@example.com")
        self.pkg = make_package("48")

    def invoice(self, amount="48"):
        inv = Document.objects.create(kind="invoice", family=self.fam)
        rules.set_lines(inv, [{"item": self.pkg.pk, "description": "Package", "unit_price": amount}])
        return rules.issue(inv, self.co)

    def test_quote_to_invoice_part_pay_full_pay_reverse_credit(self):
        q = Document.objects.create(kind="quotation", family=self.fam)
        rules.set_lines(q, [{"description": "Package", "unit_price": "96"}])
        rules.issue(q, self.co)
        inv = rules.convert_quotation(q, self.co)
        self.assertEqual(inv.total, Decimal("96.00"))
        rules.issue(inv, self.co)
        self.assertTrue(inv.number.startswith("INV-"))
        p1 = rules.record_payment(self.fin, self.fam, "40", "USD", "mukuru", date.today(), "MK1")
        inv.refresh_from_db()
        self.assertEqual(inv.status, "part_paid")
        self.assertEqual(inv.outstanding(), Decimal("56.00"))
        self.assertEqual(p1.receipt.kind, "receipt")
        rules.record_payment(self.fin, self.fam, "56", "USD", "ecocash", date.today(), "EC1")
        inv.refresh_from_db()
        self.assertEqual(inv.status, "paid")
        rules.reverse_payment(p1, self.fin, "Wrong family")
        inv.refresh_from_db()
        self.assertEqual(inv.status, "part_paid")
        p1.receipt.refresh_from_db()
        self.assertEqual(p1.receipt.status, "cancelled")
        cn = rules.credit_note_for(inv, self.co, "40", "Goodwill")
        rules.issue(cn, self.co)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "paid")

    def test_issued_documents_are_locked(self):
        inv = self.invoice()
        with self.assertRaises(RuleBroken):
            rules.set_lines(inv, [{"description": "x", "unit_price": "1"}])
        with self.assertRaises(RuleBroken):
            rules.amend(inv, self.co, "typo", [])
        owner = make_user("o", "owner")
        with self.assertRaises(RuleBroken):
            rules.amend(inv, owner, "", [{"description": "x", "unit_price": "1"}])
        rules.amend(inv, owner, "Price typo", [{"description": "Package", "unit_price": "32"}])
        self.assertEqual(inv.total, Decimal("32.00"))
        self.assertIn("Price typo", inv.amended_reason)

    def test_only_finance_and_owner_record_payments(self):
        self.invoice()
        with self.assertRaises(RuleBroken):
            rules.record_payment(self.co, self.fam, "10", "USD", "cash", date.today())
        r = client_for(self.co).post("/api/payments/", {"family": self.fam.pk, "amount": "10", "currency": "USD",
                                                       "method": "cash", "received_on": "2026-11-01"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_never_across_currencies(self):
        inv = self.invoice()
        pay = rules.record_payment(self.fin, self.fam, "10", "GBP", "bank", date.today(), allocations=[])
        with self.assertRaises(RuleBroken):
            rules.allocate(pay, [{"invoice": inv.pk, "amount": "10"}], self.fin)
        b = rules.balances(self.fam)
        self.assertEqual(b["owed"], {"USD": Decimal("48.00")})
        self.assertEqual(b["credit"], {"GBP": Decimal("10.00")})

    def test_duplicate_reference_is_blocked(self):
        rules.record_payment(self.fin, self.fam, "10", "USD", "mukuru", date.today(), "MK9", allocations=[])
        with self.assertRaises(RuleBroken):
            rules.record_payment(self.fin, self.fam, "10", "USD", "mukuru", date.today(), "MK9", allocations=[])

    def test_payment_plan_and_statement_and_pdfs(self):
        inv = self.invoice("100")
        plan = rules.payment_plan_for(inv, self.fin, 3)
        self.assertEqual(sum(i.amount for i in plan.installments.all()), Decimal("100.00"))
        rules.issue(plan, self.fin)
        rules.record_payment(self.fin, self.fam, "30", "USD", "cash", date.today(), "C1")
        st = rules.statement(self.fam, self.fin)
        self.assertEqual(st.total, Decimal("70.00"))
        from .pdf import render_document
        for doc in Document.objects.exclude(status="draft"):
            self.assertTrue(render_document(doc).startswith(b"%PDF"))

    def test_verify_page(self):
        inv = self.invoice()
        r = self.client.get(f"/verify/{inv.verify_code}")
        self.assertContains(r, inv.number)
        self.assertEqual(self.client.get("/verify/NOTACODE").status_code, 404)

    def test_monthly_invoices_are_safe_to_run_twice(self):
        from enrolments.models import Enrolment
        from common.testing import make_student
        s = make_student(self.fam)
        Enrolment.objects.create(student=s, package=self.pkg, stage="active", level="beginner")
        c = client_for(self.co)
        self.assertEqual(c.post("/api/documents/monthly_invoices/", {"period": "2026-12"}, format="json").data["created"], 1)
        self.assertEqual(c.post("/api/documents/monthly_invoices/", {"period": "2026-12"}, format="json").data["created"], 0)


class NumberingConcurrencyTests(TransactionTestCase):
    def test_parallel_issue_gives_gapless_unique_numbers(self):
        results, errors = [], []

        def take():
            try:
                results.append(next_number("invoice", 2026))
            except Exception as e:  # noqa: BLE001
                errors.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=take) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertFalse(errors)
        self.assertEqual(sorted(results), [f"INV-2026-{i:04d}" for i in range(1, 9)])
