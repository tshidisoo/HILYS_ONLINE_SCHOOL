"""Branded PDFs for every billing document and the certificate. Rendered with WeasyPrint from HTML templates."""
import base64
import io
from functools import lru_cache

import qrcode
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML

from branding import tokens
from settings_app.models import CompanySettings

from .rules import statement_rows


@lru_cache(maxsize=1)
def logo_data_uri():
    path = settings.REPO_DIR / tokens.LOGO_FILE
    if not path.exists():
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def qr_data_uri(text):
    buf = io.BytesIO()
    qrcode.make(text, box_size=4, border=1).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def verify_url(code):
    return f"{settings.API_PUBLIC_URL}/verify/{code}"


def _context(extra):
    return {"t": tokens, "company": CompanySettings.get(), "logo": logo_data_uri(), **extra}


def render_document(doc):
    ctx = {"doc": doc, "lines": list(doc.lines.select_related("student")), "qr": qr_data_uri(verify_url(doc.verify_code)),
           "verify_url": verify_url(doc.verify_code), "installments": list(doc.installments.all())}
    if doc.kind == "invoice":
        ctx["paid"], ctx["credited"], ctx["outstanding"] = doc.paid_amount(), doc.credited_amount(), doc.outstanding()
    if doc.kind == "receipt" and doc.payment:
        ctx["allocations"] = list(doc.payment.allocations.select_related("invoice"))
    if doc.kind == "statement":
        ctx["rows"] = statement_rows(doc.family, doc.currency)
    if doc.kind == "agreement":
        ctx["students"] = list(doc.family.students.all())
    html = render_to_string("pdf/document.html", _context(ctx))
    return HTML(string=html).write_pdf()


def render_certificate(cert):
    html = render_to_string("pdf/certificate.html", _context({
        "cert": cert, "qr": qr_data_uri(verify_url(cert.verify_code)), "verify_url": verify_url(cert.verify_code)}))
    return HTML(string=html).write_pdf()
