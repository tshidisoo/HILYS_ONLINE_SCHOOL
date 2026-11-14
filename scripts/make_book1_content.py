"""Builds public/assets/book1-content.js from materials/book1/lessons.py.

The website's lesson pages use it for flashcards, the culture piece and the home task.
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
print("Wrote %s: %d lessons, %d with flashcards" % (out.relative_to(ROOT), len(content), with_cards))
