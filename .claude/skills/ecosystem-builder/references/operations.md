# Operations: project files, git, first deploy and handover

## `CLAUDE.md` (repo root)

Stable rules and pointers only, never status. Sections, in this order:

1. **One line on what the repo is.**
2. **Where truth lives**: git for what is built, `projects/ecosystem-foundation/plan.md` for decisions, `docs/handover.md` as a dated snapshot.
3. **Map**: a table of folders, what each is, and its future production address.
4. **Where new things go**: runbooks in `docs/deploy-YYYY-MM-<topic>.md` with rollback in its own section, plans in `projects/<name>/`, decision records in `brainstorms/YYYY-MM-DD-<topic>.md`, seed scripts and demo logins in `.claude/dev/`. Nothing new in the root.
5. **Local dev**: the exact commands and ports, and that backend tests need Postgres.
6. **Deploying**: the pattern below, and that the assistant never connects to the production server; it writes commands and the owner runs them.
7. **Committing**: stage named paths, never `git add -A`, commit or push only when asked, never commit secrets, dumps, media or `node_modules`.
8. **Working with the owner**: money features are verified by posting and reversing through the real screens; anything public-facing needs the owner's explicit yes.
9. **Rule modules**: which file holds the rules for each record type, and that no second copy may be added elsewhere.

## `README.md`

For a person. What is in the repo, how to run each part locally, the app list by area, how deploys work, where secrets live. Nothing that changes weekly.

## Git

- `git init` in Phase 3, with `.gitignore` written before the first commit.
- Commit locally at the end of each phase and after each module, with named paths and a clear message (`feat(billing): quotation, invoice, receipt with allocations`).
- Never push, never add a remote, never create a repository on a hosting service. Those are the owner's steps.
- Before the final commit, read `git status` and confirm nothing sensitive is staged.

## Production pattern (described, not performed)

- One Linux VPS. No Docker in production.
- The repo is cloned on the server. The server follows a deploy branch (for example `live`), not `main`. Moving the deploy branch is the act of deploying, and happens only on the owner's explicit yes.
- systemd services: `<biz>-backend` (gunicorn), `<biz>-celery-worker`, `<biz>-celery-beat`. They restart separately.
- The backend has its own virtualenv on the server. Migrations run with it.
- Frontends build on the server inside the repo (`CI=true npm run build`); nginx serves each `build/` folder on its own subdomain and proxies `/api/` to gunicorn.
- Subdomains: the main domain for the website, `api.`, `admin.` for the staff app, `partners.` and one named for the worker role.
- HTTPS through Let's Encrypt.
- Environment files on the server only.
- Nightly encrypted backups of the database and media to off-server storage, and a restore drill.

## `docs/deploy-YYYY-MM-first-setup.md`

The first-server-setup runbook. The owner will paste it block by block, so:

- It starts with a short list of what the owner must have before beginning: a VPS and its address, a domain with DNS pointed at the server, and the values for the environment file. These are the only things they supply, and the runbook says exactly where each one is typed.
- Every command block runs as written. Where a value is the owner's (the domain, the server address), the first block has them set it once as a shell variable, and every later block uses the variable.
- After each block: "You should see…", and "If you see anything else, stop and send the output."
- Order: system packages, database and user, Redis, clone, virtualenv and requirements, environment file, migrate, create the owner's login, collect static, systemd units (full file contents included), nginx site files (full contents included), HTTPS, frontend builds, start and enable services, checks that change nothing.
- **Rollback is its own section at the end**, clearly marked as only for undoing, saying what is lost.
- It does not seed demo data in production.

Later changes each get their own runbook in the same style: what ships in plain words, check what the pull will bring, pull, migrate, build, restart, check it is live, rollback apart.

## `docs/handover.md`

Written for the owner, in plain language, dated at the top.

1. **What you have**: each part in one or two lines, with a screenshot.
2. **How to start it on this computer**: the exact steps, and the address of each part.
3. **Demo logins**: where the file is (`.claude/dev/demo-logins.md`) and which login shows what.
4. **Try this first**: the golden path as a ten-minute walkthrough the owner can follow.
5. **What the research found**: five lines, and a link to the full report.
6. **Decisions made for you**: the assumptions that matter most, each with how to change it. Include the single-API decision.
7. **What is not built or not checked**: honest and specific. Modules in the Later tier, anything faked for the demo, any quality-bar box left unticked and why.
8. **Drafts that need your approval**: prices, website promises, terms, privacy notice (and that legal text needs a local lawyer).
9. **Your to-do list before going live**, in order: confirm name and prices, supply logo and photos, buy the domain, rent the server, create the Firebase project, choose a payment provider, legal review, set up backups, run the first-setup runbook, remove demo data, publish the app.
10. **Numbers**: tests passing, screens built, documents generated.

## The final message to the user

Short. What exists, how to open it, where the handover is, the three or four decisions most worth their attention, and the first thing on their to-do list. Do not paste the handover into chat. Do not claim anything the quality bar did not confirm.
