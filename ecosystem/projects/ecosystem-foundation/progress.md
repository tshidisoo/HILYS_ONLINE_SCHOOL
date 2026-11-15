# HILYS ecosystem: progress

Built with the ecosystem-builder skill (copy in `.claude/skills/ecosystem-builder/`), started 2026-11-15.
The owner chose: build in `ecosystem/` inside the HILYS repo; push to the `ecosystem` branch (the session container is temporary); use own defaults where reference files are missing; full scope fitted to a school.

## Phases

- [x] 0. Brief taken (one round of questions answered)
- [x] 1. Research: `projects/research/competitors.md`
- [x] 2. Design: `projects/ecosystem-foundation/plan.md`, assumptions
- [x] 3. Scaffold: folders, docker-compose, tokens, git
- [x] 4. Management system (modules below)
- [x] 5. Website: existing site's forms feed the API
- [x] 6. Teacher portal
- [x] 7. Parent mobile app (Flutter)
- [x] 8. Prove it works (quality bar)
- [x] 9. Hand over

## Phase 4 modules

- [x] users and roles, audit
- [x] leads (reply clock)
- [x] families and students (rules, duplicates, needs cleanup)
- [x] enrolments (stages, gates)
- [x] lessons (timetable, attendance, notes, make-ups)
- [x] curriculum (Book 1, progress, end-of-book check, certificates)
- [x] catalogue (price book)
- [x] pipeline
- [x] billing documents and PDFs
- [x] payments desk (allocations, reversals)
- [x] finance
- [x] teacher pay
- [x] Home and analytics
- [x] tasks, feedback, notifications
- [x] video course subscriptions
- [x] privacy tools
- [x] website and parent endpoints
- [x] settings
- [x] seed_demo

## Quality bar (see .claude/skills/ecosystem-builder/references/quality-bar.md)

- [x] Runs from the README steps (with local Postgres and Redis; Docker Compose not started here)
- [x] `check` clean, `makemigrations --check` clean, `seed_demo` safe twice
- [x] 42 backend tests on Postgres
- [x] Both React apps build; `flutter analyze` clean
- [x] No console errors or failed requests on any main screen
- [x] Golden path walked through the real screens: 22 of 22 checks
- [x] Two accounts per outside role see only their own records
- [x] Every screen at 1440, 1024 and 375 pixels; screenshots in docs/screenshots
- [x] Every PDF rendered and looked at, including a multi-page invoice
- [x] Research "what we adopt" items are all in the product
- [ ] Separate reviewer agents: not used; my own review instead (see handover)
- [ ] Phone builds on real devices: not possible on this machine
