# HILYS ecosystem

The software that runs HILYS Languages & Culture Centre: a management system (Django API and React staff app), a teacher portal, a Flutter parent app, and the enquiry form on the existing website in `../public/`.

## Where truth lives

- **Git** for what is built.
- **`projects/ecosystem-foundation/plan.md`** for decisions: roles, stages, modules, price book.
- **`docs/handover.md`** is a dated snapshot for the owner, not a live status page.
- **`brainstorms/`** holds decision records and assumptions.

## Map

| Folder | What it is | Production address |
|---|---|---|
| `backend/` | Django 5.2 + DRF API, Celery worker and beat | `api.<domain>` |
| `staff-app/` | React staff app (Vite) | `admin.<domain>` |
| `teacher-portal/` | React teacher portal (Vite) | `teachers.<domain>` |
| `mobile/` | Flutter parent app | app stores; web build optional |
| `../public/` | The existing static website; its forms post to `/api/public/enquiry/` | `<domain>` |
| `docs/` | Runbooks, handover, screenshots | – |
| `projects/`, `brainstorms/` | Plans and decision records | – |

## Where new things go

- Runbooks: `docs/deploy-YYYY-MM-<topic>.md`, with rollback in its own section.
- Plans: `projects/<name>/`. Decisions: `brainstorms/YYYY-MM-DD-<topic>.md`.
- Seed scripts and demo logins: `.claude/dev/` (gitignored). Nothing new in the `ecosystem/` root.

## Local development

- Postgres 16 and Redis 7: `docker compose up -d`, or local services. Backend tests need Postgres (SQLite gives false results).
- API: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cp .env.example .env`, then `.venv/bin/python manage.py migrate && .venv/bin/python manage.py seed_demo && .venv/bin/python manage.py runserver 127.0.0.1:8000`.
- Worker and beat: `.venv/bin/celery -A config worker -l info` and `.venv/bin/celery -A config beat -l info`.
- Staff app `npm --prefix staff-app run dev` (port 3000); teacher portal `npm --prefix teacher-portal run dev` (3001); both proxy `/api` to 8000.
- Parent app: `cd mobile && flutter run -d chrome --dart-define=API_URL=http://127.0.0.1:8000`, or `flutter build web --no-web-resources-cdn` and serve `build/web` on 3002.
- Website: serve `../public` on 5500; on localhost its forms use the local API.
- Tests: `cd backend && .venv/bin/python manage.py test`; `cd mobile && flutter analyze && flutter test`.

## Deploying

One Linux server, no Docker. The server follows the `live` branch; moving `live` is the act of deploying and happens only on the owner's explicit yes. Systemd services `hilys-backend` (gunicorn), `hilys-celery-worker`, `hilys-celery-beat` restart separately; a beat schedule change needs a beat restart. Frontends build on the server. The assistant never connects to the production server: it writes the commands and the owner runs them.

## Committing

Stage named paths; never `git add -A`. Commit or push only when asked. Never commit secrets, `.env`, dumps, media or `node_modules`.

## Working with the owner

- Money features are verified by posting and reversing through the real screens, not only by tests.
- Anything public-facing (prices, promises, legal text, website content) needs the owner's explicit yes, and stays marked as draft until then.
- HILYS has no physical address: documents and pages show email, WhatsApp and the website only.

## Rule modules (one place per rule; never add a second copy)

| Record | Rules live in |
|---|---|
| Leads, reply clock | `backend/leads/rules.py`, `backend/common/business_time.py` |
| Families, duplicates, cleanup | `backend/families/validation.py` |
| Enrolment stages and gates | `backend/enrolments/rules.py` |
| Lessons, attendance, make-ups, monthly timetable | `backend/lessons/rules.py` |
| Book progress, end-of-book check, certificates | `backend/curriculum/rules.py` |
| Documents, payments, allocations, reversals, credit notes, statements | `backend/billing/rules.py` |
| Document numbering | `backend/billing/numbering.py` |
| Cash flow, accounts, money owed | `backend/finance/rules.py` |
| Teacher pay | `backend/teacherpay/rules.py` |
| Who may do what | helper properties on `backend/users/models.py` (`User`); views never compare role strings |
