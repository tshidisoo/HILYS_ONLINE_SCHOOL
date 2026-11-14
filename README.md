# HILYS Languages website

A plain HTML site for HILYS Languages & Culture Centre: online isiNdebele lessons for children of Ndebele families abroad. There's no framework and no build step.

## What's here

| Path | What it is |
|---|---|
| `public/index.html` | Home page: levels, culture, how it works, prices, FAQ, free trial |
| `public/courses.html` | Course list and the three ways to learn (Self-paced, HILYS Plus, Live) with prices |
| `public/book-1.html` | Book 1 video course page: what's taught, lesson shape, the 35 lessons |
| `public/lesson.html` | One lesson page (`lesson.html?n=5`): video, culture piece, "Mark as done" |
| `public/teach.html` | "Teach with HILYS" page for new teachers. Unlisted for now: no page links to it and search engines are told to skip it. Share the address directly |
| `public/level-check.html` | Four questions for parents that suggest Beginner, Intermediate or Conversation. Nothing is saved |
| `public/worksheet.html` | Printable one-page worksheet for a lesson (`worksheet.html?n=5`): trace, read, finish the word, draw |
| `public/certificate.html` | Printable Book 1 certificate: type the child's name, then print or save as PDF |
| `public/assets/book1-content.js` | Flashcards, culture piece and home task for each lesson. Made by a script, don't edit by hand |
| `scripts/make_book1_content.py` | Rebuilds `book1-content.js` from `materials/book1/lessons.py` |
| `public/assets/book1.js` | The Book 1 lesson list. Add video links and choose free lessons here |
| `public/assets/site.js` | WhatsApp and booking settings, shared by every page |
| `public/policies.html` | Parent policies: safety, missed lessons, power cuts, payments, stopping |
| `public/404.html` | Page shown for broken links |
| `public/assets/site.css` | Shared styles for every page |
| `public/assets/logo.jpg` | Logo |
| `firebase.json` | Firebase Hosting settings (serves the `public` folder) |
| `docs/whatsapp-messages.md` | Message drafts for the first families (not part of the website) |
| `docs/pilot-feedback.md` | Video pilot: the message, the 10 questions for the five families, and how to read the answers |
| `docs/curriculum/` | Free-trial lesson with level check, and Beginner lessons 1–4 |
| `materials/recording-kit.html` | Teleprompter for recording the Book 1 videos: each slide's script, notes and timing |
| `scripts/make_recording_kit.py` | Rebuilds the recording kit's scripts (`materials/book1/recording-data.js`) from `lessons.py` |
| `materials/flashcards.html` | On-screen flashcards to share on Zoom (open in Chrome, pick a lesson) |
| `records/hilys-tracker.xlsx` | Families, lessons, payments, monthly income and prices, plus the video course: waiting list and subscribers, pilot feedback, course summary |
| `scripts/make_tracker.py` | Rebuilds a blank tracker. Don't run it over your real tracker. With `--add-to` it adds only the video-course sheets to a tracker you already use |

## Teaching materials

- **Flashcards:** double-click `materials/flashcards.html`. Click a card or press space to show the English, use the arrow keys to move between cards, and press S to shuffle. To change words, edit the `SETS` list near the bottom of the file.
- **Recording kit:** double-click `materials/recording-kit.html` and pick a lesson. Put the lesson's slides on the screen you are recording, and the kit on a second screen or a phone. It shows what to read aloud for each slide, the notes that are not read aloud, a clock with the time planned for the slide, and a tick for slides already recorded. Each lesson also lists the words still waiting for Sija's check. After changing `lessons.py`, run `python scripts/make_recording_kit.py`. Changes made only in Google Slides are not picked up.
- **Video course sheets in the tracker:** list waiting-list families and subscribers on **Video course**, and each pilot family's answers on **Pilot feedback**. **Course summary** counts them, including progress towards 20 HILYS Plus subscribers. If you already keep a tracker with real rows, run `python scripts/make_tracker.py --add-to your-tracker.xlsx` to add these three sheets without touching the others (keep a copy first).
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

**Parent reviews and the referral offer:** in the same file, add real reviews to the `reviews` list and write your offer in `referralOffer`. The "What parents say" section on the home page stays hidden while both are empty. Only add words a parent really said, and ask them first.

## Video course (Book 1)

- **Add a video:** in `public/assets/book1.js`, paste the video's embed address into that lesson's `video: ""`. Until then the lesson page says the video is being recorded.
- **Free lessons:** lessons with `free: true` can be watched by anyone (lessons 1 and 2 to start). The others show a "join the waiting list" message.
- **Flashcards, culture piece and home task:** free lessons show these under the video. They come from `materials/book1/lessons.py`. Only checked words are shown: anything still marked with a `*` (waiting for Sija's check) or missing an English meaning is left out, so some lessons have few or no flashcards yet. After Sija checks a word, remove its `*` in `lessons.py` and run `python scripts/make_book1_content.py`.
- **Worksheets:** free lessons link to a printable worksheet (one A4 page) with letters to trace, lines to read, words to finish and a picture to draw. They are built by the same script as the flashcards, from the same checked content.
- **Certificate:** when all 35 lessons are ticked as done, the course page links to `certificate.html`. Until sign-in exists anyone can open and print it.
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
