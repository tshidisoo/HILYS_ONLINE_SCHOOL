# HILYS ecosystem plan

Written 2026-11-15. A record of decisions, not a gate. Assumptions are listed in `brainstorms/2026-11-15-assumptions.md`.

## The business in five lines

1. HILYS Languages & Culture Centre teaches isiNdebele online to children of Ndebele families abroad (UK, South Africa, Australia, US).
2. It sells monthly packages of live 30-minute Zoom lessons (one-to-one or groups of up to 3), and is preparing a Book 1 video course with subscriptions.
3. Parents pay, in USD, by Mukuru, EcoCash Diaspora or Western Union.
4. Teachers deliver the lessons from Zimbabwe: Sija now, more freelance teachers later.
5. Every course carries culture: folktales, songs and food.

## The golden path

A parent finds the website → does the level check or asks for a free trial → the request arrives as a **lead** with a reply clock (one working day, Harare time) → staff book a **trial lesson** with a teacher → the teacher records the trial in the **teacher portal** and sets the child's level → staff convert the lead into a **family** with a **student**, and create an **enrolment** (level, package, teacher, weekly times) → an **invoice** for the month is issued from the price book → the parent pays by Mukuru and finance **records the payment** against the invoice → a **receipt** PDF is issued → the teacher teaches, records **attendance and lesson notes** for each lesson → the parent sees the timetable in their own time zone, lesson notes, Book 1 progress and invoices in the **parent app** → at the end of Book 1 the teacher records the **end-of-book check** → a **certificate** is issued → a **feedback** link goes to the parent; answers reach leadership only. Taught lessons feed **teacher pay**.

## Folder map

| Folder | What it is | Future address |
|---|---|---|
| `backend/` | Django API, Celery worker and beat | `api.<domain>` |
| `staff-app/` | React staff app | `admin.<domain>` |
| `teacher-portal/` | React portal for teachers | `teachers.<domain>` |
| `mobile/` | Flutter parent app | app stores |
| `../public/` (existing) | The existing plain HTML website; its forms post to the API | `<domain>` |
| `docs/`, `projects/`, `brainstorms/` | Runbooks and handover; plans; decisions | – |

## Django apps by area

| Area | Apps |
|---|---|
| People and access | `users` (roles, teachers, parents), `audit` |
| Leads and sales | `leads`, `pipeline` |
| Families | `families` (family = the paying customer; students = the children) |
| Teaching (the unit of work) | `enrolments` (stages, gates), `lessons` (timetable, attendance, notes), `curriculum` (levels, Book 1 lessons, progress, checks, certificates) |
| Money | `catalogue` (price book), `billing` (documents, payments, allocations), `finance` (accounts, expenses, cash flow), `teacherpay` |
| Operations | `tasks`, `feedback`, `notifications`, `privacy` |
| Insight | `analytics` (Home per role, KPIs) |
| Public and app | `website` (public endpoints), `mobile` (parent endpoints), `settings_app` (company settings) |

## Roles

| Role | Who | Sees and does |
|---|---|---|
| Owner | The founder | Everything; approves overrides; reads audit log and feedback |
| Coordinator (admin) | Office staff | Leads, families, enrolments, timetable, documents (issue, not payments), tasks |
| Finance | Finance lead | Billing documents, payments desk, finance, teacher pay |
| Teacher | Sija and freelance teachers (outside party, teacher portal) | Only their own students, lessons, trial lessons and pay statements |
| Parent | A family's payer (mobile app) | Only their own family: children, timetable, notes, progress, documents, messages |

Several people can hold one role. Only finance and the owner record payments.

## Record stages

**Lead:** New → Contacted → Trial booked → Trial done → Converted | Dismissed (with reason).

**Enrolment (the unit of work):** Trial → Waiting to start → Active → Paused → Finished | Stopped.
Gates: *Waiting to start* needs a level and a teacher; *Active* needs weekly times and an issued invoice for the first month; *Finished* for Book 1 needs an end-of-book check of 3 or more out of 6.

**Lesson (attendance):** Scheduled → Taught | Moved (24h notice) | Missed (counts as used) | Cancelled by HILYS | Cut short (power or internet). Cancelled and Cut short owe a make-up.

**Billing documents:** Draft → Issued → Part paid → Paid | Cancelled; credit notes against issued invoices.

## Modules

**Core (built):** users and roles; leads with reply clock; families and students with rules; enrolments; timetable and attendance; price book; pipeline; billing documents (quotation, invoice, receipt, credit note, payment plan, statement, enrolment agreement) with PDFs and verification codes; payments desk with allocations and reversals; simple finance; Home per role; analytics; tasks; feedback; notifications; privacy tools; website and parent-app endpoints; settings; audit log; soft delete bin.

**Industry (built):** curriculum and progress (Book 1's 35 lessons from `materials/book1/lessons.py`, levels, end-of-book check, certificates); teacher pay statements; video-course waiting list and subscriptions; trial lesson booking.

**Later (named, not built):** online card payments (Stripe), partner portal for associations and heritage schools, paid video access control, SMS reminders, group-class scheduling optimiser, Book 1b curriculum content.

## Price book (draft, from the live website)

| Service | Price (USD) |
|---|---|
| One-to-one lesson | 12.00 per lesson |
| Group lesson (up to 3), per child | 8.00 per lesson |
| 1 a week, one-to-one / group | 48.00 / 32.00 per month |
| 2 a week, one-to-one / group | 96.00 / 64.00 per month |
| 4 a week, one-to-one / group | 192.00 / 128.00 per month |
| Self-paced video course | 39.00 once, or 9.00 per month (draft) |
| HILYS Plus | 19.00 per month (draft) |
| Free trial lesson | 0.00 |

## Stack (defaults: the stack reference file was not supplied)

Django 5.2 LTS, Django REST Framework, PostgreSQL 16, Redis 7, Celery 5; React 18 with Vite; Flutter stable. Local ports: API 8000, staff app 3000, teacher portal 3001, parent app (web build) 3002, existing website 5500. One API for the website, staff app, portal and app (no second website backend).
