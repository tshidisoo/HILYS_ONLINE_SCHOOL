---
name: ecosystem-builder
description: Build a complete business software ecosystem for any industry from a short description of the business - public website, staff management system (CRM, casework, billing documents, finance, analytics), partner and field-worker portals, and a customer mobile app - on the proven VisionExploit stack (Django + DRF + Postgres + Redis + Celery, React, Flutter). Researches competitors first, then builds everything in one long run until it is presentable, with polished UI, working functions and demo data. Use this whenever the user describes a business or business idea and wants "the whole system", "an ecosystem", "a management system and website and app", "the same as VisionExploit but for X", "mirror our project for another industry", or asks to set up the software for their own or someone else's business, even if they do not name this skill.
---

# Ecosystem Builder

Turn a description of a business into a working software ecosystem, built the way VisionExploit was built, adapted to that business's industry.

The person using this skill is usually a founder, not a developer. They give a description and expect to come back to something they can open, click through and show to other people. Invoking this skill is their instruction to run long, to research on the web, to use subagents for parallel research and reviews where you have them, and to make sensible decisions without asking. Tokens and time are not the constraint. A half-built system that needed ten questions is the failure; a finished one with a clear list of the assumptions you made is the goal.

## What you produce

One monorepo in the current folder containing:

1. **Management system** for staff: API plus a React staff app.
2. **Public website** that wins customers and feeds leads and orders into the management system.
3. **Portals** for outside parties (partners, suppliers, field workers), only the ones this business needs.
4. **Customer mobile app** in Flutter.
5. **Billing documents**: branded quotation, invoice, receipt, credit note, payment plan and statement PDFs, plus a service agreement if the industry uses one.
6. **Demo data and demo logins** so every screen shows something real-looking.
7. **Project scaffolding**: `CLAUDE.md`, `README.md`, a first-server-setup runbook, the research report, the decision record and a handover document with screenshots.

Everything runs locally when you finish. You never deploy, buy, register accounts or publish; those go on the owner's to-do list in the handover.

## Reference files

Read each one at the phase that needs it. They hold the detail; this file holds the order of work.

| File | Read it when |
|---|---|
| `references/research.md` | Phase 1, before any design |
| `references/industry-mapping.md` | Phase 2, to turn the business into modules, roles and stages |
| `references/stack-and-layout.md` | Phase 3, before creating any file |
| `references/management-system.md` | Phase 4, the module catalogue and how each is built |
| `references/billing-documents.md` | Phase 4, before touching money |
| `references/website-portals-app.md` | Phases 5 to 7 |
| `references/lessons.md` | Phase 2 and again before Phase 8. Every item is a mistake that already cost real rework |
| `references/quality-bar.md` | Phase 8, and whenever you are about to call something done |
| `references/operations.md` | Phase 9, for CLAUDE.md, runbook, git and handover |

If the folder `C:\Users\tshid\VEC-Ecosystem-Deployment` exists on this machine, it is the original VisionExploit project. Read it for patterns when a reference file is not specific enough (its `CLAUDE.md` and `README.md` give the map). Treat it as read-only. Never open its `.env` files, `secrets/`, `pre_migration_backups/`, `media/` or `.claude/`, and never carry VisionExploit's name, logo, wording, prices or client data into another business. If the folder does not exist, the reference files are enough.

## How to run

### Phase 0: Take the brief

Read what the user gave you. You need: what the business sells, who pays, who delivers the service, and where it operates. If the description covers those, do not ask anything.

If something essential is missing, ask once, in a single round of at most four questions, each with your recommended answer first. Good candidates: business name, city and country (this sets currency, language, privacy law and competitors), who delivers the service (employees, freelancers, partner companies), and brand colours or a logo file if they have one. After that one round, never stop to ask again. Decide, write the decision down, and keep going.

Start in an empty folder. If the current folder already has a project in it, say so and ask whether to build in a new subfolder; that is the one other question worth stopping for, because overwriting someone's work cannot be undone.

Create `projects/ecosystem-foundation/progress.md` now: a checklist of every phase and, later, every module. Update it as you go. On a run this long your earlier context will be summarised, and this file is how you find your place again. Keep your task list in step with it.

### Phase 1: Research the industry and competitors

Follow `references/research.md`. Study direct local competitors, the best regional players, and the best software built for this industry anywhere in the world. Write `projects/research/competitors.md` with a feature matrix and a short list headed "What we adopt, and why".

This is what separates a generic CRM from a system that fits the trade. The founder of VisionExploit did this by hand for every feature; do it properly here. Adopt ideas and patterns, never anyone's text, images, logo or page design.

### Phase 2: Design the ecosystem

Follow `references/industry-mapping.md` and `references/lessons.md`. Write `projects/ecosystem-foundation/plan.md`:

- The business in five lines, and the golden path: the single journey from a stranger finding the website to a paid, delivered, receipted service with feedback collected.
- The folder map and the Django app list, grouped by area.
- The roles and what each can see and do.
- The record stages for the industry's core work.
- The module list in three tiers: Core (always built), Industry (this trade's own modules), Later (named, not built).
- The price book: realistic draft services and prices from your research, marked as draft.
- Every assumption you made, in `brainstorms/YYYY-MM-DD-assumptions.md`, one line each with the reason.

Do not wait for approval. The plan is a record for the owner, not a gate.

### Phase 3: Scaffold

Follow `references/stack-and-layout.md` exactly: folders, versions, ports, docker-compose, `.gitignore`, `.claude/launch.json`, design tokens. Run `git init`, set up the ignore rules before the first commit, and commit locally at the end of every phase with named paths. Never push.

Pick the brand before writing UI: name, two or three colours, fonts, a simple wordmark if no logo was supplied. Put them in one tokens file per frontend and one for PDFs, so a rebrand is one edit.

### Phase 4: Management system

Follow `references/management-system.md` and `references/billing-documents.md`. Build the API and the staff app together, one module at a time, in this order: users and roles, leads, customers, the industry's core module, pipeline, billing documents, payments, simple finance, Home dashboard, then the remaining Core modules. Write tests as you go and run them on Postgres.

After each module: seed demo data for it, open it in the browser, use it, fix what is wrong, tick it in `progress.md`.

### Phase 5: Website

Follow `references/website-portals-app.md`. If a design skill is installed (for example `hallmark` or `scroll-craft`), use it for the home page; a generic template look is a failure here. The enquiry, booking or order form must land in the management system, and you must see the record arrive.

### Phase 6: Portals

Build only the portals the plan calls for. Each outside party sees only their own records; test that with two demo accounts of the same role.

### Phase 7: Mobile app

Build the Flutter app against the same API. Verify with `flutter analyze` and a web build opened in the browser at phone width.

### Phase 8: Prove it works

Follow `references/quality-bar.md` from top to bottom. Walk the golden path through the real screens as each role. Post a payment and reverse it through the UI. Render every PDF and look at it. Screenshot every main screen at desktop and phone width into `docs/screenshots/`. Fix everything you find, then walk the path again. Run a code review pass on each part (use the reviewer agents if they exist) and fix what they find.

You are done with this phase when the quality bar's checklist is fully ticked, not when you are tired of it.

### Phase 9: Hand over

Follow `references/operations.md`. Write `CLAUDE.md`, `README.md`, `docs/deploy-YYYY-MM-first-setup.md`, and `docs/handover.md`. Then give the user a short final message: what exists, how to start it, where the demo logins are, the screenshots, the assumptions that most need their eye, and their own to-do list.

## Rules that hold through every phase

- **Keep going.** Errors, failed installs, a port in use, a flaky tool: diagnose and work through them. Stop only for something that cannot be undone or that reaches outside this machine.
- **Never outward-facing without the owner.** No deploying, no SSH to any server, no creating accounts (Firebase, payment providers, domains, app stores), no pushing to a remote, no sending email or messages to real people. Build the code path, leave it switched off without credentials, and list the step in the handover.
- **Draft, never promise.** Prices, guarantees, refund terms, privacy notices and legal wording are drafts until the owner approves them. Mark them as drafts in the admin and in the handover. Legal documents also say they need review by a local lawyer.
- **No real people's data.** Demo data is invented and looks plausible for the country. Competitor names appear only in the research report, never in the product.
- **One source for each rule.** A business rule lives in one backend module that every entry point calls. Forms mirror it for instant feedback only.
- **Money is exact.** Decimal amounts, a currency on every amount, never add across currencies, payment status derived from recorded money.
- **Report honestly.** If something is not built, not verified, or faked for the demo, the handover says so in plain words.
- **Plain language in the product.** Labels, buttons and messages are written for staff who are not technical. No jargon, no developer terms on screen.

## What "the same as VisionExploit" means

Same stack, same folder shape, same module patterns, same billing document suite, same working rules. It does not mean the same modules: a visa tracker is meaningless to a bakery. For each VisionExploit module, `references/industry-mapping.md` gives the general idea behind it and how to find this industry's equivalent. Where an industry needs something VisionExploit never had (stock, bookings, shifts, deliveries), build it to the same standard using the same patterns.

One deliberate difference: VisionExploit has a separate website backend that syncs to the management system, and that sync lost leads until a retry queue was added. Here the website talks to the one management system API through public endpoints, unless the user asks for two backends. Say so in the handover.
