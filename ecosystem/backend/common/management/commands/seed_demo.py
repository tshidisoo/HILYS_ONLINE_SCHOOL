"""Invented demo data so every screen shows something. Safe to run twice. Every record is flagged as demo."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from billing import rules as billing
from billing.models import Document
from catalogue.models import CatalogueItem
from common.business_time import business_tz, today
from curriculum import rules as curriculum
from curriculum.models import Book
from enrolments.models import Enrolment, StageChange
from families.models import Family, Message, Student
from finance.models import Account, Entry
from leads import rules as lead_rules
from leads.models import Lead
from lessons import rules as lesson_rules
from lessons.models import Lesson
from pipeline.models import Opportunity
from privacy.models import DataRequest
from settings_app.models import CompanySettings
from teacherpay import rules as teacherpay
from users.models import TeacherProfile, User
from website.models import SiteContent
from workflow.models import Feedback, Task
from workflow.notify import notify

PASSWORD = "hilys-demo-2026"
NOTES = ["Practised the greeting and answered “Linjani?” on her own. Please say it together at breakfast.",
         "Read ma me mi mo mu with no help. The click c is still shy: try “icici” at home.",
         "Loved the mopane worm story! Learned umama, ubaba, ugogo. Home task: point and name family members.",
         "Good focus today. We sang the vowel song twice and wrote a e i o u.",
         "Tired after school, so we played the clapping game. Still learned three new words."]


class Command(BaseCommand):
    help = "Create invented demo data. Safe to run twice."

    def handle(self, *args, **opts):
        call_command("import_book1", verbosity=0)
        if User.objects.filter(username="owner", is_demo=True).exists():
            self.stdout.write("Demo data is already there. Nothing changed.")
            return
        with transaction.atomic():
            self.seed()
        self.write_logins()
        self.stdout.write(self.style.SUCCESS("Demo data created. Logins: .claude/dev/demo-logins.md"))

    def user(self, username, first, last, role, **kw):
        u = User.objects.create_user(username=username, password=PASSWORD, first_name=first, last_name=last,
                                     role=role, is_demo=True, email=kw.pop("email", f"{username}@example.com"), **kw)
        return u

    def at(self, day, hh, mm=0):
        return datetime.combine(day, time(hh, mm), tzinfo=business_tz())

    def seed(self):
        s = CompanySettings.get()
        s.email, s.whatsapp = "hello@example.com", "+263 77 000 0000"
        s.save()
        d = today()
        self.owner = self.user("owner", "Owner", "Demo", "owner")
        self.coord = self.user("coordinator", "Coordinator", "Demo", "coordinator")
        self.fin = self.user("finance", "Finance", "Demo", "finance")
        self.t1 = self.user("teacher1", "Nomvula", "Demo-Teacher", "teacher")
        self.t2 = self.user("teacher2", "Sipho", "Demo-Teacher", "teacher")
        TeacherProfile.objects.create(user=self.t1, bio="Teaches Beginner and Book 1.", zoom_link="https://zoom.us/j/0000000001")
        TeacherProfile.objects.create(user=self.t2, bio="Teaches Intermediate and Conversation.", zoom_link="https://zoom.us/j/0000000002")

        P = {}
        for i, (name, kind, lt, per_week, price, unit, draft) in enumerate([
            ("Free trial lesson", "trial", "one_to_one", 0, "0", "per lesson", False),
            ("One-to-one lesson", "lesson", "one_to_one", 0, "12", "per lesson", False),
            ("Group lesson, per child", "lesson", "group", 0, "8", "per lesson", False),
            ("1 a week, one-to-one", "package", "one_to_one", 1, "48", "per month", False),
            ("1 a week, group", "package", "group", 1, "32", "per month", False),
            ("2 a week, one-to-one", "package", "one_to_one", 2, "96", "per month", False),
            ("2 a week, group", "package", "group", 2, "64", "per month", False),
            ("4 a week, one-to-one", "package", "one_to_one", 4, "192", "per month", False),
            ("4 a week, group", "package", "group", 4, "128", "per month", False),
            ("Book 1 video course (self-paced)", "course", "", 0, "39", "once", True),
            ("HILYS Plus", "course", "", 0, "19", "per month", True)]):
            P[name] = CatalogueItem.objects.create(name=name, kind=kind, lesson_type=lt, lessons_per_week=per_week,
                                                   price=Decimal(price), unit=unit, is_draft_price=draft, sort_order=i,
                                                   is_demo=True)

        mob = Account.objects.create(name="Remittances (Mukuru / EcoCash / WU)", kind="mobile", currency="USD",
                                     payment_methods=["mukuru", "ecocash", "western_union"])
        bank = Account.objects.create(name="Bank account", kind="bank", currency="USD", payment_methods=["bank", "card"])
        Account.objects.create(name="Cash", kind="cash", currency="USD", payment_methods=["cash"])

        book = Book.objects.get(code="book-1")
        units = list(book.units.all())

        def family(name, email, phone, country, city, tz, kids, founding=False, login=False):
            f = Family(parent_name=name, email=email, phone=phone, whatsapp=phone, country=country, city=city,
                       time_zone=tz, owner=self.coord, founding_family=founding, source="Website", is_demo=True)
            from families.validation import flag
            flag(f)
            f.save()
            studs = [Student.objects.create(family=f, first_name=k[0], last_name=name.split()[-1], birth_year=d.year - k[1],
                                            level=k[2], is_demo=True, support_notes=k[3] if len(k) > 3 else "") for k in kids]
            if login:
                u = self.user(email.split("@")[0], name.split()[0], name.split()[-1], "parent", email=email, time_zone=tz)
                f.login = u
                f.save(update_fields=["login"])
            return f, studs

        self.f1, (thandi, sizwe) = family("Nomsa Ndlovu", "parent1@example.com", "07700 900123", "GB", "Leeds", "Europe/London",
                                          [("Thandi", 7, "beginner", "Shy on camera at first; give her time to answer."), ("Sizwe", 9, "beginner")], founding=True, login=True)
        self.f2, (lindo,) = family("Bongani Moyo", "parent2@example.com", "0491 570 156", "AU", "Perth", "Australia/Perth",
                                   [("Lindiwe", 8, "intermediate")], login=True)
        self.f3, (nkosi,) = family("Rudo Sibanda", "rudo.sibanda@example.com", "+1 202 555 0143", "US", "Houston", "America/Chicago",
                                   [("Nkosana", 11, "beginner")])
        self.f4, (zodwa,) = family("Themba Dube", "", "+27 21 555 0199", "ZA", "Cape Town", "Africa/Johannesburg",
                                   [("Zodwa", 6, "beginner")])
        self.f5, (ayanda,) = family("Sibusiso Khumalo", "s.khumalo@example.com", "07700 900456", "GB", "Birmingham", "Europe/London",
                                    [("Ayanda", 10, "conversation")])

        def enrol(student, teacher, pkg, slots, stage, group="", started_days_ago=60):
            e = Enrolment.objects.create(student=student, teacher=teacher, package=P[pkg], book=book, level=student.level,
                                         weekly_slots=slots, stage=stage, group_name=group, is_demo=True,
                                         start_date=d - timedelta(days=started_days_ago))
            prev = ""
            for st in ["trial", "waiting", "active", "paused", "finished"][: ["trial", "waiting", "active", "paused", "finished"].index(stage) + 1]:
                if st == "paused":
                    StageChange.objects.create(enrolment=e, from_stage=prev, to_stage="paused", by=self.coord, reason="Family travelling to Zimbabwe for December")
                elif prev != st:
                    StageChange.objects.create(enrolment=e, from_stage=prev, to_stage=st, by=self.coord)
                prev = st
            return e

        e_thandi = enrol(thandi, self.t1, "2 a week, group", [{"weekday": 1, "time": "18:30"}, {"weekday": 3, "time": "18:30"}], "active", "Ndlovu siblings")
        e_sizwe = enrol(sizwe, self.t1, "2 a week, group", [{"weekday": 1, "time": "18:30"}, {"weekday": 3, "time": "18:30"}], "active", "Ndlovu siblings")
        e_lindo = enrol(lindo, self.t2, "1 a week, one-to-one", [{"weekday": 5, "time": "09:00"}], "active")
        e_nkosi = enrol(nkosi, self.t1, "4 a week, one-to-one", [{"weekday": w, "time": "16:00"} for w in (0, 1, 3, 4)], "active", started_days_ago=200)
        e_zodwa = enrol(zodwa, self.t2, "1 a week, group", [{"weekday": 2, "time": "15:00"}], "waiting")
        e_ayanda = enrol(ayanda, self.t2, "2 a week, one-to-one", [{"weekday": 0, "time": "19:00"}, {"weekday": 2, "time": "19:00"}], "paused")

        # Past lessons: reported, with notes and the Book 1 lesson taught.
        def past_lessons(e, weeks, start_unit=0, unreported_last=False):
            made, ui = [], start_unit
            for w in range(weeks, 0, -1):
                for slot in e.weekly_slots:
                    day = d - timedelta(days=7 * w)
                    day = day - timedelta(days=(day.weekday() - slot["weekday"]) % 7)
                    hh, mm = (int(x) for x in slot["time"].split(":"))
                    ls = Lesson.objects.create(enrolment=e, teacher=e.teacher, starts_at=self.at(day, hh, mm), is_demo=True)
                    made.append(ls)
            for i, ls in enumerate(made):
                if unreported_last and i == len(made) - 1:
                    continue
                status = "taught"
                if i % 9 == 4:
                    status = "missed"
                elif i % 11 == 6:
                    status = "cut_short"
                ls.status, ls.reported_at = status, ls.starts_at + timedelta(hours=2)
                if status == "taught":
                    ls.unit = units[min(ui, len(units) - 1)]
                    ui += 1
                    ls.parent_note = NOTES[i % len(NOTES)]
                    ls.private_note = "Ready to move on." if i % 3 == 0 else ""
                elif status == "missed":
                    ls.parent_note = "Thandi did not join today. This lesson counts as used (no 24 hours' notice)."
                else:
                    ls.parent_note = "The power went off after 15 minutes. A make-up lesson is owed."
                    ls.makeup_owed = True
                ls.save()
            return made

        past_lessons(e_thandi, 6, 0)
        past_lessons(e_sizwe, 6, 0, unreported_last=True)
        past_lessons(e_lindo, 5, 10)
        nk = past_lessons(e_nkosi, 9, 0)
        for e in (e_thandi, e_sizwe, e_lindo, e_nkosi):
            lesson_rules.schedule_month(e, d.year, d.month)
            ny, nm = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
            lesson_rules.schedule_month(e, ny, nm)
        Lesson.objects.filter(enrolment__in=[e_thandi, e_sizwe, e_lindo, e_nkosi], status="scheduled",
                              starts_at__lt=timezone.now()).exclude(pk=Lesson.objects.filter(enrolment=e_sizwe).order_by("-starts_at").filter(starts_at__lt=timezone.now()).values("pk")[:1]).update(
            status="taught", reported_at=timezone.now(), parent_note=NOTES[0])
        # Nkosana finished all of Book 1: make sure every unit is covered, then the end-of-book check and certificate.
        done = set(Lesson.objects.filter(enrolment=e_nkosi, status="taught", unit__isnull=False).values_list("unit_id", flat=True))
        missing = [u for u in units if u.pk not in done]
        for i, u in enumerate(missing):
            Lesson.objects.create(enrolment=e_nkosi, teacher=self.t1, starts_at=self.at(d - timedelta(days=120 - i), 16), status="taught",
                                  unit=u, parent_note=f"Covered {u.title_en}.", reported_at=timezone.now() - timedelta(days=100), is_demo=True)
        curriculum.record_check(nkosi, book, self.t1, [True, True, True, True, False, True], d - timedelta(days=3),
                                "Practise reading sentences aloud: Lessons 30–34.", is_demo=True)

        # Money: part-paid, paid with receipt, overdue, quotation, credit note, payment plan.
        def invoice(fam, period, lines, issued_days_ago, by=self.coord):
            inv = Document.objects.create(kind="invoice", family=fam, period=period, created_by=by, is_demo=True)
            billing.set_lines(inv, lines)
            inv.issue_date = d - timedelta(days=issued_days_ago)
            inv.due_date = inv.issue_date + timedelta(days=7)
            billing.issue(inv, by)
            return inv

        prev_m = (d.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        this_m = d.strftime("%Y-%m")
        two_ago = ((d.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        pk2 = P["2 a week, group"]
        for period, ago in ((two_ago, 62), (prev_m, 32)):
            inv = invoice(self.f1, period, [{"item": pk2.pk, "description": f"{pk2.name} – {period}", "unit_price": pk2.price, "student": s.pk} for s in (thandi, sizwe)], ago)
            billing.record_payment(self.fin, self.f1, inv.total, "USD", "mukuru", inv.issue_date + timedelta(days=3), f"MK{inv.pk:06d}", is_demo=True)
        inv_now = invoice(self.f1, this_m, [{"item": pk2.pk, "description": f"{pk2.name} – {this_m}", "unit_price": pk2.price, "student": s.pk} for s in (thandi, sizwe)], 2)
        billing.record_payment(self.fin, self.f1, Decimal("64"), "USD", "ecocash", d - timedelta(days=1), "EC4471920", is_demo=True)
        inv_l = invoice(self.f2, this_m, [{"item": P["1 a week, one-to-one"].pk, "description": f"1 a week, one-to-one – {this_m}", "unit_price": "48", "student": lindo.pk}], 3)
        billing.record_payment(self.fin, self.f2, Decimal("48"), "USD", "western_union", d - timedelta(days=1), "WU 813 442 9910", is_demo=True)
        inv_n = invoice(self.f3, prev_m, [{"item": P["4 a week, one-to-one"].pk, "description": f"4 a week, one-to-one – {prev_m}", "unit_price": "192", "student": nkosi.pk}], 40)
        billing.payment_plan_for(inv_n, self.fin, 3)
        plan = Document.objects.filter(kind="payment_plan", related=inv_n).first()
        billing.issue(plan, self.fin)
        inv_n2 = invoice(self.f3, this_m, [{"item": P["4 a week, one-to-one"].pk, "description": f"4 a week, one-to-one – {this_m}", "unit_price": "192", "student": nkosi.pk}], 1)
        cn = billing.credit_note_for(inv_n2, self.owner, Decimal("12"), "One lesson cancelled by HILYS and not made up")
        billing.issue(cn, self.owner)
        q = Document.objects.create(kind="quotation", family=self.f4, created_by=self.coord, is_demo=True,
                                    notes="Zodwa can join the Saturday group from next month.")
        billing.set_lines(q, [{"item": P["1 a week, group"].pk, "description": "1 a week, group – first month", "unit_price": "32", "student": zodwa.pk}])
        billing.issue(q, self.coord)
        agr = Document.objects.create(kind="agreement", family=self.f1, created_by=self.coord, is_demo=True, is_draft_text=True)
        billing.issue(agr, self.coord)
        Document.objects.create(kind="invoice", family=self.f5, created_by=self.coord, is_demo=True, period=this_m,
                                notes="Draft: Ayanda is paused, check before issuing.")
        wrong = billing.record_payment(self.fin, self.f2, Decimal("20"), "USD", "cash", d - timedelta(days=5), "CASH-001",
                                       note="Recorded against the wrong family", allocations=[], is_demo=True)
        billing.reverse_payment(wrong, self.fin, "Recorded against the wrong family by mistake")
        billing.record_payment(self.fin, self.f5, Decimal("30"), "USD", "bank", d - timedelta(days=2), "BANK-REF-77",
                               note="Paid ahead; not matched yet", allocations=[], is_demo=True)
        for amt, cat, note, ago in [("25", "Internet and data", "Teacher data bundles", 10), ("15", "Software", "Zoom subscription", 8),
                                    ("6.5", "Transfer fees", "Mukuru collection fee", 30), ("40", "Marketing", "Facebook ads for families in the UK", 20)]:
            Entry.objects.create(account=mob if cat != "Software" else bank, kind="expense", amount=Decimal(amt), currency="USD",
                                 category=cat, on_date=d - timedelta(days=ago), note=note, recorded_by=self.fin, is_demo=True)

        # Leads: late, due soon, needs cleanup, trial booked and done, dismissed.
        now = timezone.now()
        late = lead_rules.create_lead({"parent_name": "Precious Mpofu", "phone": "07700 900789", "email": "precious@example.com", "country": "GB",
                                       "child_name": "Ntando", "child_age": 8, "message": "Can my son join a Saturday group?"},
                                      "Website", is_demo=True, received_at=now - timedelta(days=4))
        lead_rules.create_lead({"parent_name": "Lwazi Nkomo", "phone": "+61 491 570 110", "child_name": "Busi", "child_age": 6,
                                "interest": "video", "message": "Interested in the video course."}, "Level check", is_demo=True)
        lead_rules.create_lead({"parent_name": "", "phone": "12345", "child_name": "?", "child_age": 40,
                                "message": "pls call"}, "Website", is_demo=True)
        trial_lead = lead_rules.create_lead({"parent_name": "Grace Ncube", "email": "grace.ncube@example.com", "phone": "07700 900321",
                                             "country": "GB", "time_zone": "Europe/London", "child_name": "Mandla", "child_age": 9},
                                            "WhatsApp", owner=self.coord, is_demo=True, received_at=now - timedelta(days=3))
        lead_rules.mark_replied(trial_lead, self.coord, "Called; booked a trial")
        trial_lead.status = "trial_booked"
        trial_lead.save()
        Lesson.objects.create(kind="trial", lead=trial_lead, teacher=self.t1, starts_at=self.at(d + timedelta(days=1), 17), is_demo=True)
        done_lead = lead_rules.create_lead({"parent_name": "Joseph Tshuma", "email": "j.tshuma@example.com", "phone": "+1 202 555 0177",
                                            "country": "US", "time_zone": "America/New_York", "child_name": "Nandi", "child_age": 7},
                                           "Referral from a family", owner=self.coord, is_demo=True, received_at=now - timedelta(days=6))
        lead_rules.mark_replied(done_lead, self.coord)
        tl = Lesson.objects.create(kind="trial", lead=done_lead, teacher=self.t1, starts_at=self.at(d - timedelta(days=2), 15), is_demo=True)
        lesson_rules.report(tl, self.t1, "taught", "Nandi knew a few greetings and was keen. Beginner is right for her.", "", None, "beginner")
        dl = lead_rules.create_lead({"parent_name": "Mercy Gumede", "email": "mercy@example.com", "child_name": "Sam"}, "Facebook", is_demo=True)
        lead_rules.dismiss(dl, "Wanted Zulu lessons, not isiNdebele")
        lead_rules.create_lead({"parent_name": "Ruth Mlilo", "email": "ruth.mlilo@example.com", "country": "GB", "child_name": "Tendai",
                                "child_age": 10, "interest": "plus"}, "Website", is_demo=True, received_at=now - timedelta(hours=22))
        for lead in Lead.objects.filter(is_demo=True):
            lead.is_demo = True
            lead.save(update_fields=["is_demo"])

        # Pipeline, tasks, messages, feedback, content, privacy, teacher pay.
        for title, org, stage, value, fam in [
            ("Zimbabwe Association of Leeds: Saturday group", "Zimbabwe Association of Leeds", "talking", "640", None),
            ("Three Ndlovu cousins joining", "", "offer", "192", self.f1),
            ("Heritage school pilot term (Birmingham)", "Birmingham Saturday Heritage School", "trial", "1200", None),
            ("Tshuma family: two children", "", "won", "128", None)]:
            o = Opportunity.objects.create(title=title, organisation=org, stage=stage, chance=Opportunity.DEFAULT_CHANCE[stage],
                                           value=Decimal(value), family=fam, owner=self.owner, is_demo=True,
                                           closed_on=d if stage == "won" else None)
        Opportunity.objects.create(title="Church youth group, Manchester", organisation="Manchester youth group", stage="lost", chance=0,
                                   value=Decimal("300"), owner=self.owner, closed_on=d - timedelta(days=4), lost_to="A volunteer teacher",
                                   lost_reason="They chose a free volunteer for now", is_demo=True)
        Task.objects.create(title="Book a make-up lesson for the Ndlovu siblings", assignee=self.coord, due_on=d, created_by=self.owner, is_demo=True)
        Task.objects.create(title="Chase the Sibanda payment plan instalment", assignee=self.fin, due_on=d - timedelta(days=1), created_by=self.owner, is_demo=True)
        Task.objects.create(title="Send the pilot video to five families", assignee=self.owner, due_on=d + timedelta(days=5), created_by=self.owner, is_demo=True)
        Message.objects.create(family=self.f1, sender=self.f1.login, body="Sawubona! Can Thandi's Thursday lesson move to 7pm UK time next week?", is_demo=True)
        Message.objects.create(family=self.f1, sender=self.coord, body="Yebo! Moved to Thursday 19:00 UK time. Ngiyabonga.", read_by_staff=True, is_demo=True)
        Message.objects.create(family=self.f2, sender=self.f2.login, body="Lindiwe loved the folktale today.", is_demo=True)
        Feedback.objects.create(family=self.f3, reason="End of Book 1", sent_at=now - timedelta(days=2), answered_at=now - timedelta(days=1),
                                rating=5, would_recommend=True, best="Nkosana can greet his grandmother now.", improve="More songs please!",
                                may_quote=True, is_demo=True)
        Feedback.objects.create(family=self.f1, reason="First month", sent_at=now - timedelta(days=1), is_demo=True)
        SiteContent.objects.create(kind="announcement", title="Video lessons coming soon", body="Book 1 video lessons are being recorded.", is_published=True, is_demo=True)
        SiteContent.objects.create(kind="testimonial", title="He can greet his grandmother now", body="Nkosana can greet his grandmother now.",
                                   author="Rudo, Houston (demo)", is_published=False, is_demo=True)
        DataRequest.objects.create(family=self.f5, requester="Sibusiso Khumalo", kind="see", due_on=d + timedelta(days=20),
                                   notes="Asked by WhatsApp for a copy of everything held.", handled_by=self.owner, is_demo=True)
        pm = d.replace(day=1) - timedelta(days=1)
        for t in (self.t1, self.t2):
            st = teacherpay.build(t, pm.year, pm.month)
            st.is_demo = True
            st.save()
            teacherpay.build(t, d.year, d.month)
        st1 = teacherpay.build(self.t1, pm.year, pm.month)
        if not st1.unreported:
            teacherpay.approve(st1, self.fin)
        notify([self.owner, self.coord], "Late reply: Precious Mpofu", "This lead has waited more than one working day.", f"/leads?open={late.pk}", key="demo-late")
        notify([self.owner, self.fin], "Overdue invoice for the Sibanda family", "A payment plan is in place.", f"/documents?open={inv_n.pk}", key="demo-overdue")

    def write_logins(self):
        path = Path(settings.BASE_DIR).parent / ".claude" / "dev" / "demo-logins.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"""# Demo logins (local only, gitignored)

Every demo account uses the password `{PASSWORD}`.

| Username | Role | App | Shows |
|---|---|---|---|
| owner | Owner | Staff app (port 3000) | Everything, audit log, feedback, overrides |
| coordinator | Coordinator | Staff app | Leads, families, enrolments, timetable |
| finance | Finance | Staff app | Documents, payments desk, money, teacher pay |
| teacher1 | Teacher (Nomvula) | Teacher portal (port 3001) | Ndlovu siblings, Nkosana, trials |
| teacher2 | Teacher (Sipho) | Teacher portal | Lindiwe, Zodwa, Ayanda |
| parent1 | Parent (Nomsa Ndlovu, UK) | Parent app (port 3002) | Two children, part-paid invoice |
| parent2 | Parent (Bongani Moyo, Perth) | Parent app | One child, paid invoice |

""")
