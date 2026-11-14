"""Builds public/assets/book1-content.js from materials/book1/lessons.py.

The website's lesson pages use it for flashcards, the culture piece, the home task and
the printable worksheet (worksheet.html).
Run it again after changing lessons.py:

    python scripts/make_book1_content.py

Only checked content goes on the website: anything marked with a * in lessons.py
(added by HILYS, waiting for Sija's check) and words with no English meaning are left out.
Once Sija has checked a word, remove its * in lessons.py and run this again.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "materials" / "book1"))
from lessons import LESSONS  # noqa: E402

MIN_CARDS = 3  # fewer checked words than this: the lesson page shows no flashcards


def checked(text):
    return bool(text) and "*" not in text


def worksheet(lesson):
    """What the printable worksheet shows: letters to trace, lines to read, words to finish, a word to draw."""
    sheet = {}
    letters = [x for x in (lesson.get("letter"), lesson.get("letter2")) if x]
    writing = lesson.get("writing")
    if letters:  # a new sound: small and capital, e.g. m M
        sheet["trace"] = [form for x in letters for form in (x, x.upper())]
        sheet["repeat"] = True
    elif isinstance(writing, dict) and writing["kind"] == "letters":
        sheet["trace"] = writing["text"].split()
    elif isinstance(writing, dict) and checked(writing["text"]):
        sheet["pattern"] = writing["text"]
    elif lesson.get("letters"):  # review and reading lessons
        sheet["trace"] = lesson["letters"][:8]
    read = [row for row in lesson.get("read", []) if checked(row)][:3]
    if read:
        sheet["read"] = read
    finish = [[q, a] for q, a in lesson.get("qedisa", []) if checked(q) and checked(a)][:5]
    if finish:
        sheet["finish"] = finish
    for key in (lesson.get("key"), lesson.get("key2")):
        if key and checked(key[0]) and checked(key[2]) and "draw" not in sheet:
            sheet["draw"] = [key[0], key[2]]
    return sheet


content = {}
for lesson in LESSONS:
    cards, seen = [], set()
    words = [(nd, pic, en) for nd, pic, en in lesson.get("words", [])]
    words += [(nd, pic, en) for pic, nd, en in lesson.get("talk", {}).get("items", [])]
    for nd, pic, en in words:
        if checked(nd) and checked(en) and nd not in seen:
            seen.add(nd)
            cards.append([pic, nd, en])

    entry = {}
    if len(cards) >= MIN_CARDS:
        entry["cards"] = cards
    nd, en, text = lesson["culture"]
    if checked(text) and checked(nd):
        entry["culture"] = {"nd": nd, "en": en, "text": text}
    if checked(lesson.get("home")):
        entry["home"] = lesson["home"]
    if checked(lesson.get("tip")):
        entry["tip"] = lesson["tip"]
    sheet = worksheet(lesson)
    if sheet:
        entry["sheet"] = sheet
    content[lesson["n"]] = entry

out = ROOT / "public" / "assets" / "book1-content.js"
lines = ["  %d: %s" % (n, json.dumps(e, ensure_ascii=False)) for n, e in content.items()]
out.write_text(
    "// Made by scripts/make_book1_content.py from materials/book1/lessons.py. Don't edit by hand:\n"
    "// change lessons.py and run the script again. Each card is [picture, isiNdebele, English].\n"
    "var BOOK1_CONTENT = {\n" + ",\n".join(lines) + "\n};\n",
    encoding="utf-8",
)
with_cards = sum(1 for e in content.values() if "cards" in e)
with_sheet = sum(1 for e in content.values() if "sheet" in e)
print("Wrote %s: %d lessons, %d with flashcards, %d with a worksheet"
      % (out.relative_to(ROOT), len(content), with_cards, with_sheet))
