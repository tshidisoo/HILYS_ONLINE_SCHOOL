# The management system

The staff app is where the business runs. Build the API and the screen for each module together, in the order below, and use each one in the browser before starting the next.

## Patterns every module follows

- **One Django app per area**, with `models.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py`, and a plain module for business rules (`validation.py`, `billing.py`, `scheduling.py`). Views stay thin; rules live in the rules module so the website, app, portal and staff screens all get the same answer.
- **Role-scoped querysets.** Every viewset's `get_queryset` starts from "what may this user see". Internal staff see by role; outside partners and field workers see only their own; customers see only theirs. Write a test per role for every list endpoint.
- **Soft delete** for customer-facing records, with a "Deleted" bin that leadership can restore from.
- **Audit log.** Record who did what to which record for: logins, creates and deletes of customers, every billing document issue or edit, every payment, role changes, overrides of a rule. Leadership can read it; nobody can edit it.
- **Stage history.** Any record with stages keeps a row per change: from, to, who, when, reason where needed.
- **Screens** are one React component with its own CSS file. A list screen has search, filters, sortable columns, pagination, an empty state that says what to do next, a loading state and an error state with a retry. A detail view opens as a modal or side panel with tabs.
- **Forms** use a shared form kit: label, field, hint, inline error under the field, a disabled submit until valid, and the server's error shown in plain words if it still fails.
- **Deep links.** Any record can be opened by URL (`?open=<id>`), so notifications and Home cards can link straight to it.
- **Side menu** grouped by area (Leads and sales, Customers, Operations, Money, Team, Settings), showing only what the role may use.

## Build order and what each module must do

### 1. Users and roles (`users`)
Custom user model with role, phone, `is_suspended`, and helper properties for every permission question (`is_internal_staff`, `is_finance_lead`, `can_own_customers`, `is_partner`, `is_field_worker`, `is_customer`). Partner organisations as their own model, with suspension. Login screen, password change, user management for the owner and admin (create, change role, suspend, reset password). Token authentication that rejects suspended accounts.

### 2. Leads (`leads`)
Sources: website form, app, partner referral, and staff-added (walk-in, WhatsApp, phone, social). Fields: name, phone or email (one is required), what they want, source, owner, status, notes. A reply clock: one working day in the business's time zone, shown as on time, due soon or late. Follow-up ticks, dismiss with a reason, convert to customer. Staff can add one lead or paste a list. Phone numbers are normalised so the local and international forms of the same number match.

### 3. Customers (`customers`)
One record per customer with a type per service line, an owner, contact details, the payer if different, tags, and a timeline of everything that has happened. All rules in `customers/validation.py`:
- Records arriving from the website, app or a partner are never rejected for failing a rule. They are saved, flagged, and listed under "Needs cleanup".
- Duplicates: a matching email or ID number is a hard stop. A matching phone can be overridden only by named senior roles, with a typed reason that goes in the audit log.
- Partner logins skip the duplicate lookup entirely, because showing "this person already exists" leaks another party's customer.

### 4. The unit of work (name the app for the trade)
The industry's core record: its stages, its template per type, its steps, its gates (conditions that block the next stage), its assigned staff or worker, its dates. Board view by stage and list view. Detail view with tabs for steps, documents, notes, billing and history. This module gets the most care; it is what the staff use all day and what the research should have shaped most.

### 5. Catalogue and price book (`catalogue`)
Services or products with description, price, currency, unit, active flag, and whether they show on the website. The price book is the only place a price is typed; quotes and invoices pick from it.

### 6. Pipeline (`pipeline`)
Open opportunities for a customer, a lead, a partner or an organisation not yet on record. Stages with a default chance of winning, value per currency, weighted value, won and lost this month. Marking one lost asks who or what it was lost to and why.

### 7. Billing documents (`billing`)
See `billing-documents.md`. Build this in full.

### 8. Payments (`payments`, inside or beside billing)
A payments desk for the finance lead and owner: record a payment, allocate it to invoices, see unmatched receipts, see what is outstanding and overdue. Reverse or correct a payment with a reason. Payment status on the customer and the invoice is calculated from recorded money; named leadership roles may override it by hand, and the override is logged.

### 9. Simple finance (`finance`)
Accounts (bank, cash, mobile money), income from receipts, expenses with category and receipt photo, transfers between accounts, a cash-flow view by month, and money owed with ageing. Each currency is totalled separately. No tax engine, no statutory reports: export a clean file an accountant's system can take.

### 10. Home (`analytics`, Home screen)
A "my day" page per role: what is due today, what is late, what is waiting on me, new since yesterday, and three or four numbers that matter for that role. Every card links to the filtered list behind it.

### 11. Analytics
Per-role KPIs with a target, the actual and a status colour. Company view for leadership: leads by source, conversion, revenue by service line, outstanding money, work by stage, returning customers. Charts are simple and labelled; follow a data-visualisation skill if one is installed.

### 12. Checklists (`checklists`)
A template per service, items with status and due date, uploads to private storage, and a public link the customer can open without logging in to see what is still needed. Items with expiry dates create reminders.

### 13. Tasks, feedback, notifications
- Tasks: assign, due date, status, linked record.
- Feedback: a survey link per customer sent at the end of the work, answers visible to leadership only.
- Notifications: in-app bell, with email and push behind a switch that stays off until credentials exist. Celery beat jobs for reminders: overdue invoices, expiring quotes, expiring documents, late leads.

### 14. Privacy tools
Data requests (see my data, delete my data) with a status, an export of one customer's records, and a retention note per data type in settings. Sensitive fields encrypted. Opening a sensitive record is logged.

### 15. Website and mobile endpoints (`website`, `mobile`)
Public, throttled endpoints for the catalogue, content, the enquiry or order form and survey links. Authenticated endpoints for the customer's own records, documents, billing documents and messages. Website content the owner will want to change (announcements, testimonials, FAQs, team, blog) is editable from the staff app.

### 16. Industry modules
Each one from the plan, built to the same patterns.

### 17. Settings
Company details used on documents, bank and payment details, document numbering prefixes, reminder timings, lead sources, stages and their default chances, service lines.

## Demo data

A `seed_demo` management command that is safe to run twice. It creates one user per role with obvious names, two partner organisations with a user each, two field workers, and enough customers and work at every stage that no screen is empty: some leads late on the reply clock, an overdue invoice, a part-paid invoice, a fully paid one with a receipt, a returning customer. Names, phones and addresses are invented and fit the country. Write the demo logins to `.claude/dev/demo-logins.md`, which is gitignored, and point to that file from the handover instead of printing passwords in chat.

## Tests

Use Django's test runner against Postgres. Cover at least: every rule in each rules module, role scoping on every list endpoint, the full billing lifecycle (draft, issue, pay in part, pay in full, reverse, credit), document numbering under concurrent issue, duplicate handling, the reply clock across a weekend and across midnight in the business's time zone. All tests pass before the handover, and the handover states the count.
