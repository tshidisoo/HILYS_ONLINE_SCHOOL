# The quality bar

"Presentable" means the owner can open it in front of an investor, a partner or a new employee and nothing embarrasses them. Work through this file in order. When something fails, fix it and re-check; do not note it and move on.

## 1. It runs

- [ ] From a clean start, the steps in `README.md` bring up the database, Redis, API, worker, beat and every frontend with no manual fixes.
- [ ] `python manage.py check` reports no issues. Migrations are complete (`makemigrations --check` is clean).
- [ ] `seed_demo` runs twice without errors or duplicates.
- [ ] All backend tests pass on Postgres. Note the count.
- [ ] Each React app builds for production with no errors.
- [ ] `flutter analyze` reports no errors (or the handover says Flutter was not available).
- [ ] The browser console shows no errors on any main screen, and no request returns a 4xx or 5xx during normal use.

## 2. The golden path works end to end

Walk it through the real screens, logging in as each role in turn. Use the browser preview tools; do not ask the user to check.

- [ ] A visitor submits the enquiry, booking or order on the website.
- [ ] It appears in the management system as a lead with the right source, and the reply clock starts.
- [ ] Sales converts it to a customer. A duplicate attempt is blocked as designed.
- [ ] The unit of work is created and moved through every stage. A gate blocks a stage when its condition is unmet.
- [ ] Outside parties do their part in their portal and see nothing that is not theirs (checked with two accounts).
- [ ] A quotation is issued, turned into an invoice, part paid, fully paid, and the receipt PDF opens.
- [ ] A payment is reversed through the UI and the status returns correctly. A role without permission cannot record a payment.
- [ ] The customer sees their progress and documents in the app.
- [ ] The work is closed, the feedback link works, and the answer reaches leadership only.
- [ ] Home and analytics for each role reflect what just happened.
- [ ] The document verification page confirms the receipt by its code.

## 3. Every screen is finished

For each main screen in each app:

- [ ] Loading, empty and error states exist and read well.
- [ ] Forms validate inline, keep the user's input on failure and show server errors in plain words.
- [ ] Tables search, filter, sort and paginate.
- [ ] Nothing overflows or overlaps at 1440, 1024 and 375 pixels wide. No horizontal scroll on a phone.
- [ ] Text is readable: body at least 14px in the staff app and 16px on the website and app, contrast at least 4.5 to 1.
- [ ] Buttons and links have hover, focus and disabled states. Keyboard focus is visible. Form fields have labels.
- [ ] Destructive actions ask for confirmation and say what will be lost.
- [ ] Labels use the trade's own words from the research. No placeholder text, no "Lorem ipsum", no "TODO", no developer terms.
- [ ] Dates, money and phone numbers are formatted for the country.

## 4. It looks like one company

- [ ] Website, staff app, portals, mobile app and PDFs share the same colours, fonts and logo treatment.
- [ ] Status colours mean the same thing everywhere.
- [ ] Spacing is consistent: one scale, used throughout.
- [ ] The website home page has a clear visual idea of its own and does not look like a default template.
- [ ] Every PDF has been rendered to an image and looked at, including a two-page case.

Take screenshots at desktop and phone width of every main screen and save them under `docs/screenshots/<app>/`. Look at each one yourself. A screenshot you have not examined proves nothing.

## 5. The research landed

- [ ] Every item under "What we adopt" in the research report exists in the product or is listed under Later with a reason.
- [ ] The differentiators are visible on the website and in the product.

## 6. It is safe

- [ ] No secrets, `.env` files, dumps or media in git. `git status` and `git log --stat` checked.
- [ ] Every list and detail endpoint has a role test. Unauthenticated requests to private endpoints get 401.
- [ ] Private files cannot be fetched by URL without a login.
- [ ] Public endpoints are throttled and validate input.
- [ ] Sensitive fields are encrypted, and the privacy tools work.
- [ ] Run a security review pass over the backend (use a security review skill or agent if one exists) and fix what it finds.

## 7. Code review

Run a review over each part and fix real findings: the Django code (ORM correctness, N+1 queries, migration safety, permissions), the React apps (broken states, missing error handling, duplicated API logic), the Flutter app. Use reviewer agents where they exist. Then run the tests and the golden path again, because fixes break things.

## When to stop

Stop when every box above is ticked, or when a box cannot be ticked for a reason outside your control (a tool missing from the machine, a step that needs the owner). In that case the handover names the box and the reason. Do not tick a box you did not check.
