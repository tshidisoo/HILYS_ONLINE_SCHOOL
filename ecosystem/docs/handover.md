# HILYS ecosystem: handover

**Date:** 15 November 2026 · Built with the ecosystem-builder skill · Branch `ecosystem` of `tshidisoo/HILYS_ONLINE_SCHOOL`

## 1. What you have

| Part | What it does | Screenshots |
|---|---|---|
| **Staff app** | Runs HILYS day to day: leads with a one-working-day reply clock, families and children, the enrolment board, the weekly timetable, Book 1 progress and certificates, documents, the payments desk, money in and out, teacher pay, pipeline, analytics, tasks, feedback, team logins, website content, privacy, audit log and settings. | `docs/screenshots/staff-app/` |
| **Teacher portal** | Phone-first. A teacher sees only their own lessons (Harare time and the family's time), reports each lesson with a note for the parent, follows each child's Book 1 progress, records the end-of-book check, and sees their pay. | `docs/screenshots/teacher-portal/` |
| **Parent app** (Flutter) | A parent sees the next lesson in their own time zone with a Zoom button, lesson notes, each child's Book 1 progress, invoices and receipts as PDFs, and can message HILYS. | `docs/screenshots/parent-app/` |
| **Website enquiry form** | The free-trial, waiting-list and level-check buttons on your existing website open one short form. Each enquiry lands in the staff app as a lead. | `docs/screenshots/website/` |
| **Documents** | Branded PDFs: quotation, invoice, receipt, credit note, payment plan, statement, enrolment agreement and the Book 1 certificate. Each has a code and QR that anyone can check at `/verify/<code>`. | `docs/screenshots/pdfs/` |

## 2. How to start it on your computer

Follow `README.md` ("Run it on your computer"). Then open:

- Staff app: http://127.0.0.1:3000
- Teacher portal: http://127.0.0.1:3001
- Parent app (web build): http://127.0.0.1:3002
- Website: http://127.0.0.1:5500

## 3. Demo logins

After `seed_demo`, the logins are in **`.claude/dev/demo-logins.md`** (kept out of git). All use the same demo password written in that file.

- `owner`, `coordinator`, `finance`: the staff app, each seeing what their role may see.
- `teacher1`, `teacher2`: the teacher portal; each sees only their own children.
- `parent1` (Nomsa, Leeds, two children), `parent2` (Bongani, Perth): the parent app.

Every demo record is flagged as demo and shows a DEMO tag in the staff app. Names, phone numbers and emails are invented.

## 4. Try this first (about ten minutes)

1. On the website (port 5500), press **Book a free trial lesson** and send the form.
2. In the staff app as `coordinator`, open **Leads**: your enquiry is there, with the reply clock running. Open it, press **Book free trial**, choose a teacher and yesterday's date.
3. In the teacher portal as `teacher1`, report the trial as **Taught** and choose the level.
4. Back in the staff app, open the lead and press **Make a family**.
5. In **Enrolments**, open the child, press **Edit**, choose a teacher, package, book and a weekly time. Try **Move to Active**: it tells you an invoice is needed first.
6. In **Documents**, make a quotation from the price book, **Issue** it, then **Turn into invoice** and issue that. Now move the enrolment to Active.
7. Sign in as `finance`, open **Payments desk**, record part of the money, then the rest. Open the receipt PDF.
8. Open one of the payments and **Reverse payment** with a reason: the invoice goes back to Part paid.
9. In the family's panel, press **Give app login** and sign in to the parent app with it.

This exact path was walked through the real screens by an automated browser: 22 checks, all passed.

## 5. What the research found

- Nobody offers isiNdebele for diaspora children with a structured curriculum, live teaching, recorded lessons **and** a progress record parents can see. That combination is HILYS's position.
- The best tutoring software (Teachworks, TutorCruncher) gave the ideas adopted here: parent notes after each lesson, attendance rules, teacher pay from reported lessons, and family balances worked out from real payments.
- Children's platforms (Outschool) show parents want the schedule, notes and messages on their phone.

Full report with sources: `projects/research/competitors.md`.

## 6. Decisions made for you

Each is listed with its reason in `brainstorms/2026-11-15-assumptions.md`. The ones most worth your eye:

| Decision | How to change it |
|---|---|
| **One API for everything.** The website's form talks straight to the management system; there is no second website backend to sync and lose leads. | Not recommended; ask Claude. |
| **Business time is Harare.** "Today", reply clocks and reminders use Africa/Harare; families see lesson times in their own zone. | `BUSINESS_TIME_ZONE` in `backend/config/settings.py`. |
| **The customer is the family** (the parent who pays); the children are under it. | Built in. |
| **Teachers are outside parties** with their own portal, not staff. | Built in. |
| **Teacher pay rates** are USD 6 per one-to-one lesson and USD 8 per group lesson, including lessons missed without notice. These are guesses. | Team and logins → a teacher → Teacher details. |
| **Reply clock:** one working day, Monday to Friday, 08:00–17:00 Harare. | `backend/common/business_time.py`. |
| **Book 1 pass rule:** 5–6 certificate, 3–4 certificate with practice notes, 0–2 repeat. | `backend/curriculum/rules.py`; ask Sija. |
| **Payments are recorded by hand** (Mukuru, EcoCash Diaspora, Western Union, bank, cash). Card payments are switched off until you choose a provider. | Payment provider setup is on your list below. |
| **No physical address** on any document or page. | Company settings. |

## 7. What is not built or not checked

Honest list:

- **Not built (Later):** online card payments; a partner portal for associations and heritage schools; paid access control for the video course; SMS reminders; Book 1b content; uploading receipt photos for expenses from the screen (the field exists, the upload button does not); MFA for the finance area; login tokens do not expire on their own (signing out or a password change ends them).
- **Phone app stores:** the Flutter app was checked as a web build at phone width and with `flutter analyze` and its test. It has **not** been built or run on an Android or iPhone device: those tools are not on this machine.
- **Docker Compose:** written for local Postgres and Redis but not started here (Docker was not running). Everything ran against local Postgres 16 and Redis 7 instead.
- **Email and push notifications:** the code path exists and is switched off; only in-app notifications work today.
- **Code review:** done by me as a read-through of the risky parts (permissions, money, scoping), not by separate reviewer agents. It found and fixed: a worker package missing from `requirements.txt` (the reminder worker would not have started on the server), document layout faults, a public survey page clashing with a staff route, and a missing rate limit on the public check page.
- **Security review:** Django's deployment check passes apart from HSTS preload (deliberately off). No outside security audit.
- **Screen readers:** not tested with a real screen reader.
- **Small scale:** some lists work out balances row by row. That is fine for hundreds of families; at thousands it would need tuning.

## 8. Drafts that need your approval

- **Prices:** every price in the price book is from your website, and the Self-paced (USD 39 or 9/month) and HILYS Plus (USD 19/month) prices are still the business plan's drafts. Items are marked "Draft price" until you untick it.
- **Enrolment agreement wording** (printed on the agreement PDF, marked DRAFT).
- **How long data is kept** (Company settings → Privacy).
- **Teacher pay rates** (above).
- **Targets** on the Analytics page (90% leads answered in time, 40% leads to families, 95% lessons reported within a day, 85% invoices paid on time).

The agreement and the data-keeping text need review by a lawyer in the countries you serve (at least the UK and Zimbabwe).

## 9. Your to-do list before going live

1. Confirm the business name on documents, the prices, and the teacher pay rates.
2. Ask Sija to check the Book 1 words (the recording kit lists them) and the pass rule.
3. Buy the domain (for example `hilys.com`).
4. Rent a server (Ubuntu 24.04, 2 GB memory).
5. Choose and set up off-server backup storage, and try one restore.
6. Choose a card payment provider if you want online payments (Stripe, or Paystack/Flutterwave for African cards and mobile money).
7. Have a lawyer review the agreement and privacy wording.
8. Run `docs/deploy-2026-11-first-setup.md` block by block.
9. Set `apiUrl` in `public/assets/site.js` and redeploy the website.
10. Do **not** run `seed_demo` on the server; create real logins in Team and logins.
11. Build and publish the parent app to the App Store and Google Play (needs Apple and Google developer accounts).

## 10. Numbers

| | |
|---|---|
| Backend tests passing on Postgres | 42 |
| Golden-path checks through the real screens | 22 of 22 |
| Staff app screens | 20, checked at 1440, 1024 and 375 pixels: no errors, no sideways scrolling |
| Teacher portal screens | 3 plus the report form, checked at desktop and phone width |
| Parent app tabs | 5 plus child progress; `flutter analyze` clean, 1 widget test passing |
| Document types with branded PDFs | 8 (including the certificate), each rendered and looked at, plus a three-page invoice |
| Accessibility | Colours are the contrast-checked set from the earlier website pass; chart colours checked for colour-blind separation in light and dark |
