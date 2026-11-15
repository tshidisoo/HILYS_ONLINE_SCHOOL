from django.db import models


class CompanySettings(models.Model):
    """One row. Used on documents, the website and reminders. HILYS has no physical address, so none is shown."""
    name = models.CharField(max_length=120, default="HILYS Languages & Culture Centre")
    short_name = models.CharField(max_length=40, default="HILYS")
    motto = models.CharField(max_length=120, default="Diversity is power")
    email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    website = models.URLField(default="https://hilys-languages.web.app")
    payment_details = models.TextField(blank=True, default=(
        "Pay by Mukuru, EcoCash Diaspora or Western Union. Send the reference on WhatsApp so we can match your payment."))
    invoice_prefix = models.CharField(max_length=8, default="INV")
    quotation_prefix = models.CharField(max_length=8, default="QUO")
    receipt_prefix = models.CharField(max_length=8, default="REC")
    credit_note_prefix = models.CharField(max_length=8, default="CRN")
    payment_plan_prefix = models.CharField(max_length=8, default="PLN")
    statement_prefix = models.CharField(max_length=8, default="STM")
    agreement_prefix = models.CharField(max_length=8, default="AGR")
    certificate_prefix = models.CharField(max_length=8, default="CERT")
    invoice_due_days = models.PositiveSmallIntegerField(default=7)
    quotation_valid_days = models.PositiveSmallIntegerField(default=14)
    lead_reply_working_days = models.PositiveSmallIntegerField(default=1)
    retention_notes = models.TextField(blank=True, default=(
        "Families and children: kept while lessons continue, then 2 years, then deleted on request or by review.\n"
        "Lesson notes: kept with the family record.\n"
        "Invoices, receipts and payments: kept 6 years for tax.\n"
        "Leads who never started: deleted after 12 months.\n"
        "Feedback answers: kept 2 years, shown to leadership only."))
    lead_sources = models.JSONField(default=list)

    class Meta:
        verbose_name_plural = "company settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"lead_sources": [
            "Website", "Level check", "Parent app", "WhatsApp", "Phone", "Referral from a family", "Facebook", "Walk-in"]})
        return obj
