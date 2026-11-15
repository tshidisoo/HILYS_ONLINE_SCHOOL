# Assumptions made during the build (2026-11-15)

One line each, with the reason. Change any of these and tell Claude; most are one setting.

- Build lives in `ecosystem/` inside the HILYS repo, on the `ecosystem` branch, pushed to GitHub. (Owner's choice; the cloud session is temporary.)
- Five skill reference files were missing; stack versions, ports, folder layout and PDF design are my own defaults. (Owner's choice.)
- Business time zone is Africa/Harare: teachers teach from Zimbabwe, so reply clocks, "today" and reminders use Harare time. Families see times in their own zone.
- Currency is USD everywhere today, but every amount carries a currency so a second one can be added. (Website prices are in USD.)
- The customer is the **family** (the paying parent); the children are **students** under it. (One parent often pays for siblings.)
- Teachers are outside parties with their own portal, not staff. (They are freelancers in the plan; they must see only their own students.)
- No partner portal yet: diaspora associations are Stage 3 of the business plan.
- Payment methods are Mukuru, EcoCash Diaspora, Western Union, bank transfer and cash, recorded by hand. Card payments are a switched-off code path.
- Monthly packages are billed at the start of the month, matching the parent policies.
- Teacher pay default: USD 6.00 per taught one-to-one lesson and USD 8.00 per taught group lesson, including "Missed (counts as used)". Draft: the owner sets real rates.
- Reply clock: one working day, Monday to Friday, Harare time.
- Book 1 end-of-book check pass rule: 5–6 certificate, 3–4 certificate with practice notes, 0–2 repeat (from `docs/curriculum/book1-assessment.md`).
- Demo data uses invented Ndebele and diaspora names, UK/SA/AU/US phone numbers in reserved test ranges where they exist, and every demo record is flagged as demo.
- The existing static website stays; its trial and waiting-list buttons gain a form that posts to the API. (Rebuilding a working site was not asked for.)
- Prices for video course and HILYS Plus are the business plan's drafts.
- Legal texts (enrolment agreement, privacy notice) are drafts that need a lawyer in the jurisdictions HILYS serves.
