# HILYS Languages website

A plain HTML site for HILYS Languages & Culture Centre: online isiNdebele lessons for children of Ndebele families abroad. There's no framework and no build step.

## What's here

| Path | What it is |
|---|---|
| `public/index.html` | Home page: levels, culture, how it works, prices, FAQ, free trial |
| `public/courses.html` | Course list and the three ways to learn (Self-paced, HILYS Plus, Live) with prices |
| `public/book-1.html` | Book 1 video course page: what's taught, lesson shape, the 35 lessons |
| `public/lesson.html` | One lesson page (`lesson.html?n=5`): video, culture piece, "Mark as done" |
| `public/assets/book1.js` | The Book 1 lesson list. Add video links and choose free lessons here |
| `public/assets/site.js` | WhatsApp and booking settings, shared by every page |
| `public/policies.html` | Parent policies: safety, missed lessons, power cuts, payments, stopping |
| `public/404.html` | Page shown for broken links |
| `public/assets/site.css` | Shared styles for every page |
| `public/assets/logo.jpg` | Logo |
| `firebase.json` | Firebase Hosting settings (serves the `public` folder) |
| `docs/whatsapp-messages.md` | Message drafts for the first families (not part of the website) |
| `docs/curriculum/` | Free-trial lesson with level check, and Beginner lessons 1–4 |
| `materials/flashcards.html` | On-screen flashcards to share on Zoom (open in Chrome, pick a lesson) |
| `records/hilys-tracker.xlsx` | Families, lessons, payments, monthly income and prices |
| `scripts/make_tracker.py` | Rebuilds a blank tracker. Don't run it over your real tracker. |

## Teaching materials

- **Flashcards:** double-click `materials/flashcards.html`. Click a card or press space to show the English, use the arrow keys to move between cards, and press S to shuffle. To change words, edit the `SETS` list near the bottom of the file.
- **Tracker:** open it in Excel or upload it to Google Sheets. Use the dropdowns, delete the grey example rows, and the **Monthly summary** sheet fills in by itself. Enter dates as `2026-11-03`.

## Edit the site

Open any `.html` file in Notepad or VS Code, change the text and save.

**WhatsApp and booking buttons:** in `public/assets/site.js`, fill in:

```js
var CONFIG = {
  whatsappNumber: "263771234567",               // digits only, with country code
  bookingUrl: "https://cal.com/your-name/trial" // your Cal.com or Calendly link
};
```

While these are empty, the buttons are greyed out and the page says "Online booking opens soon".

## Video course (Book 1)

- **Add a video:** in `public/assets/book1.js`, paste the video's embed address into that lesson's `video: ""`. Until then the lesson page says the video is being recorded.
- **Free lessons:** lessons with `free: true` can be watched by anyone (lessons 1 and 2 to start). The others show a "join the waiting list" message.
- **Prices:** the Self-paced and HILYS Plus prices are in `public/courses.html`. They are proposals; change the text there.
- **Not built yet:** sign-in and online payment. The site only hides the player on paid lessons, so don't paste a paid lesson's video link until sign-in exists. "Mark as done" is remembered in the visitor's own browser only.

## Preview on your computer

```bash
python -m http.server 5500 --directory public
```

Then open http://localhost:5500.

## Put it online (Firebase Hosting, free)

You only need to set this up once:

```bash
npm install -g firebase-tools
```

```bash
firebase login
```

```bash
firebase projects:create hilys-languages
```

```bash
firebase use hilys-languages
```

After that, run this command each time you want to publish changes:

```bash
firebase deploy --only hosting
```

The site goes live at `https://hilys-languages.web.app`. You can connect your own domain later in the Firebase console under Hosting, then Add custom domain.

After you have a domain, change `og:image` in `public/index.html` to the full address (for example `https://hilys.com/assets/logo.jpg`) so WhatsApp link previews show the logo.
