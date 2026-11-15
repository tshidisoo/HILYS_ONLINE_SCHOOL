# Lessons from building VisionExploit

Each of these was learned by getting it wrong first. Design them in; do not wait to rediscover them.

## Data and rules

1. **One rule set per record type.** VisionExploit had the same rule written in serializers, views and React forms, and they drifted apart. All rules for a record live in one backend module. Forms only mirror them for instant feedback.
2. **Never reject an incoming record.** A lead from the website, app or a partner that fails a rule is saved and listed under "Needs cleanup". Rejecting it loses a customer who will never know.
3. **Duplicates need a policy, not a crash.** Hard stop on email or ID match, a logged override for phone matches by senior roles, and no duplicate lookup at all for partner logins.
4. **Normalise phone numbers** on the way in, so the local and international forms of one number match.
5. **Any sync between two systems needs a retry queue and a resync job.** The website's push to the management system failed silently and leads were lost. This is why the default here is one API. If a second system is ever added, add the queue with it.
6. **Soft delete, with a bin.** People delete the wrong record.
7. **Any internal staff member can own a customer.** Restricting ownership to sales roles broke real workflows.

## Roles and access

8. **Decide internal versus outside before the first view.** An `is_internal_staff` check added late had to be retrofitted across the codebase. Outside parties see only their own records, everywhere, including search, counts and error messages.
9. **Permission helpers on the user, not role strings in views.** When a role was renamed or a second person shared a role, string checks broke.
10. **Several people can hold one role, and people cover for each other.** Do not assume one user per role.
11. **Only finance and the owner record payments,** even though several roles issue documents.

## Money

12. **Payment status is derived from recorded money.** When staff set it by hand it was wrong within weeks.
13. **Receipts are allocated to invoices.** Without allocations nobody could say which invoice a payment settled, and old receipts had to be matched by hand later.
14. **Issued documents are locked, numbered without gaps, and amended only by named roles with a stored reason.**
15. **Never add across currencies.** Show a total per currency.
16. **Finance is billing, cash flow and money owed.** An attempt to rebuild statutory bookkeeping and tax filing inside the system was wasted effort. Feed an accounting system instead.
17. **Verify money features through the real screens,** posting and reversing, not only with tests. Tests passed while the UI could not reverse a payment.
18. **Watch for cached clients.** A cached external client (for example a spreadsheet connection) kept stale credentials and failed quietly. Build clients per call or refresh them.

## Time

19. **The server runs in UTC; the business does not.** "Today", "overdue", reply clocks, cut-offs and scheduled jobs use the business's time zone. Test around midnight and across weekends.
20. **A beat schedule change needs a beat restart,** separately from the worker.

## Privacy and security

21. **Privacy compliance from the first model.** VisionExploit was reviewed and found non-compliant after it was built, and fixing it meant culling features. Decide what personal data is held, why, for how long and who sees it, before modelling. Sensitive fields are encrypted and private files are served through an authenticated view, never from a public folder.
22. **Backups before the first real customer:** an encrypted nightly database and media backup off the server, and a restore that has actually been tried.
23. **Secrets live only in environment files on the server.** No default that works in production. A missing key raises an error.
24. **CORS is an allow-list.** Allow-all only in debug with no list set.
25. **Throttle every public endpoint.** The first public form had none.
26. **MFA for the finance area** is worth having before real money is recorded.

## Building and shipping

27. **Every server dependency is in `requirements.txt`.** gunicorn was installed by hand and missing from the file.
28. **Tests run on Postgres.** SQLite gives false passes and false failures.
29. **Migrations run with the project's virtualenv,** never the system Python.
30. **Runbooks have no placeholders.** The owner pastes each block top to bottom; every block must run as written. Rollback sits in its own clearly marked section, and says what data is lost.
31. **Each runbook states what to expect after every block,** and tells the owner to stop and send the output if they see anything else.
32. **Never `git add -A`.** Stage named paths. The root collects archives, media and notes that must not be committed.
33. **Keep the root clean.** One-off fix scripts and guides in the root were followed months later and described a process that no longer existed. Runbooks go in `docs/`, plans in `projects/`, decisions in `brainstorms/`.
34. **`CLAUDE.md` holds stable rules and pointers, never status.** Status in it went stale and misled later sessions.
35. **A side-folder build breaks the generated service worker.** Regenerate it.

## Product

36. **Research competitors before designing a feature.** The features that worked best came from seeing what others did and where they fell short.
37. **Every role gets a Home page that says what to do today.** Staff ignored dashboards full of charts and used the page that listed their overdue items.
38. **Plain words on screen.** Staff are not technical. No internal names, codes or developer terms in labels and messages.
39. **Empty states explain the next step.** A blank table reads as broken.
40. **Anything public-facing needs the owner's yes:** prices, promises, guarantees, legal wording. Build it as a draft.
41. **Structured data and SEO claims must be checked in the built page,** not assumed from the source.
42. **Demo and test records are clearly marked** (a `ZZ TEST` prefix or a demo flag) so they can be removed before going live.
