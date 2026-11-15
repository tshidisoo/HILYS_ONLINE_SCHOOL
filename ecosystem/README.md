# HILYS ecosystem

Software for HILYS Languages & Culture Centre, which teaches isiNdebele online to children of Ndebele families abroad.

| Part | For | Folder | Local address |
|---|---|---|---|
| Management system API | everything below | `backend/` | http://127.0.0.1:8000 |
| Staff app | owner, coordinator, finance | `staff-app/` | http://127.0.0.1:3000 |
| Teacher portal | teachers | `teacher-portal/` | http://127.0.0.1:3001 |
| Parent app | parents (phone; also builds for the web) | `mobile/` | http://127.0.0.1:3002 |
| Website enquiry form | visitors | `../public/` | http://127.0.0.1:5500 |

Start here: **`docs/handover.md`** (what exists, how to try it, what is still a draft).

## Run it on your computer

You need Python 3.12 or newer, Node 20 or newer, PostgreSQL 16, Redis 7, and Flutter for the parent app.

```bash
docker compose up -d                       # Postgres and Redis (or run them yourself)
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env                       # DJANGO_DEBUG=1 for local use
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo       # invented demo data; logins in .claude/dev/demo-logins.md
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

In other terminals:

```bash
npm --prefix staff-app install && npm --prefix staff-app run dev          # port 3000
npm --prefix teacher-portal install && npm --prefix teacher-portal run dev  # port 3001
cd backend && .venv/bin/celery -A config worker -l info                   # reminders
cd backend && .venv/bin/celery -A config beat -l info                     # reminder schedule
cd mobile && flutter run -d chrome --dart-define=API_URL=http://127.0.0.1:8000
python3 -m http.server 5500 --directory ../public                         # the website
```

## Apps in the API, by area

- **People and access:** `users` (roles, teachers), `audit` (who did what)
- **Leads and sales:** `leads` (reply clock, trials), `pipeline` (larger deals)
- **Families:** `families` (parents, children, messages)
- **Teaching:** `enrolments` (stages and gates), `lessons` (timetable, attendance, notes, make-ups), `curriculum` (Book 1, checks, certificates)
- **Money:** `catalogue` (price book), `billing` (documents, PDFs, payments), `finance` (accounts, cash flow), `teacherpay`
- **Operations:** `workflow` (tasks, feedback, notifications, reminders), `privacy`
- **Insight:** `analytics` (Home per role, KPIs)
- **Public and app:** `website` (enquiries, document check, survey), `mobile` (parent endpoints), `settings_app`

## Tests

```bash
cd backend && .venv/bin/python manage.py test     # needs Postgres
cd mobile && flutter analyze && flutter test
```

## Deploying

See `docs/deploy-2026-11-first-setup.md`. One Linux server; the server follows the `live` branch. Secrets live only in the server's `backend/.env`.
