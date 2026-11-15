from collections import defaultdict
from decimal import Decimal

from common.business_time import today
from common.errors import RuleBroken

from .models import Account, Entry


def account_for(method, currency):
    for acc in Account.objects.filter(is_active=True, currency=currency):
        if method in (acc.payment_methods or []):
            return acc
    acc, _ = Account.objects.get_or_create(name=f"Unsorted {currency}", currency=currency,
                                           defaults={"kind": Account.Kind.CASH})
    return acc


def income_from_payment(pay):
    Entry.objects.create(account=account_for(pay.method, pay.currency), kind=Entry.Kind.INCOME, amount=pay.amount,
                         currency=pay.currency, category="Lesson fees", on_date=pay.received_on,
                         note=f"Payment from {pay.family}", payment=pay, recorded_by=pay.recorded_by, is_demo=pay.is_demo)


def reverse_income(pay):
    for e in Entry.objects.filter(payment=pay, kind=Entry.Kind.INCOME):
        Entry.objects.create(account=e.account, kind=Entry.Kind.EXPENSE, amount=e.amount, currency=e.currency,
                             category="Lesson fees", on_date=today(), note=f"Reversal: {pay.reversed_reason}",
                             payment=pay, recorded_by=pay.reversed_by, is_demo=pay.is_demo)


def transfer(user, from_acc, to_acc, amount, on_date, note=""):
    if from_acc.currency != to_acc.currency:
        raise RuleBroken("Both accounts must use the same currency. Record an exchange as money out and money in.", "to_account")
    amount = Decimal(str(amount))
    if amount <= 0:
        raise RuleBroken("The amount must be more than zero.", "amount")
    Entry.objects.create(account=from_acc, kind=Entry.Kind.TRANSFER_OUT, amount=amount, currency=from_acc.currency,
                         category="Transfer", on_date=on_date, note=note, recorded_by=user)
    Entry.objects.create(account=to_acc, kind=Entry.Kind.TRANSFER_IN, amount=amount, currency=to_acc.currency,
                         category="Transfer", on_date=on_date, note=note, recorded_by=user)


def signed(e):
    return e.amount if e.kind in (Entry.Kind.INCOME, Entry.Kind.TRANSFER_IN) else -e.amount


def account_balances():
    out = []
    for acc in Account.objects.filter(is_active=True):
        bal = sum((signed(e) for e in acc.entries.all()), Decimal("0"))
        out.append({"id": acc.pk, "name": acc.name, "kind": acc.get_kind_display(), "currency": acc.currency, "balance": bal})
    return out


def cash_flow(months=6):
    """Money in and out per month, one table per currency. Transfers are left out: they move money, not earn it."""
    data = defaultdict(lambda: defaultdict(lambda: {"in": Decimal("0"), "out": Decimal("0")}))
    for e in Entry.objects.exclude(kind__in=[Entry.Kind.TRANSFER_IN, Entry.Kind.TRANSFER_OUT]):
        key = e.on_date.strftime("%Y-%m")
        data[e.currency][key]["in" if e.kind == Entry.Kind.INCOME else "out"] += e.amount
    result = {}
    for cur, by_month in data.items():
        rows = [{"month": m, "in": v["in"], "out": v["out"], "net": v["in"] - v["out"]}
                for m, v in sorted(by_month.items())][-months:]
        result[cur] = rows
    return result


def money_owed_ageing():
    """Outstanding invoices by how late they are, per currency."""
    from billing.models import Document
    buckets = ["Not due yet", "1–30 days late", "31–60 days late", "Over 60 days late"]
    out = defaultdict(lambda: {b: Decimal("0") for b in buckets})
    d = today()
    for inv in Document.objects.filter(kind="invoice", status__in=["issued", "part_paid"]):
        owed = inv.outstanding()
        late = (d - inv.due_date).days if inv.due_date else 0
        b = buckets[0] if late <= 0 else buckets[1] if late <= 30 else buckets[2] if late <= 60 else buckets[3]
        out[inv.currency][b] += owed
    return {cur: [{"bucket": b, "amount": v[b]} for b in buckets] for cur, v in out.items()}
