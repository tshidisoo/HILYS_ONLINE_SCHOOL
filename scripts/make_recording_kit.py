"""Builds materials/book1/recording-data.js for the recording kit (materials/recording-kit.html).

It builds each Book 1 lesson the same way build.py builds the slide decks, and saves every
slide's narration script, teacher notes and timing. Run it again after changing lessons.py:

    python scripts/make_recording_kit.py

Changes made only in Google Slides are not picked up: this reads lessons.py, not the slides.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "materials" / "book1"
sys.path.insert(0, str(BOOK))
import build as B  # noqa: E402
from lessons import LESSONS  # noqa: E402

NOTE_STARTS = ("TEACHER:", "FOR VIDEO:")
LABELS = {"title": "Title card", "goodbye": "Goodbye"}


def split_notes(notes):
    """Lines to say aloud, then the notes that are not read out (TEACHER: / FOR VIDEO:)."""
    script, extra = [], []
    for line in notes.strip().splitlines():
        line = line.strip()
        if line == "SCRIPT:" or not line:
            continue
        if line.startswith(NOTE_STARTS) or (extra and not line.startswith("SCRIPT:")):
            extra.append(line)
        else:
            script.append(line.removeprefix("SCRIPT:").strip())
    return script, extra


def label(slide, kind):
    if kind in LABELS:
        return LABELS[kind]
    for shape in slide.shapes:  # the coloured tag, e.g. "UMDLALO · GAME"
        text = shape.text_frame.text.strip() if shape.has_text_frame else ""
        if " · " in text and text.isupper() and not text.startswith("HILYS"):
            return text.split(" · ")[-1].capitalize()
    return kind.capitalize()


def words_to_check():
    """Per lesson, the items still waiting for Sija (from WORDS-TO-CHECK.md)."""
    found, n = {}, None
    for line in (BOOK / "WORDS-TO-CHECK.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"## Lesson (\d+):", line)
        if m:
            n = int(m.group(1)); found[n] = []
        elif n and line.startswith("- "):
            found[n].append(line[2:].replace("**", ""))
    return found


keys = {}
for L in LESSONS:
    if L["kind"] == "phonics":
        keys[L["letter"]] = L["key"]
        if L.get("letter2"):
            keys[L["letter2"]] = L["key2"]

check = words_to_check()
lessons = []
for i, L in enumerate(LESSONS):
    deck = B.build(L, LESSONS[i - 1] if i else None, LESSONS[i + 1] if i + 1 < len(LESSONS) else None, keys)
    scale = 40 / sum(B.MINUTES[kind] for _, kind, _ in deck.slides)  # same timing as Deck.save
    t, slides = 0.0, []
    for slide, kind, notes in deck.slides:
        seconds = B.MINUTES[kind] * scale * 60
        script, extra = split_notes(notes)
        slides.append({"label": label(slide, kind), "start": round(t), "seconds": round(seconds),
                       "script": script, "notes": extra})
        t += seconds
    slides[-1]["seconds"] += 40 * 60 - sum(s["seconds"] for s in slides)  # rounding: keep the total at 40:00
    lessons.append({"n": L["n"], "nd": L["title_nd"], "en": L["title_en"], "pages": L["pages"],
                    "check": check.get(L["n"], []), "slides": slides})

out = BOOK / "recording-data.js"
out.write_text(
    "// Made by scripts/make_recording_kit.py from lessons.py and build.py. Don't edit by hand.\n"
    "var RECORDING = [\n" + ",\n".join(json.dumps(l, ensure_ascii=False) for l in lessons) + "\n];\n",
    encoding="utf-8",
)
print("Wrote %s: %d lessons, %d slides" % (out.relative_to(ROOT), len(lessons), sum(len(l["slides"]) for l in lessons)))
