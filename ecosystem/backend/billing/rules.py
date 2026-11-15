"""Every money rule lives here: totals, issuing, payments, allocations, reversals, credit notes, statements."""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from audit.log import record
from common.business_time import today
from common.errors import RuleBroken
from settings_app.models import CompanySettings

from .models import Allocation, Document, Installment, Line, Payment
from .numbering import next_number

K, ST = Document.Kind, Document.Status


def recalc_total(doc):
    doc.total = sum((line.amount for line in doc.lines.all()), Decimal("0"))
    doc.save(update_fields=["total", "updated_at"])
    return doc.total


def ensure_draft(doc):
    if doc.is_locked:
        raise RuleBroken("This document is issued and locked. Issue a credit note, or ask the owner to amend it.", "detail")


def set_lines(doc, lines):
    ensure_draft(doc)
    doc.lines.all().delete()
    for ln in lines:
        Line.objects.create(document=doc, item_id=ln.get("item"), description=ln["description"],
                            quantity=Decimal(str(ln.get("quantity", 1))), unit_price=Decimal(str(ln["unit_price"])),
                            student_id=ln.get("student"))
    return recalc_total(doc)


@transaction.atomic
def issue(doc, user):
    if not user.can_issue_documents:
        raise RuleBroken("Your role cannot issue documents.", "detail")
    ensure_draft(doc)
    if doc.kind in (K.QUOTATION, K.INVOICE, K.CREDIT_NOTE) and doc.total <= 0:
        raise RuleBroken("Add at least one line with a price before issuing.", "lines")
    if doc.kind == K.CREDIT_NOTE:
        inv = doc.related
        if not inv or inv.kind != K.INVOICE or inv.status not in Document.ISSUED_STATES:
            raise RuleBroken("A credit note must belong to an issued invoice.", "related")
        if doc.total > inv.total - inv.credited_amount():
            raise RuleBroken("The credit note is more than is left on the invoice.", "lines")
    if doc.kind == K.PAYMENT_PLAN and sum(i.amount for i in doc.installments.all()) != (doc.related.outstanding() if doc.related else doc.total):
        raise RuleBroken("The instalments must add up to what is owed on the invoice.", "installments")
    s = CompanySettings.get()
    doc.issue_date = doc.issue_date or today()
    if doc.kind == K.INVOICE and not doc.due_date:
        doc.due_date = doc.issue_date + timedelta(days=s.invoice_due_days)
    if doc.kind == K.QUOTATION and not doc.due_date:
        doc.due_date = doc.issue_date + timedelta(days=s.quotation_valid_days)
    doc.number = next_number(doc.kind, doc.issue_date.year)
    doc.status = ST.ISSUED
    doc.issued_by = user
    doc.save()
    if doc.kind == K.CREDIT_NOTE:
        refresh_status(doc.related)
    record(user, "issue", doc, f"Issued {doc} to {doc.family} for {doc.currency} {doc.total}")
    return doc


@transaction.atomic
def amend(doc, user, reason, lines):
    """Issued documents are locked. Only the owner may amend one, and the reason is kept."""
    if not user.can_override_rules:
        raise RuleBroken("Only the owner can amend an issued document.", "detail")
    if not reason.strip():
        raise RuleBroken("Say why the document is being amended.", "reason")
    if doc.allocations.exists():
        raise RuleBroken("Payments are allocated to this invoice. Issue a credit note instead.", "detail")
    doc.lines.all().delete()
    for ln in lines:
        Line.objects.create(document=doc, item_id=ln.get("item"), description=ln["description"],
                            quantity=Decimal(str(ln.get("quantity", 1))), unit_price=Decimal(str(ln["unit_price"])))
    recalc_total(doc)
    doc.amended_reason = (doc.amended_reason + "\n" if doc.amended_reason else "") + f"{today()}: {reason}"
    doc.save()
    record(user, "amend", doc, f"Amended {doc}", reason)
    return doc


def refresh_status(invoice):
    """Payment status is derived from recorded money, never set by hand."""
    if invoice.kind != K.INVOICE or invoice.status in (ST.DRAFT, ST.CANCELLED):
        return invoice
    paid = invoice.paid_amount() + invoice.credited_amount()
    new = ST.PAID if paid >= invoice.total else ST.PART_PAID if paid > 0 else ST.ISSUED
    if new != invoice.status:
        invoice.status = new
        invoice.save(update_fields=["status", "updated_at"])
    return invoice


@transaction.atomic
def convert_quotation(quote, user):
    if quote.kind != K.QUOTATION or quote.status not in (ST.ISSUED, ST.ACCEPTED):
        raise RuleBroken("Only an issued quotation can become an invoice.", "detail")
    if quote.children.filter(kind=K.INVOICE).exists():
        raise RuleBroken("This quotation already has an invoice.", "detail")
    inv = Document.objects.create(kind=K.INVOICE, family=quote.family, currency=quote.currency, related=quote,
                                  period=quote.period, created_by=user, is_demo=quote.is_demo)
    for ln in quote.lines.all():
        Line.objects.create(document=inv, item=ln.item, description=ln.description, quantity=ln.quantity,
                            unit_price=ln.unit_price, student=ln.student)
    recalc_total(inv)
    quote.status = ST.ACCEPTED
    quote.save(update_fields=["status", "updated_at"])
    return inv


@transaction.atomic
def record_payment(user, family, amount, currency, method, received_on, reference="", note="", allocations=None,
                   is_demo=False):
    """Only finance and the owner record payments. A receipt is issued for every payment."""
    if not user.can_record_payments:
        raise RuleBroken("Only finance and the owner can record payments.", "detail")
    amount = Decimal(str(amount))
    if amount <= 0:
        raise RuleBroken("The amount must be more than zero.", "amount")
    if method == Payment.Method.CARD:
        raise RuleBroken("Card payments are recorded automatically once online payments are switched on.", "method")
    if reference and Payment.objects.filter(method=method, reference=reference, reversed_at__isnull=True).exists():
        raise RuleBroken(f"A payment with reference {reference} is already recorded.", "reference")
    pay = Payment.objects.create(family=family, amount=amount, currency=currency, method=method, reference=reference,
                                 received_on=received_on, recorded_by=user, note=note, is_demo=is_demo)
    if allocations is None:  # oldest unpaid invoices of the same currency first
        allocations, left = [], amount
        for inv in Document.objects.filter(family=family, kind=K.INVOICE, currency=currency,
                                           status__in=[ST.ISSUED, ST.PART_PAID]).order_by("issue_date", "id"):
            take = min(inv.outstanding(), left)
            if take > 0:
                allocations.append({"invoice": inv.pk, "amount": take})
                left -= take
            if left <= 0:
                break
    allocate(pay, allocations, user)
    receipt = Document.objects.create(kind=K.RECEIPT, family=family, currency=currency, total=amount, payment=pay,
                                      created_by=user, is_demo=is_demo, notes=f"{pay.get_method_display()} {reference}".strip())
    receipt.issue_date = received_on
    receipt.number = next_number("receipt", received_on.year)
    receipt.status = ST.PAID
    receipt.issued_by = user
    receipt.save()
    record(user, "payment", pay, f"Recorded {pay} and issued {receipt.number}")
    try:  # money in lands in the matching account for the cash-flow view
        from finance.rules import income_from_payment
        income_from_payment(pay)
    except ImportError:
        pass
    return pay


def allocate(pay, allocations, user):
    for a in allocations:
        inv = Document.objects.select_for_update().get(pk=a["invoice"])
        amt = Decimal(str(a["amount"]))
        if inv.family_id != pay.family_id or inv.kind != K.INVOICE:
            raise RuleBroken("A payment can only settle this family's invoices.", "allocations")
        if inv.currency != pay.currency:
            raise RuleBroken("A payment cannot settle an invoice in another currency.", "allocations")
        if amt <= 0 or amt > inv.outstanding():
            raise RuleBroken(f"{inv.number} has {inv.currency} {inv.outstanding()} left to pay.", "allocations")
        if amt > pay.unallocated():
            raise RuleBroken("That is more than is left of the payment.", "allocations")
        Allocation.objects.create(payment=pay, invoice=inv, amount=amt)
        refresh_status(inv)


@transaction.atomic
def reverse_payment(pay, user, reason):
    if not user.can_record_payments:
        raise RuleBroken("Only finance and the owner can reverse payments.", "detail")
    if pay.reversed_at:
        raise RuleBroken("This payment is already reversed.", "detail")
    if not reason.strip():
        raise RuleBroken("Say why the payment is being reversed.", "reason")
    invoices = [a.invoice for a in pay.allocations.select_related("invoice")]
    pay.reversed_at, pay.reversed_by, pay.reversed_reason = timezone.now(), user, reason.strip()
    pay.save()
    for inv in invoices:
        refresh_status(inv)
    receipt = getattr(pay, "receipt", None)
    if receipt:
        receipt.status = ST.CANCELLED
        receipt.save(update_fields=["status", "updated_at"])
    try:
        from finance.rules import reverse_income
        reverse_income(pay)
    except ImportError:
        pass
    record(user, "reverse", pay, f"Reversed {pay}", reason)
    return pay


def credit_note_for(invoice, user, amount, reason):
    if invoice.kind != K.INVOICE:
        raise RuleBroken("Credit notes belong to invoices.", "detail")
    cn = Document.objects.create(kind=K.CREDIT_NOTE, family=invoice.family, currency=invoice.currency,
                                 related=invoice, created_by=user, notes=reason, is_demo=invoice.is_demo)
    Line.objects.create(document=cn, description=f"Credit against {invoice.number}: {reason}", quantity=1,
                        unit_price=Decimal(str(amount)))
    recalc_total(cn)
    return cn


def payment_plan_for(invoice, user, parts):
    """Split what is owed on an invoice into instalments, due a month apart."""
    owed = invoice.outstanding()
    if owed <= 0:
        raise RuleBroken("Nothing is owed on this invoice.", "detail")
    parts = max(2, min(int(parts), 6))
    plan = Document.objects.create(kind=K.PAYMENT_PLAN, family=invoice.family, currency=invoice.currency,
                                   related=invoice, total=owed, created_by=user, is_demo=invoice.is_demo)
    each = (owed / parts).quantize(Decimal("0.01"))
    start = today()
    for i in range(parts):
        amount = each if i < parts - 1 else owed - each * (parts - 1)
        Installment.objects.create(plan=plan, due_date=start + timedelta(days=30 * i), amount=amount)
    return plan


def statement(family, user, currency="USD", start=None, end=None):
    """A dated list of invoices, credits and payments with a running balance, issued as a document."""
    rows = statement_rows(family, currency, start, end)
    doc = Document.objects.create(kind=K.STATEMENT, family=family, currency=currency, created_by=user,
                                  total=rows[-1]["balance"] if rows else Decimal("0"), notes=f"{start or ''} to {end or today()}")
    return issue(doc, user)


def statement_rows(family, currency="USD", start=None, end=None):
    events = []
    for d in Document.objects.filter(family=family, currency=currency, status__in=Document.ISSUED_STATES,
                                     kind__in=[K.INVOICE, K.CREDIT_NOTE]):
        events.append((d.issue_date, d.number, d.get_kind_display(), d.total if d.kind == K.INVOICE else -d.total))
    for p in family.payments.filter(currency=currency):
        events.append((p.received_on, p.reference or "", f"Payment ({p.get_method_display()})", -p.amount))
        if p.reversed_at:
            events.append((p.reversed_at.date(), p.reference or "", "Payment reversed", p.amount))
    events.sort(key=lambda e: (e[0], e[3] < 0))
    rows, balance = [], Decimal("0")
    for when, ref, what, amt in events:
        balance += amt
        if (start and when < start) or (end and when > end):
            continue
        rows.append({"date": when, "reference": ref, "what": what, "amount": amt, "balance": balance})
    return rows


def balances(family):
    """What a family owes, one total per currency. Never added across currencies."""
    out = {}
    for inv in Document.objects.filter(family=family, kind=K.INVOICE, status__in=[ST.ISSUED, ST.PART_PAID]):
        out[inv.currency] = out.get(inv.currency, Decimal("0")) + inv.outstanding()
    credit = {}
    for p in family.payments.filter(reversed_at__isnull=True):
        if p.unallocated() > 0:
            credit[p.currency] = credit.get(p.currency, Decimal("0")) + p.unallocated()
    return {"owed": out, "credit": credit}
